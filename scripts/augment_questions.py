#!/usr/bin/env python3
"""Generate augmented NotebookLM-style questions using an LLM (or a safe fallback).

This script reads a source of test queries (either `semantic_results.csv`'s
`test_name` column or a plain `--queries-file`) and produces augmented
questions to exercise NotebookLM in slightly different ways.

Behavior:
- If `OPENAI_API_KEY` is present and the `openai` package is installed,
  the script will call the OpenAI ChatCompletion API (configurable `--model`).
- Otherwise, the script will use a deterministic, non-ML fallback that
  produces simple paraphrases and question variants. This ensures the
  script is safe to run in any environment and won't modify tests.

Outputs are written as JSONL (one JSON object per line) to `--out`.

Examples:
  python scripts/augment_questions.py --source artifacts/semantic_results.csv --out artifacts/augmented_questions.jsonl --n 5

Notes:
- This script does not modify tests or test code; it only writes augmentation
  artifacts under the artifacts folder by default.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Iterable


def extract_queries_from_results(path: Path) -> List[str]:
    if not path.exists():
        return []
    queries = []
    with path.open("r", encoding="utf-8") as f:
        reader = csv.reader(f)
        headers = next(reader, None)
        # If headers look like a header row, try to use DictReader instead
        if headers and any(h and h.strip().lower() in ("test_name",) for h in headers):
            f.seek(0)
            dict_reader = csv.DictReader(f)
            for r in dict_reader:
                tn = r.get("test_name") or ""
                # many rows use format: test_fn::<query>
                parts = tn.split("::", 1)
                if len(parts) == 2:
                    queries.append(parts[1].strip())
        else:
            # fallback: try to parse rows where second column is "test_name"
            f.seek(0)
            for row in reader:
                if len(row) > 1:
                    candidate = row[1]
                    if "::" in candidate:
                        parts = candidate.split("::", 1)
                        queries.append(parts[1].strip())
    # deduplicate while preserving order
    seen = set()
    out = []
    for q in queries:
        if q and q not in seen:
            seen.add(q)
            out.append(q)
    return out


def read_queries_file(path: Path) -> List[str]:
    if not path.exists():
        return []
    lines = [l.strip() for l in path.read_text(encoding="utf-8").splitlines()]
    return [l for l in lines if l]


def fallback_augment(query: str, n: int = 3) -> List[str]:
    """Produce simple deterministic augmentations without an LLM.

    These are lightweight paraphrases and variants that are safe to run anywhere.
    """
    variants = set()
    # basic templates
    templates = [
        "Please list: {}",
        "Give me a short list for: {}",
        "Provide three concise answers for: {}",
        "In one sentence, answer: {}",
        "What are the primary answers to: {}",
    ]
    words = query.split()
    # produce mixes: templates + simple rewordings
    for t in templates:
        variants.add(t.format(query))

    # simple shuffle-based paraphrases (deterministic via seed from query)
    rand = random.Random(hash(query) & 0xFFFFFFFF)
    for i in range(n * 2):
        arr = words[:]
        if len(arr) > 3:
            rand.shuffle(arr)
            cand = " ".join(arr)
            variants.add(f"Paraphrase: {cand}")

    # fall back to split-question forms
    if "?" in query:
        variants.add(query.replace("?", " now?"))
    else:
        variants.add(query + "?")

    out = list(variants)
    out = out[:max(n, 1)]
    return out


def call_openai_chat(queries: Iterable[str], model: str, n_per: int, temperature: float = 0.8):
    """Call OpenAI ChatCompletion to generate augmentations.

    Returns dict mapping original query -> list of generated strings.
    Requires `openai` package and `OPENAI_API_KEY` env var.
    """
    try:
        from openai import OpenAI
    except Exception as e:
        raise RuntimeError("openai package not installed") from e

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY not set")
    client = OpenAI(api_key=api_key)

    out = {}
    for q in queries:
        prompt = (
            "You are a helpful assistant that creates alternative test questions for NotebookLM.\n"
            "Given the original user query, produce a list of concise paraphrases and variant prompts (no commentary).\n"
            f"Original: {q}\n"
            "Output format: JSON array of strings."
        )
        try:
            resp = client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=512,
            )
            txt = resp.choices[0].message.content
            if not txt:
                print(f"Warning: Empty response for query '{q}'")
                out[q] = []
                continue
            txt = txt.strip()
            # attempt to parse JSON array from response
            try:
                arr = json.loads(txt)
                if isinstance(arr, list):
                    out[q] = [str(x) for x in arr][:n_per]
                    continue
            except Exception:
                # fallback: split lines
                lines = [ln.strip('-* 0123456789.\t') for ln in txt.splitlines() if ln.strip()]
                out[q] = [ln for ln in lines][:n_per]
        except Exception as e:
            # propagate the error to allow caller to decide; do not crash the whole run
            raise

    return out


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser()
    default_art = os.environ.get("NOTEBOOKLM_ARTIFACTS", "./artifacts")
    p.add_argument("--source", default=str(Path(default_art) / "semantic_results.csv"), help="Path to results CSV to extract queries from")
    p.add_argument("--queries-file", default=None, help="Plain file with one query per line (optional). If omitted, the script will use $NOTEBOOKLM_ARTIFACTS/queries.txt when present.")
    p.add_argument("--out", default=str(Path(default_art) / "augmented_questions.jsonl"), help="Output JSONL file")
    p.add_argument("--model", default="gpt-3.5-turbo", help="OpenAI model to use when OPENAI_API_KEY is present")
    p.add_argument("--n", type=int, default=3, help="Number of augmentations per input")
    p.add_argument("--temperature", type=float, default=0.8, help="Sampling temperature for LLM")
    args = p.parse_args(argv)

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    queries: List[str] = []
    # Priority: explicit --queries-file -> $NOTEBOOKLM_ARTIFACTS/queries.txt -> CSV source
    if args.queries_file:
        queries = read_queries_file(Path(args.queries_file))
    else:
        default_queries = Path(default_art) / "queries.txt"
        if default_queries.exists():
            queries = read_queries_file(default_queries)
        else:
            queries = extract_queries_from_results(Path(args.source))

    if not queries:
        print("No queries found in source. Provide --queries-file or a CSV with test_name entries.")
        return 2

    use_openai = False
    try:
        from openai import OpenAI
    except Exception:
        print("augment_questions: 'openai' package not importable; using fallback augmentation.")
        use_openai = False
    else:
        if not os.environ.get("OPENAI_API_KEY"):
            print("augment_questions: OPENAI_API_KEY not set in this environment; using fallback augmentation.")
            use_openai = False
        else:
            use_openai = True

    results = []
    timestamp = datetime.now(timezone.utc).isoformat()

    if use_openai:
        try:
            gen = call_openai_chat(queries, model=args.model, n_per=args.n, temperature=args.temperature)
        except Exception as e:
            print(f"OpenAI call failed: {e}")
            print("Falling back to local augmentations.")
            gen = {q: fallback_augment(q, n=args.n) for q in queries}
    else:
        gen = {q: fallback_augment(q, n=args.n) for q in queries}

    with out_path.open("w", encoding="utf-8") as f:
        for q in queries:
            augments = gen.get(q, [])
            for a in augments:
                rec = {
                    "timestamp": timestamp,
                    "original": q,
                    "augmented": a,
                    "method": "openai" if use_openai else "fallback",
                }
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                results.append(rec)

    print(f"Wrote {len(results)} augmented prompts to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
