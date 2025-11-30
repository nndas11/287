import os
import pytest

from scripts.offline_scoring import compute_and_write_score


ART_DIR = os.environ.get("NOTEBOOKLM_ARTIFACTS", "./artifacts")
THRESHOLD = float(os.environ.get("SEMANTIC_SIM_THRESHOLD", "0.65"))


def test_offline_scoring():
    """Compute semantic similarity between two artifact files using the helper.

    The test expects two files in `NOTEBOOKLM_ARTIFACTS` (default `./artifacts`):
    - `expected.txt` : the expected/source passage
    - `actual.txt`   : the actual/answer snippet

    If files are not present the test will be skipped so this can run in CI
    without the browser-dependent artifacts.
    """
    expected_path = os.path.join(ART_DIR, "expected.txt")
    actual_path = os.path.join(ART_DIR, "actual.txt")

    if not os.path.exists(expected_path) or not os.path.exists(actual_path):
        pytest.skip("Offline artifact files not present: expected.txt / actual.txt")

    sim = compute_and_write_score(ART_DIR, threshold=THRESHOLD, test_name="support.test_offline_scoring")
    assert sim >= THRESHOLD, f"Semantic similarity {sim:.4f} is below threshold {THRESHOLD}"
