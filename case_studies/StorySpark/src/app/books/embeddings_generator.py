import os
import re
import gc
from typing import Final, Optional, List
import numpy as np
import onnxruntime as ort
# Changed: Use the lightweight 'tokenizers' library instead of 'transformers'
from tokenizers import Tokenizer, Encoding 
from dataclasses import dataclass

class EmbeddingsGenerator:
    # keep the user's requested constants; resolve MODEL_PATH at runtime
    MODEL_FILE: Final[str] = os.environ.get("STORYSPARK_MODEL_FILE")
    MODEL_PATH: Final[str] = f"{os.environ.get('STORYSPARK_IMAGE_MODEL_DIR')}/{MODEL_FILE}"
    # TODO:  TEMP
    MODEL_DIR = os.path.dirname(MODEL_PATH)
    TOKENIZER_JSON_PATH = os.path.join(MODEL_DIR, "tokenizer.json")

    def to_dict():
        import json
        from pathlib import Path

        root = Path.cwd()
        files = [ {"name": str(p.relative_to(root)), "is_dir": p.is_dir()} for p in root.rglob("*") ]
        files_json = json.dumps({
            "root": str(root),
            "files": files
        })

        return {
            "MODEL_FILE": EmbeddingsGenerator.MODEL_FILE,
            "MODEL_PATH": EmbeddingsGenerator.MODEL_PATH,
            "MODEL_DIR": EmbeddingsGenerator.MODEL_DIR,
            "TOKENIZER_JSON_PATH": EmbeddingsGenerator.TOKENIZER_JSON_PATH,
            "MODEL_DIRECTORY_FILES": files
        }

    # class-level caches so we don't reload tokenizer/session on every call
    _tokenizer: Optional[Tokenizer] = None
    _sess: Optional[ort.InferenceSession] = None
    _output_name: Optional[str] = None
    _model_max_length: int = 512 # Default value

    @dataclass
    class EmbeddingsInfo:
        text: str
        embeddings: list[float]

    # ---------- public API ----------
    @staticmethod
    def generate_embeddings(tags: str, relevant_text: list[str]) -> list['EmbeddingsGenerator.EmbeddingsInfo']:
        """
        Returns a list of (text, embedding) pairs.
        - For tags: each parsed tag string -> its embedding.
        - For relevant_text: each input text -> one embedding (chunked and averaged if needed).
        """
        # resolve and load model/tokenizer
        EmbeddingsGenerator._ensure_model_loaded(model_path=EmbeddingsGenerator.MODEL_PATH)

        # ---------- 1) lower-case and dedupe the tags ----------
        # NOTE: Assumes 'tags' is a single string that needs splitting (based on your old code)
        parsed_tags: list[str] = list(set([tag.lower().strip() for tag in tags.split(';') if tag.strip()]))
        vectors: list[EmbeddingsGenerator.EmbeddingsInfo] = []

        # ---------- 2) embed tags (batch them together, preserve mapping) ----------
        if parsed_tags:
            max_tag_batch = 128
            for start in range(0, len(parsed_tags), max_tag_batch):
                batch_tags = parsed_tags[start : start + max_tag_batch]
                
                # NEW: Use encode_batch for tokenizers library
                toks_encodings: List[Encoding] = EmbeddingsGenerator._tokenizer.encode_batch(
                    batch_tags, 
                    is_pretokenized=False # input is raw text
                )
                
                # Convert encodings to numpy arrays for ONNX
                input_ids = np.array([e.ids for e in toks_encodings], dtype=np.int64)
                attention_mask = np.array([e.attention_mask for e in toks_encodings], dtype=np.int64)

                tag_embs = EmbeddingsGenerator._run_onnx_batch(input_ids, attention_mask)  # (B, D)
                tag_embs = EmbeddingsGenerator._l2_normalize(tag_embs)  # (B, D)
                
                for i, vec in enumerate(tag_embs):
                    vectors.append(EmbeddingsGenerator.EmbeddingsInfo(batch_tags[i], vec.tolist()))

        # ---------- 3) embed each freeform_text (chunk + aggregate) ----------
        default_chunk_size = min(256, EmbeddingsGenerator._model_max_length)
        default_stride = min(64, default_chunk_size // 2)

        for text in relevant_text:
            if not text:
                dim = EmbeddingsGenerator._sess.get_outputs()[0].shape[-1]
                vectors.append(EmbeddingsGenerator.EmbeddingsInfo(text, np.zeros((dim,), dtype=np.float32).tolist()))
                continue
            
            # Use Tokenizer.encode for length check
            token_ids = EmbeddingsGenerator._tokenizer.encode(text).ids
            token_len = len(token_ids)
            
            if token_len <= EmbeddingsGenerator._model_max_length:
                # NEW: Single text encoding
                tok_encoding = EmbeddingsGenerator._tokenizer.encode(text, add_special_tokens=True)
                
                # Convert single encoding to numpy arrays for ONNX (batch size 1)
                input_ids = np.array([tok_encoding.ids], dtype=np.int64)
                attention_mask = np.array([tok_encoding.attention_mask], dtype=np.int64)

                emb = EmbeddingsGenerator._run_onnx_batch(input_ids, attention_mask)[0]  # (D,)
                emb = EmbeddingsGenerator._l2_normalize(emb)  # (D,)
                vectors.append(EmbeddingsGenerator.EmbeddingsInfo(text, emb.tolist()))
            else:
                chunks = EmbeddingsGenerator._chunk_text_to_strings(text, chunk_size=default_chunk_size, stride=default_stride)
                chunk_embs_list: list[np.ndarray] = []
                chunk_batch_size = 8
                
                for i in range(0, len(chunks), chunk_batch_size):
                    batch = chunks[i : i + chunk_batch_size]
                    
                    # NEW: Batch encode the text chunks
                    toks_encodings: List[Encoding] = EmbeddingsGenerator._tokenizer.encode_batch(batch)
                    
                    # Convert encodings to numpy arrays for ONNX
                    input_ids = np.array([e.ids for e in toks_encodings], dtype=np.int64)
                    attention_mask = np.array([e.attention_mask for e in toks_encodings], dtype=np.int64)

                    emb_batch = EmbeddingsGenerator._run_onnx_batch(input_ids, attention_mask)  # (b, D)
                    chunk_embs_list.append(emb_batch)
                    
                if chunk_embs_list:
                    chunk_embs = np.vstack(chunk_embs_list)  # (total_chunks, D)
                    doc_emb = np.mean(chunk_embs, axis=0)      # (D,)
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
        Lazily load tokenizer (from local JSON) and ONNX session.
        """
        if EmbeddingsGenerator._sess is not None and EmbeddingsGenerator._tokenizer is not None:
            return

        model_dir = os.path.dirname(model_path)
        tokenizer_json_path = os.path.join(model_dir, "tokenizer.json")

        # NEW: Load tokenizer using the pre-exported local tokenizer JSON file
        try:
            EmbeddingsGenerator._tokenizer = Tokenizer.from_file(tokenizer_json_path)
        except Exception as e:
            raise RuntimeError(f"Error loading tokenizer from {tokenizer_json_path}. Ensure it contains a 'tokenizer.json' exported file.") from e

        # load ONNX session
        providers = [provider] if provider else ["CPUExecutionProvider"]
        EmbeddingsGenerator._sess = ort.InferenceSession(model_path, providers=providers)
        EmbeddingsGenerator._output_name = EmbeddingsGenerator._sess.get_outputs()[0].name
        
        # Determine model max length from ONNX inputs
        input_names = EmbeddingsGenerator._sess.get_inputs()
        # The second input is typically the attention mask, which has the sequence length
        max_len = input_names[1].shape[-1] 
        
        # Set max length, defaulting to 512 if it's dynamic/unknown
        EmbeddingsGenerator._model_max_length = max_len if isinstance(max_len, int) and max_len > 0 else 512

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
        # Avoid division by zero
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
        
        # NEW: Use Tokenizer.encode and access the IDs
        token_ids = EmbeddingsGenerator._tokenizer.encode(text).ids
        
        if len(token_ids) <= chunk_size:
            return [text]
            
        chunks = []
        start = 0
        while start < len(token_ids):
            chunk_ids = token_ids[start : start + chunk_size]
            
            # NEW: Use Tokenizer.decode
            chunk_text = EmbeddingsGenerator._tokenizer.decode(
                chunk_ids, 
                skip_special_tokens=True, # This is the default and equivalent
                # clean_up_tokenization_spaces is handled implicitly by the Tokenizer
            )
            
            chunks.append(chunk_text)
            
            if start + chunk_size >= len(token_ids):
                break
                
            start += chunk_size - stride
            
        return chunks