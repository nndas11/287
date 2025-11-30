import numpy as np
from semantic import EmbeddingModel


def test_embeddings_shape():
    model = EmbeddingModel()
    texts = ["hello world", "another sentence"]
    emb = model.embed(texts)
    assert isinstance(emb, np.ndarray)
    assert emb.shape[0] == 2
