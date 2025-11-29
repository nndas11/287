"""Similarity utilities."""
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from typing import Tuple


def cosine_similarity_matrix(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    """Compute cosine similarity between two matrices a and b.

    a: (n_samples_a, dim)
    b: (n_samples_b, dim)
    returns: (n_samples_a, n_samples_b)
    """
    return cosine_similarity(a, b)


def top_k_cosine(query_vec: np.ndarray, corpus_vecs: np.ndarray, k: int = 5) -> Tuple[np.ndarray, np.ndarray]:
    """Return top-k indices and scores for a single query vector.

    query_vec: (dim,) or (1, dim)
    corpus_vecs: (n, dim)
    returns: (indices, scores)
    """
    if query_vec.ndim == 1:
        q = query_vec.reshape(1, -1)
    else:
        q = query_vec
    sims = cosine_similarity(q, corpus_vecs)[0]
    idx = np.argsort(-sims)[:k]
    return idx, sims[idx]
