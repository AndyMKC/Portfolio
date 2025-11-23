from sentence_transformers import SentenceTransformer
from typing import Final

class EmbeddingsGenerator:
    # TODO: Fetch this from Environment Variables (STORYSPARK_HUGGINGFACE_EMBEDDINGS_MODEL) and enforce some type of check for the same number of dimensions
    MODEL_NAME: Final[str] = "all-MiniLM-L6-v2"

    @staticmethod
    def generate_embeddings(texts: list[str]) -> list[float]:
        # This should already be cached into the docker image and not have to downloaded each time this is called
        model = SentenceTransformer(EmbeddingsGenerator.MODEL_NAME)
        return model.encode(texts).tolist()