from sentence_transformers import SentenceTransformer
from typing import Final

class EmbeddingsGenerator:
    MODEL_NAME: Final[str] = "all-MiniLM-L6-v2"

    @staticmethod
    def generate_embeddings(texts: list[str]) -> list[float]:
        # This should already be cached into the docker image and not have to downloaded each time this is called
        model = SentenceTransformer(EmbeddingsGenerator.MODEL_NAME)
        return model.encode(texts).tolist()