#!/usr/bin/env python3
"""Generate `expected.txt` and `actual.txt` from NotebookLM HTML artifacts.

This looks for an HTML file in the artifacts directory (default: ./artifacts),
parses it, extracts the AI answer text and the highlighted source passage, and
writes two files:

- `expected.txt` : the source/passage text (used as expected)
- `actual.txt`   : the AI answer snippet (used as actual)

The script prefers BeautifulSoup for robustness. Install with:

  pip install beautifulsoup4

Usage:

  NOTEBOOKLM_ARTIFACTS=./artifacts python scripts/generate_expected_actual.py

"""
from pathlib import Path
import sys
import os

try:
    from bs4 import BeautifulSoup
except Exception:
    print("BeautifulSoup4 is required: pip install beautifulsoup4")
    sys.exit(2)


def find_html_file(artifacts_dir: Path):
    # Prefer a file named notebooklm_page.html; otherwise take first .html
    p = artifacts_dir / "notebooklm_page.html"
    if p.exists():
        return p
    html_files = sorted(artifacts_dir.glob("*.html"))
    if html_files:
        return html_files[0]
    # fallback: search recursively
    html_files = sorted(artifacts_dir.rglob("*.html"))
    return html_files[0] if html_files else None


def extract_texts(html_path: Path):
    text = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(text, "html.parser")

    # Answer: last element with class containing 'to-user-message-inner-content'
    answer_nodes = soup.select(".to-user-message-inner-content")
    answer_text = answer_nodes[-1].get_text(separator=" ", strip=True) if answer_nodes else ""

    # Passage: highlighted spans inside elements-container
    passage_spans = soup.select("div.elements-container span.highlighted")
    passage_text = " ".join([s.get_text(separator=" ", strip=True) for s in passage_spans])

    return answer_text, passage_text


def main():
    art_dir = Path(os.environ.get("NOTEBOOKLM_ARTIFACTS", "./artifacts"))
    if not art_dir.exists():
        print(f"Artifacts directory not found: {art_dir}")
        sys.exit(1)

    html_file = find_html_file(art_dir)
    if not html_file:
        print("No HTML artifact found in", art_dir)
        sys.exit(1)

    print("Parsing HTML artifact:", html_file)
    answer_text, passage_text = extract_texts(html_file)

    if not answer_text and not passage_text:
        print("No answer text or passage found in HTML. Check selectors or artifact contents.")
        sys.exit(1)

    # According to the offline scoring test, expected.txt should contain the source/passage
    expected_path = art_dir / "expected.txt"
    actual_path = art_dir / "actual.txt"

    expected_path.write_text(passage_text or "", encoding="utf-8")
    actual_path.write_text(answer_text or "", encoding="utf-8")

    print(f"Wrote expected -> {expected_path}")
    print(f"Wrote actual   -> {actual_path}")


if __name__ == "__main__":
    main()
