import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(os.environ.get("PLAYWRIGHT_TEST") != "1",
                    reason="Playwright integration tests disabled by default. Set PLAYWRIGHT_TEST=1 to enable")
def test_open_notebooklm_creates_artifacts(tmp_path):
    """Run the `scripts/open_notebooklm.py` script (headless) and assert artifacts were created.

    This test is disabled by default because Playwright browsers may not be installed in CI.
    To run locally:

      1. Install playwright and browsers in the repo venv:
         .venv/bin/python -m pip install playwright
         .venv/bin/python -m playwright install

      2. Run pytest with the env flag set:
         PLAYWRIGHT_TEST=1 NOTEBOOKLM_ARTIFACTS=./artifacts .venv/bin/python -m pytest tests/test_notebooklm.py -q

    After enabling, the test will run the script in headless mode and verify that the
    HTML and screenshot files exist.
    """
    artifacts_dir = tmp_path / "artifacts"
    env = os.environ.copy()
    env["NOTEBOOKLM_ARTIFACTS"] = str(artifacts_dir)

    cmd = [sys.executable, "scripts/open_notebooklm.py", "--headless", "--wait-ms", "3000"]
    subprocess.run(cmd, check=True, env=env)

    html_path = artifacts_dir / "notebooklm_page.html"
    png_path = artifacts_dir / "notebooklm_screenshot.png"

    assert html_path.exists(), "HTML artifact not created"
    assert png_path.exists(), "Screenshot artifact not created"
