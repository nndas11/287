#!/usr/bin/env python3
"""Produce aggregated metrics from `semantic_results.csv`.

Usage:
  NOTEBOOKLM_ARTIFACTS=./artifacts python scripts/summary_report.py

Options:
  --results PATH   Path to the results CSV (default: $NOTEBOOKLM_ARTIFACTS/semantic_results.csv)
  --out-dir PATH   Directory to write summary files (default: same folder as results)
  --bins N         Number of histogram bins (default: 10)
  --save-plot      Save histogram PNG if matplotlib is installed

The script prints a summary (count, mean, median, std, min, max), prints
per-test averages, and writes `semantic_summary.json` and `semantic_summary.csv`
into the artifacts folder. If matplotlib is available and `--save-plot` is set,
it will save a histogram PNG as `semantic_hist.png`.
"""
from __future__ import annotations
import argparse
import csv
import json
import os
from pathlib import Path
import sys
from statistics import mean, median, pstdev
import numpy as np


def read_scores(results_path: Path):
    if not results_path.exists():
        raise FileNotFoundError(f"Results CSV not found: {results_path}")
    scores = []
    rows = []

    # First try to read a CSV with headers (semantic_score or score)
    with results_path.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames or []
        has_score_header = any(fn and fn.strip().lower() in ("semantic_score", "score") for fn in fieldnames)
        if has_score_header:
            for r in reader:
                val = r.get("semantic_score") or r.get("score")
                if val is None:
                    continue
                try:
                    s = float(val)
                except Exception:
                    try:
                        s = float(val.strip())
                    except Exception:
                        continue
                scores.append(s)
                rows.append({
                    "test_name": r.get("test_name", ""),
                    "score": s,
                    "expected": r.get("expected", ""),
                    "actual": r.get("actual", ""),
                })
            return scores, rows

    # Fallback: some older or manually appended CSVs may not include a header row.
    # Assume the column ordering: timestamp, test_name, expected, actual, score
    with results_path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        for r in reader:
            if not r:
                continue
            # If the last column is numeric, treat it as score; otherwise skip
            last = r[-1].strip() if r[-1] else ""
            try:
                s = float(last)
            except Exception:
                # skip header-like or malformed rows
                continue

            # Map columns defensively
            test_name = r[1] if len(r) > 1 else ""
            expected = r[2] if len(r) > 2 else ""
            actual = r[3] if len(r) > 3 else ""

            scores.append(s)
            rows.append({"test_name": test_name, "score": s, "expected": expected, "actual": actual})

    return scores, rows


def summarize(scores: list[float]):
    if not scores:
        return {}
    arr = np.asarray(scores, dtype=float)
    return {
        "count": int(arr.size),
        "mean": float(arr.mean()),
        "median": float(np.median(arr)),
        "std": float(arr.std(ddof=0)),
        "min": float(arr.min()),
        "max": float(arr.max()),
    }


def per_test_summary(rows: list[dict]):
    groups = {}
    for r in rows:
        name = r.get("test_name") or ""
        groups.setdefault(name, []).append(r["score"])
    out = {}
    for name, vals in groups.items():
        arr = np.asarray(vals, dtype=float)
        out[name] = {
            "count": int(arr.size),
            "mean": float(arr.mean()),
            "median": float(np.median(arr)),
        }
    return out


def print_ascii_hist(counts, bin_edges, width=50):
    maxc = max(counts) if counts else 0
    for i, c in enumerate(counts):
        left = bin_edges[i]
        right = bin_edges[i + 1]
        bar = "#" * int((c / maxc) * width) if maxc > 0 else ""
        print(f"{left:0.3f} - {right:0.3f} | {c:5d} | {bar}")


def main():
    p = argparse.ArgumentParser()
    default_art = os.environ.get("NOTEBOOKLM_ARTIFACTS", "./artifacts")
    p.add_argument("--results", default=str(Path(default_art) / "semantic_results.csv"))
    p.add_argument("--out-dir", default=None)
    p.add_argument("--bins", type=int, default=10)
    p.add_argument("--save-plot", action="store_true")
    args = p.parse_args()

    results_path = Path(args.results)
    out_dir = Path(args.out_dir) if args.out_dir else results_path.parent
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        scores, rows = read_scores(results_path)
    except FileNotFoundError as e:
        print(e)
        sys.exit(2)

    summary = summarize(scores)
    per_test = per_test_summary(rows)

    print("Summary metrics:")
    if summary:
        print(json.dumps(summary, indent=2))
    else:
        print("No scores found in results CSV.")

    print("\nPer-test summary (top 20):")
    for k, v in list(per_test.items())[:20]:
        print(f"- {k}: count={v['count']}, mean={v['mean']:.4f}, median={v['median']:.4f}")

    # histogram
    if scores:
        counts, bin_edges = np.histogram(np.asarray(scores), bins=args.bins)
        print("\nHistogram:")
        try:
            # try to save plot if requested
            if args.save_plot:
                import matplotlib.pyplot as plt

                plt.figure(figsize=(6, 4))
                plt.hist(scores, bins=args.bins, color="C0", edgecolor="black")
                plt.xlabel("Semantic score")
                plt.ylabel("Count")
                plt.title("Semantic score distribution")
                png_path = out_dir / "semantic_hist.png"
                plt.tight_layout()
                plt.savefig(png_path)
                print(f"Saved histogram to {png_path}")
            else:
                raise ImportError
        except Exception:
            # fallback to ASCII histogram
            print_ascii_hist(counts, bin_edges)

    # Write summary files
    json_path = out_dir / "semantic_summary.json"
    csv_path = out_dir / "semantic_summary.csv"
    with json_path.open("w", encoding="utf-8") as jf:
        json.dump({"summary": summary, "per_test": per_test}, jf, indent=2)
    # write a small CSV per-test
    with csv_path.open("w", encoding="utf-8", newline="") as cf:
        writer = csv.writer(cf)
        writer.writerow(["test_name", "count", "mean", "median"])
        for name, v in per_test.items():
            writer.writerow([name, v["count"], f"{v['mean']:.6f}", f"{v['median']:.6f}"])

    print(f"\nWrote {json_path} and {csv_path}")


if __name__ == "__main__":
    main()
