"""Optional FAISS index wrapper. Falls back if FAISS not installed."""
from typing import Optional
import numpy as np

try:
    import faiss
    FAISS_AVAILABLE = True
except Exception:
    faiss = None
    FAISS_AVAILABLE = False


class FaissIndex:
    def __init__(self, dim: int, use_gpu: bool = False):
        if not FAISS_AVAILABLE:
            raise RuntimeError("faiss is not available. Install faiss-cpu or faiss-gpu to use this class")
        self.dim = dim
        self.index = faiss.IndexFlatIP(dim)  # inner product for cosine if vectors normalized

    def add(self, vectors: np.ndarray):
        if vectors.dtype != np.float32:
            vectors = vectors.astype('float32')
        self.index.add(vectors)

    def search(self, queries: np.ndarray, k: int = 5):
        if queries.dtype != np.float32:
            queries = queries.astype('float32')
        distances, indices = self.index.search(queries, k)
        return indices, distances
