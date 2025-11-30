import sys
import types
import numpy as np
from fastapi.testclient import TestClient


class DummySentenceTransformer:
    def __init__(self, model_name=None):
        self.model_name = model_name

    def encode(self, texts, convert_to_numpy=True, show_progress_bar=False):
        # deterministic, lightweight embedding: [length, vowel_count]
        if isinstance(texts, str):
            texts = [texts]
        arr = []
        for t in texts:
            vowels = sum(ch in 'aeiouAEIOU' for ch in t)
            arr.append([len(t), vowels])
        return np.array(arr, dtype=float)


def setup_dummy_sentence_transformers():
    # insert a fake sentence_transformers module before importing app to avoid heavy downloads
    mod = types.ModuleType("sentence_transformers")
    mod.SentenceTransformer = DummySentenceTransformer
    sys.modules["sentence_transformers"] = mod


def test_health_endpoint():
    setup_dummy_sentence_transformers()
    # import app after installing dummy to avoid model download
    from api.main import app
    client = TestClient(app)
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "ok"}


def test_similarity_search_pagination():
    setup_dummy_sentence_transformers()
    from api import main
    client = TestClient(main.app)

    # override model with deterministic fake (already used via dummy), but ensure attribute exists
    # corpus with 3 items
    corpus = ["apple", "banana", "applesauce"]
    # page 1, size 2
    body = {"query": "apple", "corpus": corpus, "page": 1, "page_size": 2}
    r = client.post("/similarity/search", json=body)
    assert r.status_code == 200
    data = r.json()
    assert data["total"] == 3
    assert data["page"] == 1
    assert data["page_size"] == 2
    assert len(data["results"]) == 2
    # page 2 should return the remaining item
    body["page"] = 2
    r2 = client.post("/similarity/search", json=body)
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["page"] == 2
    assert len(d2["results"]) == 1
    # each result should contain index, score, text
    for item in d2["results"]:
        assert set(item.keys()) >= {"index", "score", "text"}
