"""Simple CLI to compute similarity between sentences.

This CLI expects a corpus file (one sentence per line). The project used to
include a sample file at `examples/data/sample_sentences.csv`, but that file
was removed during cleanup. Please pass `--corpus /path/to/corpus.txt` or
recreate the sample data if you want a default demo.
"""
import argparse
import csv
import os
from .embeddings import EmbeddingModel
from .similarity import top_k_cosine


def main():
    parser = argparse.ArgumentParser(description="Compute semantic similarity between sentences")
    parser.add_argument("--corpus", type=str, default=None, help="Path to a corpus file (one sentence per line)")
    parser.add_argument("--topk", type=int, default=3)
    args = parser.parse_args()

    if not args.corpus:
        print("No --corpus provided. Provide a path to a corpus file (one sentence per line).")
        return

    if not os.path.exists(args.corpus):
        print(f"Corpus file not found: {args.corpus}")
        return

    corpus = []
    with open(args.corpus, newline='') as f:
        reader = csv.reader(f)
        for row in reader:
            if row:
                corpus.append(row[0])

    if not corpus:
        print("Corpus is empty. Provide a file with one sentence per line.")
        return

    model = EmbeddingModel()
    emb = model.embed(corpus)

    # demo: compare first sentence to rest
    idxs, scores = top_k_cosine(emb[0], emb, k=args.topk)
    print("Query:", corpus[0])
    for i, s in zip(idxs, scores):
        print(f"- ({s:.4f}) {corpus[i]}")


if __name__ == '__main__':
    main()
