import os
from sentence_transformers import SentenceTransformer
from typing import Final

class EmbeddingsGenerator:
    # TODO: Fetch this from Environment Variables (STORYSPARK_HUGGINGFACE_EMBEDDINGS_MODEL) and enforce some type of check for the same number of dimensions
    MODEL_NAME: Final[str] = "all-MiniLM-L6-v2"
    MODEL_PATH: Final[str] = os.environ.get("EMBEDDINGS_MODEL_PATH")

    @staticmethod
    def generate_embeddings(texts: list[str]) -> list[float]:
        # This should already be cached into the docker image and not have to downloaded each time this is called
        model = SentenceTransformer(EmbeddingsGenerator.MODEL_PATH)

        # TODO:  For now, to get things working, just concatenate all the sources into one big string and get embeddings for that.
        # For better accuracy, we probably want to have multiple rows for each book with each row based on either one specific tag
        # or one block of summary text
        
        # Normally I would use "\n\n" as separator but GPT is suggesting to use this since it is more clear for later splitting/debugging and won't get picked up by tokenization.
        # "\n\n" may get treated as ordinary whitespace by some/many embedding models and may get confused if there are other chunks of text that legitimately has "\n\n" in them.
        final_text = "<|sep|>".join(texts)

        return model.encode(final_text).tolist()