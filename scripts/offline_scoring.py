"""Reusable offline scoring helper.

Contains a single helper function `compute_and_write_score` that reads two text
files (expected, actual) from an artifacts directory, computes embeddings via
the `semantic` package, writes `semantic_score.txt` and returns the similarity
score. If a threshold is provided and the score is below it, an
`AssertionError` is raised.
"""
from pathlib import Path
import os
import numpy as np

from semantic import EmbeddingModel


def compute_and_write_score(artifacts_dir: str | Path = "./artifacts",
                            expected_fname: str = "expected.txt",
                            actual_fname: str = "actual.txt",
                            score_fname: str = "semantic_score.txt",
                            threshold: float | None = None,
                            test_name: str | None = None,
                            results_fname: str = "semantic_results.csv") -> float:
    artifacts_dir = Path(artifacts_dir)
    expected_path = artifacts_dir / expected_fname
    actual_path = artifacts_dir / actual_fname

    if not expected_path.exists():
        raise FileNotFoundError(f"Expected file not found: {expected_path}")
    if not actual_path.exists():
        raise FileNotFoundError(f"Actual file not found: {actual_path}")

    expected = expected_path.read_text(encoding="utf-8").strip()
    actual = actual_path.read_text(encoding="utf-8").strip()

    model = EmbeddingModel()
    emb = model.embed([expected, actual])
    a, b = emb[0], emb[1]
    sim = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b) + 1e-12))

    artifacts_dir.mkdir(parents=True, exist_ok=True)
    score_path = artifacts_dir / score_fname
    score_path.write_text(f"{sim}\n", encoding="utf-8")

    # Append a summary row to a CSV file for multi-test reporting.
    # Columns: timestamp_iso, test_name, expected, actual, semantic_score
    try:
        import csv
        from datetime import datetime, timezone

        results_path = artifacts_dir / results_fname
        header = ["timestamp", "test_name", "expected", "actual", "semantic_score"]

        # sanitize expected/actual to single-line strings
        exp_single = " ".join(expected.splitlines())
        act_single = " ".join(actual.splitlines())

        write_header = not results_path.exists()
        with results_path.open("a", encoding="utf-8", newline="") as csvf:
            writer = csv.writer(csvf)
            if write_header:
                writer.writerow(header)
            # Use timezone-aware UTC timestamp
            writer.writerow([
                datetime.now(timezone.utc).isoformat(),
                test_name or "",
                exp_single,
                act_single,
                f"{sim:.6f}",
            ])
    except Exception:
        # Do not fail scoring if reporting fails; log to stdout instead
        print("Warning: failed to write results CSV")

    if threshold is not None and sim < float(threshold):
        raise AssertionError(f"Semantic similarity {sim:.6f} is below threshold {threshold}")

    return sim
