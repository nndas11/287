"""Embedding wrapper using sentence-transformers."""
from sentence_transformers import SentenceTransformer
import numpy as np
from typing import List, Union


class EmbeddingModel:
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    def embed(self, texts: Union[str, List[str]]) -> np.ndarray:
        """Return embeddings for a single string or list of strings as a numpy array."""
        if isinstance(texts, str):
            texts = [texts]
        emb = self.model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
        return np.array(emb)
