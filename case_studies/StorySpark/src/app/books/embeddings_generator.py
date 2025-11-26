import os
import re
import gc
from typing import Final, Optional
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer
from dataclasses import dataclass

class EmbeddingsGenerator:
    # keep the user's requested constants; resolve MODEL_PATH at runtime
    MODEL_FILE: Final[str] = os.environ.get("STORYSPARK_MODEL_FILE")
    MODEL_PATH: Final[str] = f"{os.environ.get('STORYSPARK_IMAGE_MODEL_DIR')}/{MODEL_FILE}"

    # class-level caches so we don't reload tokenizer/session on every call
    _tokenizer = None
    _sess = None
    _output_name = None
    _model_max_length = None

    @dataclass
    class EmbeddingsInfo:
        text: str
        embeddings: list[float]

    # ---------- public API ----------
    @staticmethod
    def generate_embeddings(tags: list[str], relevant_text: list[str]) -> list[EmbeddingsInfo]:
        """
        Returns a list of (text, embedding) pairs.
        - For tags: each parsed tag string -> its embedding.
        - For relevant_text: each input text -> one embedding (chunked and averaged if needed).
        """
        # resolve and load model/tokenizer
        EmbeddingsGenerator._ensure_model_loaded(model_path=EmbeddingsGenerator.MODEL_PATH)

        # ---------- 1) lower-case and dedupe the tags ----------
        parsed_tags: list[str] = list(set([tag.lower().strip() for tag in tags.split(';')]))
        vectors: list[EmbeddingsGenerator.EmbeddingsInfo] = []

        # ---------- 2) embed tags (batch them together, preserve mapping) ----------
        if parsed_tags:
            max_tag_batch = 128
            for start in range(0, len(parsed_tags), max_tag_batch):
                batch_tags = parsed_tags[start : start + max_tag_batch]
                toks = EmbeddingsGenerator._tokenizer(batch_tags, padding="longest", truncation=True, max_length=64, return_tensors="np")
                tag_embs = EmbeddingsGenerator._run_onnx_batch(toks["input_ids"], toks["attention_mask"])  # (B, D)
                tag_embs = EmbeddingsGenerator._l2_normalize(tag_embs)  # (B, D)
                for i, vec in enumerate(tag_embs):
                    vectors.append(EmbeddingsGenerator.EmbeddingsInfo(batch_tags[i], vec.tolist()))

        # ---------- 3) embed each freeform_text (chunk + aggregate) ----------
        default_chunk_size = min(256, EmbeddingsGenerator._model_max_length)
        default_stride = min(64, default_chunk_size // 2)

        for text in relevant_text:
            if not text:
                # keep mapping for empty text
                dim = EmbeddingsGenerator._sess.get_outputs()[0].shape[-1]
                vectors.append(EmbeddingsGenerator.EmbeddingsInfo(text, np.zeros((dim,), dtype=np.float32).tolist()))
                continue

            token_len = len(EmbeddingsGenerator._tokenizer.encode(text, add_special_tokens=True))
            if token_len <= EmbeddingsGenerator._model_max_length:
                toks = EmbeddingsGenerator._tokenizer([text], padding="longest", truncation=True, max_length=token_len, return_tensors="np")
                emb = EmbeddingsGenerator._run_onnx_batch(toks["input_ids"], toks["attention_mask"])[0]  # (D,)
                emb = EmbeddingsGenerator._l2_normalize(emb)  # (D,)
                vectors.append(EmbeddingsGenerator.EmbeddingsInfo(text, emb.tolist()))
            else:
                chunks = EmbeddingsGenerator._chunk_text_to_strings(text, chunk_size=default_chunk_size, stride=default_stride)
                chunk_embs_list: list[np.ndarray] = []
                chunk_batch_size = 8
                for i in range(0, len(chunks), chunk_batch_size):
                    batch = chunks[i : i + chunk_batch_size]
                    lens = [len(EmbeddingsGenerator._tokenizer.encode(c, add_special_tokens=True)) for c in batch]
                    batch_max_len = min(max(lens), EmbeddingsGenerator._model_max_length)
                    toks = EmbeddingsGenerator._tokenizer(batch, padding="max_length", truncation=True, max_length=batch_max_len, return_tensors="np")
                    emb_batch = EmbeddingsGenerator._run_onnx_batch(toks["input_ids"], toks["attention_mask"])  # (b, D)
                    chunk_embs_list.append(emb_batch)
                if chunk_embs_list:
                    chunk_embs = np.vstack(chunk_embs_list)  # (total_chunks, D)
                    doc_emb = np.mean(chunk_embs, axis=0)     # (D,)
                    doc_emb = EmbeddingsGenerator._l2_normalize(doc_emb)
                    vectors.append(EmbeddingsGenerator.EmbeddingsInfo(text, doc_emb.tolist()))
                else:
                    dim = EmbeddingsGenerator._sess.get_outputs()[0].shape[-1]
                    vectors.append(EmbeddingsGenerator.EmbeddingsInfo(text, np.zeros((dim,), dtype=np.float32).tolist()))

        # free memory if needed
        gc.collect()
        return vectors

    # ---------- helpers ----------
    @staticmethod
    def _ensure_model_loaded(model_path: str, tokenizer_name: Optional[str] = None, provider: Optional[str] = None):
        """
        Lazily load tokenizer and ONNX session. If tokenizer files are colocated
        with the model (same directory), prefer the local tokenizer; otherwise
        fall back to the HF model id passed in tokenizer_name.
        """
        if EmbeddingsGenerator._sess is not None and EmbeddingsGenerator._tokenizer is not None:
            return

        # Find a local tokenizer dir next to the model file
        model_dir = os.path.dirname(model_path)

        # load tokenizer using the pre-exported local tokenizer files
        EmbeddingsGenerator._tokenizer = AutoTokenizer.from_pretrained(model_dir, use_fast=True)

        # load ONNX session
        providers = [provider] if provider else ["CPUExecutionProvider"]
        EmbeddingsGenerator._sess = ort.InferenceSession(model_path, providers=providers)
        EmbeddingsGenerator._output_name = EmbeddingsGenerator._sess.get_outputs()[0].name
        EmbeddingsGenerator._model_max_length = getattr(EmbeddingsGenerator._tokenizer, "model_max_length", 512)

    @staticmethod
    def _run_onnx_batch(input_ids: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
        ort_inputs = {
            "input_ids": input_ids.astype(np.int64),
            "attention_mask": attention_mask.astype(np.int64),
        }
        outputs = EmbeddingsGenerator._sess.run([EmbeddingsGenerator._output_name], ort_inputs)
        emb = outputs[0]
        # ensure float32 numpy array
        return np.asarray(emb, dtype=np.float32)

    @staticmethod
    def _l2_normalize(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
        norm = np.linalg.norm(v, axis=-1, keepdims=True)
        return v / (norm + eps)

    @staticmethod
    def _chunk_text_to_strings(text: str, chunk_size: int, stride: int) -> list[str]:
        """
        Chunk a single text into token-level chunks (decoded back to text).
        Returns list of chunk strings.
        """
        if not text:
            return [""]
        token_ids = EmbeddingsGenerator._tokenizer.encode(text, add_special_tokens=False)
        if len(token_ids) <= chunk_size:
            return [text]
        chunks = []
        start = 0
        while start < len(token_ids):
            chunk_ids = token_ids[start : start + chunk_size]
            chunk_text = EmbeddingsGenerator._tokenizer.decode(
                chunk_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True
            )
            chunks.append(chunk_text)
            if start + chunk_size >= len(token_ids):
                break
            start += chunk_size - stride
        return chunks
