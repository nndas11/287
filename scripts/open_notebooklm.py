#!/usr/bin/env python3
"""Open notebooklm.google.com and capture page HTML/screenshot.

Usage:
  - Install playwright in your virtualenv: `.venv/bin/python -m pip install playwright`
  - Install browsers: `.venv/bin/python -m playwright install`
  - Run interactively (headful) so you can log in and view answers:
      PYTHONPATH=. .venv/bin/python scripts/open_notebooklm.py
  - Run headless (CI) to capture page automatically (may require credentials/automation):
      NOTEBOOKLM_ARTIFACTS=artifacts .venv/bin/python scripts/open_notebooklm.py --headless --wait-ms 5000

This script is intentionally minimal: I/O and extraction points are left for you to
complete where you will read the expected/actual answers from the page DOM.
"""
import argparse
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description="Open notebooklm.google.com and capture page state")
    parser.add_argument("--headless", action="store_true", help="run browser in headless mode")
    parser.add_argument("--wait-ms", type=int, default=0, help="extra wait time in milliseconds after navigation")
    args = parser.parse_args()

    artifacts_dir = Path(os.environ.get("NOTEBOOKLM_ARTIFACTS", "artifacts"))
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    try:
        from playwright.sync_api import sync_playwright
    except Exception as e:
        print("Playwright is not installed. Install with: .venv/bin/python -m pip install playwright", file=sys.stderr)
        raise

    url = "https://notebooklm.google.com/"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless, args=["--disable-blink-features=AutomationControlled"])
        context = browser.new_context()
        page = context.new_page()
        print(f"Navigating to {url}...")
        page.goto(url, wait_until="domcontentloaded")

        # optional extra wait to allow scripts to render
        if args.wait_ms > 0:
            page.wait_for_timeout(args.wait_ms)

        if not args.headless:
            print("Running in headful mode. Please interact with the page (log in / open conversation).\n"
                  "When you're ready, press ENTER here to continue and capture the page.")
            input()

        # Save full HTML and a screenshot for later inspection / parsing
        html_path = artifacts_dir / "notebooklm_page.html"
        png_path = artifacts_dir / "notebooklm_screenshot.png"
        page_content = page.content()
        html_path.write_text(page_content, encoding="utf-8")
        page.screenshot(path=str(png_path), full_page=True)

        print(f"Saved HTML to: {html_path}")
        print(f"Saved screenshot to: {png_path}")

        # TODO: Add extraction code here to pull expected/actual answers from the DOM.
        # Example (pseudo):
        # answer_elem = page.query_selector("css-selector-for-answer")
        # actual_text = answer_elem.inner_text() if answer_elem else ""
        # Save or print actual_text for later semantic scoring.

        browser.close()


if __name__ == "__main__":
    main()
