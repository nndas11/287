# Semantic Similarity Project

Minimal Python project focused on semantic analysis and similarity search.

**Quick Start**

- **Create venv:** `python3 -m venv .venv`
- **Activate (macOS / zsh):** `source .venv/bin/activate`
- **Install deps:** `pip install -r requirements.txt`

**Run the API (local)**

- Start the FastAPI app:

  ```bash
  uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
  ```

- Open the minimal web UI at `http://127.0.0.1:8000/static/index.html` after the server starts.


**Running tests**

- Run the unit tests (fast):

  ```bash
  .venv/bin/python -m pytest -q
  ```

- Browser-based tests (Selenium / Playwright) are disabled by default. Enable them explicitly when you have the required browsers and drivers installed.

  - Selenium example (uses your Chrome profile):

    ```bash
    RUN_SELENIUM=1 \
    USER_DATA_DIR=/path/to/your/chrome-profile \
    NOTEBOOKLM_ARTIFACTS=./artifacts \
    SEMANTIC_SIM_THRESHOLD=0.65 \
    .venv/bin/python -m pytest -s tests/test_notebooklm_selenium.py::test_verify_exact_passage_link -q
    ```

  - Playwright tests (if you have Playwright and browsers installed):

    ```bash
    PLAYWRIGHT_TEST=1 NOTEBOOKLM_ARTIFACTS=./artifacts .venv/bin/python -m pytest -q tests/test_notebooklm.py
    ```

**Important environment variables**

- `NOTEBOOKLM_ARTIFACTS`: Directory to save captured HTML, screenshots, and extracted artifacts (default: `./artifacts`).
- `SEMANTIC_SIM_THRESHOLD`: Floating-point threshold for semantic similarity assertions (default: `0.65`).
- `RUN_SELENIUM`: Set to `1` to enable Selenium tests under pytest.
- `PLAYWRIGHT_TEST`: Set to `1` to enable Playwright capture tests.
- `USER_DATA_DIR`: When using Selenium + Chrome, set this to your Chrome profile directory if you want to reuse bookmarks/history (close Chrome first or use a copy of the profile to avoid lock errors).

**Artifacts & scoring**

- Browser tests write extracted texts and a computed semantic similarity score into the `NOTEBOOKLM_ARTIFACTS` directory (by default `./artifacts`).
- The Selenium test (`tests/test_notebooklm_selenium.py`) computes embeddings with `sentence-transformers` and writes a score file (`semantic_score.txt`). You can run a separate offline scoring test by creating two text files (expected/actual) in the artifacts folder and computing similarity with the `semantic` package.

**New: Helpers for artifact extraction and offline scoring**

This repo includes two helper scripts to standardize the flow from browser capture -> artifact extraction -> offline scoring:

- `scripts/generate_expected_actual.py` — Parse an HTML artifact (e.g. `notebooklm_page.html`) and extract the AI answer and highlighted source passage, writing `actual.txt` and `expected.txt` into the artifacts directory. This helper uses BeautifulSoup; install with:

  ```bash
  .venv/bin/python -m pip install beautifulsoup4
  ```

- `scripts/offline_scoring.py` — Reusable scoring helper (importable) that reads `expected.txt` and `actual.txt` from the artifacts directory, computes embeddings using the `semantic` package, writes `semantic_score.txt`, and returns the similarity score. It optionally enforces a threshold (raises an AssertionError if the score is below the configured threshold).

Example workflow (end-to-end):

1. Run the Selenium/Playwright capture so the NotebookLM page HTML is saved under the artifacts directory (default `./artifacts`).

2. Extract expected/actual from the HTML (if you didn't already write them directly):

```bash
NOTEBOOKLM_ARTIFACTS=./artifacts python scripts/generate_expected_actual.py
```

3. Compute and persist the semantic score (helper will write `semantic_score.txt`):

```bash
NOTEBOOKLM_ARTIFACTS=./artifacts SEMANTIC_SIM_THRESHOLD=0.65 python -c "from scripts.offline_scoring import compute_and_write_score; print(compute_and_write_score('./artifacts', threshold=0.65))"
```

4. Or run the offline pytest which uses the same helper (skips if artifacts are missing):

```bash
NOTEBOOKLM_ARTIFACTS=./artifacts SEMANTIC_SIM_THRESHOLD=0.65 .venv/bin/python -m pytest -q tests/test_offline_scoring.py
```

Notes:

- The Selenium test was updated to write `expected.txt` and `actual.txt` directly and then call the scoring helper; that is the simplest and most robust flow.
- If the NotebookLM DOM changes or your artifact filenames differ, update `scripts/generate_expected_actual.py` selectors accordingly or write `expected.txt`/`actual.txt` directly from the capture script.

**Selenium notes / troubleshooting**

- If you see `session not created: Chrome instance exited`, it often means the Chrome profile is in use or incompatible with the driver. Close Chrome, or pass a copy of the profile to `USER_DATA_DIR`.
- If you prefer isolation, run Chrome with a fresh temporary profile (omit `USER_DATA_DIR`) so Chrome/Chromedriver create a new profile for the test run.

**Contributing**

- Fixes and improvements welcome. Open a PR with small, focused commits. If you change dependencies, update `requirements.txt` and note platform-specific packages (e.g., `faiss-cpu` may not be available on macOS).

**Contact / Next steps**

- For help running the browser tests or creating an offline scoring harness, tell me which environment you prefer (local Chrome, headless CI, Playwright) and I can add a ready-to-run pytest wrapper.
