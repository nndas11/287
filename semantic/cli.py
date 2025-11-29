"""Simple CLI to compute similarity between sentences."""
import argparse
import csv
from .embeddings import EmbeddingModel
from .similarity import top_k_cosine


def main():
    parser = argparse.ArgumentParser(description="Compute semantic similarity between sentences")
    parser.add_argument("--corpus", type=str, default="examples/data/sample_sentences.csv")
    parser.add_argument("--topk", type=int, default=3)
    args = parser.parse_args()

    corpus = []
    with open(args.corpus, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                corpus.append(row[0])

    model = EmbeddingModel()
    emb = model.embed(corpus)

    # demo: compare first sentence to rest
    idxs, scores = top_k_cosine(emb[0], emb, k=args.topk)
    print("Query:", corpus[0])
    for i, s in zip(idxs, scores):
        print(f"- ({s:.4f}) {corpus[i]}")


if __name__ == '__main__':
    main()
