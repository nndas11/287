# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Commands

**Run all unit tests (fast, no browser required):**
```bash
.venv/bin/python -m pytest -q
```

**Run a single test file:**
```bash
.venv/bin/python -m pytest tests/support/test_similarity.py -q
```

**Run a single test function:**
```bash
.venv/bin/python -m pytest tests/support/test_similarity.py::test_name -q
```

**Run Selenium tests against NotebookLM (requires Chrome):**
```bash
RUN_SELENIUM=1 USER_DATA_DIR=/path/to/chrome-profile NOTEBOOKLM_ARTIFACTS=./artifacts .venv/bin/python -m pytest -q tests/notebook/
```

**Start the FastAPI server:**
```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

**Generate summary report from results CSV:**
```bash
NOTEBOOKLM_ARTIFACTS=./artifacts python scripts/summary_report.py --save-plot
```

**Augment test queries (uses OpenAI if `OPENAI_API_KEY` is set, otherwise fallback):**
```bash
python scripts/augment_questions.py --source artifacts/semantic_results.csv --out artifacts/augmented_questions.jsonl --n 5
```

## Architecture

The project tests [NotebookLM](https://notebooklm.google.com/) by automating queries via Selenium, capturing AI answers and source citations, then asserting semantic similarity between the cited passage (`expected`) and the AI answer (`actual`).

### Core library: `semantic/`

- `embeddings.py` — `EmbeddingModel` wraps `sentence-transformers` (default model: `all-MiniLM-L6-v2`). This is the single entrypoint for all embedding generation.
- `similarity.py` — `top_k_cosine` and `cosine_similarity_matrix` operate on numpy arrays returned by `EmbeddingModel.embed()`.
- `index.py` — Optional `FaissIndex` wrapper. Gracefully skips if `faiss` is not installed (unavailable on macOS via pip).
- `cli.py` — CLI demo; requires `--corpus <file>` (one sentence per line).

### API: `api/main.py`

FastAPI app with three endpoints (`/embed`, `/similarity`, `/similarity/search`) that all delegate to `EmbeddingModel`. The web UI is served as static files from `web/` at `/static`.

### Test structure: `tests/`

Two categories of tests:

- `tests/support/` — Unit/integration tests for the `semantic` library and scoring helpers. These run without a browser and are always enabled.
- `tests/notebook/` — Selenium tests that drive a real Chrome session against NotebookLM. Each test is gated behind `RUN_SELENIUM=1`. All notebook tests share the `driver` and `wait` session-scoped fixtures defined in `tests/conftest.py`.

Each notebook test follows the same pattern: navigate to a notebook → send a query → click citation 1 → collect highlighted passage text → write `expected.txt` / `actual.txt` → call `scripts/offline_scoring.compute_and_write_score()` → assert score ≥ threshold.

### Scripts: `scripts/`

- `offline_scoring.py` — Importable helper. Reads `expected.txt` / `actual.txt`, computes cosine similarity, writes `semantic_score.txt`, and appends a row to `semantic_results.csv`. Raises `AssertionError` if score is below threshold.
- `summary_report.py` — Aggregates `semantic_results.csv` into summary stats and optionally a histogram PNG.
- `augment_questions.py` — Generates paraphrased test queries. Uses OpenAI if `OPENAI_API_KEY` is set; otherwise uses a deterministic fallback.
- `generate_expected_actual.py` — Parses a captured NotebookLM HTML page (via BeautifulSoup) to extract `expected.txt` and `actual.txt` without running a browser.

### Artifacts: `artifacts/`

Runtime outputs written by tests and scripts. Key files:

| File | Written by | Purpose |
|---|---|---|
| `expected.txt` | notebook tests / `generate_expected_actual.py` | Source passage text |
| `actual.txt` | notebook tests / `generate_expected_actual.py` | AI answer text |
| `semantic_score.txt` | `offline_scoring.py` | Latest single score |
| `semantic_results.csv` | `offline_scoring.py` | Append-only log of all test runs |
| `semantic_summary.json/csv` | `summary_report.py` | Aggregated metrics |
| `augmented_questions.jsonl` | `augment_questions.py` | LLM-augmented test queries |

## Key environment variables

| Variable | Default | Description |
|---|---|---|
| `NOTEBOOKLM_ARTIFACTS` | `./artifacts` | Directory for all captured artifacts |
| `SEMANTIC_SIM_THRESHOLD` | `0.65` | Minimum passing cosine similarity score |
| `RUN_SELENIUM` | unset | Set to `1` to enable Selenium test execution |
| `USER_DATA_DIR` | unset | Chrome profile path for Selenium (must be closed first) |
| `PLAYWRIGHT_TEST` | unset | Set to `1` to enable Playwright tests |
| `WEBDRIVER_WAIT` | `120` | Selenium WebDriverWait timeout in seconds |

## CI

The GitHub Actions workflow (`.github/workflows/ci.yml`) is fully commented out. Tests are not run automatically on push/PR.
