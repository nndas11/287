from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Any, Optional
from semantic import EmbeddingModel, top_k_cosine
import numpy as np


app = FastAPI(title="Semantic Similarity API")

# Enable CORS for the web UI
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the web UI from / (mounts `web/` directory)
app.mount("/static", StaticFiles(directory="web"), name="static")

model = EmbeddingModel()


class EmbedRequest(BaseModel):
    texts: List[str]


class SimilarityRequest(BaseModel):
    query: str
    corpus: List[str]
    top_k: int = 5


class SearchRequest(BaseModel):
    query: str
    corpus: Optional[List[str]] = None
    page: int = 1
    page_size: int = 10


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/embed")
def embed(req: EmbedRequest):
    emb = model.embed(req.texts)
    return {"embeddings": emb.tolist()}


@app.post("/similarity")
def similarity(req: SimilarityRequest):
    corpus_emb = model.embed(req.corpus)
    query_emb = model.embed(req.query)[0]
    idxs, scores = top_k_cosine(query_emb, corpus_emb, k=req.top_k)
    results = []
    for i, s in zip(idxs, scores):
        results.append({"index": int(i), "score": float(s), "text": req.corpus[i]})
    return {"results": results}


@app.post("/similarity/search")
def similarity_search(req: SearchRequest):
    """Search corpus for query and return paginated results sorted by score.

    If `corpus` is omitted, the endpoint will use the sample data file from `examples/data/sample_sentences.csv`.
    """
    if req.corpus is None:
        # lazy load sample corpus
        try:
            with open("examples/data/sample_sentences.csv", newline='') as f:
                corpus = [line.strip() for line in f if line.strip()]
        except Exception:
            return {"results": [], "total": 0}
    else:
        corpus = req.corpus

    corpus_emb = model.embed(corpus)
    query_emb = model.embed(req.query)[0]
    sims = np.asarray(np.dot(corpus_emb, query_emb) / (np.linalg.norm(corpus_emb, axis=1) * np.linalg.norm(query_emb) + 1e-12))
    order = np.argsort(-sims)
    total = len(corpus)
    # pagination
    page = max(1, req.page)
    page_size = max(1, req.page_size)
    start = (page - 1) * page_size
    end = start + page_size
    selected = order[start:end]
    results = []
    for i in selected:
        results.append({"index": int(i), "score": float(sims[i]), "text": corpus[i]})
    return {"results": results, "total": total, "page": page, "page_size": page_size}
