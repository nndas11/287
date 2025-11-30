"""Demo script showing embeddings and top-k similarity."""
from semantic import EmbeddingModel, top_k_cosine
"""Demo script showing embeddings and top-k similarity."""
from semantic import EmbeddingModel, top_k_cosine
import csv


def load_corpus(path="examples/data/sample_sentences.csv"):
    with open(path, newline='') as f:
        return [line.strip() for line in f if line.strip()]


def main():
    corpus = load_corpus()
    model = EmbeddingModel()
    emb = model.embed(corpus)

    print(f"Loaded {len(corpus)} sentences")
    # show top-3 for sentence 0
    idxs, scores = top_k_cosine(emb[0], emb, k=3)
    print("Query:", corpus[0])
    for i, s in zip(idxs, scores):
        print(f"- ({s:.4f}) {corpus[i]}")


if __name__ == '__main__':
    main()
