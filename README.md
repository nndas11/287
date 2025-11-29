# Semantic Similarity Project

Minimal Python project focused on semantic analysis and similarity search.

Quick start

1. Create a virtual environment and activate it (macOS / zsh):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Run the demo:

```bash
python examples/demo.py
```

3. Run the API locally:

```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

4. Open the Web UI

After starting the API, open `http://127.0.0.1:8000/static/index.html` to use the minimal web UI.

Notes
