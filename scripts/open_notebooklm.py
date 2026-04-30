#!/usr/bin/env python3
"""Open NotebookLM with Playwright, save HTML + screenshot to NOTEBOOKLM_ARTIFACTS."""
import argparse
import os
from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "https://notebooklm.google.com/"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--headless", action="store_true")
    parser.add_argument("--wait-ms", type=int, default=3000)
    args = parser.parse_args()

    artifacts_dir = Path(os.environ.get("NOTEBOOKLM_ARTIFACTS", "./artifacts"))
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=args.headless)
        page = browser.new_page()
        page.goto(URL)
        page.wait_for_timeout(args.wait_ms)

        (artifacts_dir / "notebooklm_page.html").write_text(page.content())
        page.screenshot(path=str(artifacts_dir / "notebooklm_screenshot.png"), full_page=True)
        browser.close()


if __name__ == "__main__":
    main()
