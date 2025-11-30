import numpy as np
from semantic import top_k_cosine


def test_top_k_returns_indices_and_scores():
    corpus = np.array([[1.0, 0.0], [0.0, 1.0], [0.7, 0.7]])
    query = np.array([1.0, 0.0])
    idxs, scores = top_k_cosine(query, corpus, k=2)
    assert len(idxs) == 2
    assert len(scores) == 2
