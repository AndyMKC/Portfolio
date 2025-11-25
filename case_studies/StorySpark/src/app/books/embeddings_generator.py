import os
# from sentence_transformers import SentenceTransformer
from typing import Final

class EmbeddingsGenerator:
    # TODO: Fetch this from Environment Variables (STORYSPARK_HUGGINGFACE_EMBEDDINGS_MODEL) and enforce some type of check for the same number of dimensions
    MODEL_FILE: Final[str] = os.environ.get("STORYSPARK_MODEL_FILE")
    MODEL_PATH: Final[str] = f"${os.environ.get("STORYSPARK_IMAGE_MODEL_DIR")}/${MODEL_FILE}"

    @staticmethod
    def generate_embeddings(texts: list[str]) -> list[float]:
        all_embs = []
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            toks = tokenizer(batch,
                            padding=True,
                            truncation=True,
                            max_length=max_length,
                            return_tensors="np")   # returns numpy arrays
            # ONNX Runtime expects int64 for input ids/masks
            ort_inputs = {
                "input_ids": toks["input_ids"].astype(np.int64),
                "attention_mask": toks["attention_mask"].astype(np.int64),
            }
            # run and get the single output (embeddings)
            emb = sess.run([output_name], ort_inputs)[0]   # shape (batch, hidden)
            # your exported wrapper already L2-normalizes; if unsure, normalize here:
            # emb = emb / np.linalg.norm(emb, axis=1, keepdims=True)
            all_embs.append(emb)
        return np.vstack(all_embs)
        # This should already be cached into the docker image and not have to downloaded each time this is called
        # model = SentenceTransformer(EmbeddingsGenerator.MODEL_PATH)

        # # TODO:  For now, to get things working, just concatenate all the sources into one big string and get embeddings for that.
        # # For better accuracy, we probably want to have multiple rows for each book with each row based on either one specific tag
        # # or one block of summary text
        
        # # Normally I would use "\n\n" as separator but GPT is suggesting to use this since it is more clear for later splitting/debugging and won't get picked up by tokenization.
        # # "\n\n" may get treated as ordinary whitespace by some/many embedding models and may get confused if there are other chunks of text that legitimately has "\n\n" in them.
        # final_text = "<|sep|>".join(texts)

        # return model.encode(final_text).tolist()
        return None