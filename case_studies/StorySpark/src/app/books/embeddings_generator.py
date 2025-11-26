# embeddings_generator.py
import os
import csv
import re
import gc
from typing import Final, List, Optional
import numpy as np
import onnxruntime as ort
from transformers import AutoTokenizer

class EmbeddingsGenerator:
    # keep the user's requested constants; resolve MODEL_PATH at runtime
    MODEL_FILE: Final[str] = os.environ.get("STORYSPARK_MODEL_FILE")
    MODEL_PATH: Final[str] = f"{os.environ.get('STORYSPARK_IMAGE_MODEL_DIR')}/{MODEL_FILE}"

    # class-level caches so we don't reload tokenizer/session on every call
    _tokenizer = None
    _sess = None
    _output_name = None
    _model_max_length = None

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
  
        # Use pre-exported local tokenizer files
        tokenizer_source = model_dir

        # load tokenizer
        EmbeddingsGenerator._tokenizer = AutoTokenizer.from_pretrained(tokenizer_source, use_fast=True)

        # load ONNX session
        providers = [provider] if provider else ["CPUExecutionProvider"]
        EmbeddingsGenerator._sess = ort.InferenceSession(model_path, providers=providers)
        EmbeddingsGenerator._output_name = EmbeddingsGenerator._sess.get_outputs()[0].name
        EmbeddingsGenerator._model_max_length = getattr(EmbeddingsGenerator._tokenizer, "model_max_length", 512)

    @staticmethod
    def _token_lengths(texts: List[str]) -> List[int]:
        # fast length estimate using tokenizer.encode without tensors
        tk = EmbeddingsGenerator._tokenizer
        return [len(tk.encode(t, add_special_tokens=True)) for t in texts]

    @staticmethod
    def _run_onnx_batch(input_ids: np.ndarray, attention_mask: np.ndarray) -> np.ndarray:
        sess = EmbeddingsGenerator._sess
        ort_inputs = {
            "input_ids": input_ids.astype(np.int64),
            "attention_mask": attention_mask.astype(np.int64),
        }
        outputs = sess.run([EmbeddingsGenerator._output_name], ort_inputs)
        emb = outputs[0]
        # ensure float32 numpy array
        return np.asarray(emb, dtype=np.float32)

    @staticmethod
    def _l2_normalize(v: np.ndarray, eps: float = 1e-12) -> np.ndarray:
        norm = np.linalg.norm(v, axis=-1, keepdims=True)
        return v / (norm + eps)

    # ---------- public API ----------
    @staticmethod
    def generate_embeddings(tags: List[str], relevant_text: List[str]) -> list[tuple[str, list[float]]]:
        """
        Returns a list of vectors (list of floats).
        Order:
          1) All parsed tag vectors (in the order of tags after parsing and deduping).
          2) One vector per freeform_text (each is chunked if needed, chunk embeddings averaged).
        Notes:
          - Each tag string in `tags` may itself contain multiple tags delimited by ';' or ',' or whitespace.
          - freeform_texts are chunked at token level if they exceed the model's max length.
          - The function loads the ONNX model and tokenizer lazily from environment-configured MODEL_PATH.
        """
        # resolve and load model/tokenizer
        EmbeddingsGenerator._ensure_model_loaded(model_path=EmbeddingsGenerator.MODEL_PATH)

        tokenizer = EmbeddingsGenerator._tokenizer
        sess = EmbeddingsGenerator._sess
        model_max_len = EmbeddingsGenerator._model_max_length

        # ---------- 1) parse tags into a flat list ----------
        parsed_tags: list[str] = list(set(tags.split(';')))

        vectors: list[str, list[float]] = []

        # ---------- 2) embed tags (batch them together) ----------
        if parsed_tags:
            # batch all tags in one call (they are short)
            toks = tokenizer(parsed_tags, padding="longest", truncation=True, max_length=64, return_tensors="np")
            tag_embs = EmbeddingsGenerator._run_onnx_batch(toks["input_ids"], toks["attention_mask"])
            # ensure normalized
            tag_embs = EmbeddingsGenerator._l2_normalize(tag_embs)
            # append each tag vector (as list[float]) preserving order
            for vec in tag_embs:
                vectors.append("qq", vec.tolist())

        # ---------- 3) embed each freeform_text (chunk + aggregate) ----------
        # helper to chunk a single text into token-level chunks (decoded back to text)
        def chunk_text_to_strings(text: str, chunk_size: int, stride: int) -> List[str]:
            if not text:
                return [""]
            token_ids = tokenizer.encode(text, add_special_tokens=False)
            if len(token_ids) <= chunk_size:
                return [text]
            chunks = []
            start = 0
            while start < len(token_ids):
                chunk_ids = token_ids[start : start + chunk_size]
                chunk_text = tokenizer.decode(chunk_ids, skip_special_tokens=True, clean_up_tokenization_spaces=True)
                chunks.append(chunk_text)
                if start + chunk_size >= len(token_ids):
                    break
                start += chunk_size - stride
            return chunks

        # parameters for chunking; chunk_size must be <= model_max_len
        default_chunk_size = min(256, model_max_len)
        default_stride = min(64, default_chunk_size // 2)

        for text in relevant_text:
            # compute token length quickly
            token_len = len(tokenizer.encode(text, add_special_tokens=True))
            if token_len <= model_max_len:
                # short enough: embed directly
                toks = tokenizer([text], padding="longest", truncation=True, max_length=token_len, return_tensors="np")
                emb = EmbeddingsGenerator._run_onnx_batch(toks["input_ids"], toks["attention_mask"])[0]
                emb = EmbeddingsGenerator._l2_normalize(emb)
                vectors.append(text, emb.tolist())
            else:
                # chunk, embed chunks in batches, then average
                chunks = chunk_text_to_strings(text, chunk_size=default_chunk_size, stride=default_stride)
                # embed chunks in small batches to avoid OOM
                chunk_embs_list = []
                chunk_batch_size = 8
                for i in range(0, len(chunks), chunk_batch_size):
                    batch = chunks[i : i + chunk_batch_size]
                    # compute per-batch max token length to reduce padding
                    lens = [len(tokenizer.encode(c, add_special_tokens=True)) for c in batch]
                    batch_max_len = min(max(lens), model_max_len)
                    toks = tokenizer(batch, padding="max_length", truncation=True, max_length=batch_max_len, return_tensors="np")
                    emb_batch = EmbeddingsGenerator._run_onnx_batch(toks["input_ids"], toks["attention_mask"])
                    chunk_embs_list.append(emb_batch)
                if chunk_embs_list:
                    chunk_embs = np.vstack(chunk_embs_list)
                    doc_emb = np.mean(chunk_embs, axis=0)
                    doc_emb = EmbeddingsGenerator._l2_normalize(doc_emb)
                    vectors.append(text, doc_emb.tolist())
                else:
                    # fallback empty vector
                    dim = EmbeddingsGenerator._sess.get_outputs()[0].shape[-1]
                    vectors.append("", np.zeros((dim,), dtype=np.float32).tolist())

        # free memory if needed
        gc.collect()
        return vectors
