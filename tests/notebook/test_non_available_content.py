import time
import os
from pathlib import Path
import pytest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from selenium.common.exceptions import NoSuchElementException
import numpy as np

from semantic import EmbeddingModel


# CONFIG – change these as needed
NOTEBOOKLM_URL = "https://notebooklm.google.com/"
NOTEBOOK_NAME = "Chromatic Roots and Derivatives"  # existing
TEST_QUERY = "what is Artificial Intelligence?"
EXPECTED_SOURCE_TITLE = "Primary Colors and Secondary Derivatives"


# Using shared `driver` and `wait` fixtures from `tests/conftest.py`


def test_verify_exact_passage_link(driver, wait):
    # 1. Go to NotebookLM home
    driver.get(NOTEBOOKLM_URL)

    # 2. Open the specific notebook by name
    notebook_card = (
        By.XPATH,
        f"//span[@class='project-button-title' and text()=' {NOTEBOOK_NAME} ']"
    )
    wait.until(EC.element_to_be_clickable(notebook_card)).click()

    save_note = (By.XPATH, "//span[text()='Save to note']")
    wait.until(EC.visibility_of_element_located(save_note))

    # 3. Wait for the chat input to be visible
    chat_input = (By.CSS_SELECTOR, "textarea[placeholder='Start typing...']")
    wait.until(EC.visibility_of_element_located(chat_input))

    # 4. Send a query that should produce a citation
    input_el = driver.find_element(*chat_input)
    input_el.clear()
    input_el.send_keys(TEST_QUERY)
    input_el.send_keys(Keys.ENTER)

    # Wait until "Save to note" is visible again (response rendered)
    wait.until(EC.visibility_of_element_located(save_note))

    # 5. Wait for the AI response to appear
    thinking_modal = (
        By.XPATH,
        "//div[contains(@class,'thinking-animation-container')]"
    )
    # Wait until thinking animation disappears
    wait.until(EC.invisibility_of_element_located(thinking_modal))

    last_answer_container = (
        By.XPATH,
        "//mat-card-content[contains(@class,'to-user-message-inner-content')]"
    )
    wait.until(EC.visibility_of_element_located(last_answer_container))

    answer_container = driver.find_element(*last_answer_container)

    # Capture some text from the answer (not asserted, just like Java code)
    answer_text_snippet = answer_container.text
   

    # 6. Locate the exact passage / citation link inside the answer (citation "1")
    last_citation = (
        By.XPATH,
        "//button[@dialoglabel='Citation Details']//span[text()='1']"
    )
    wait.until(EC.element_to_be_clickable(last_citation))

    # 7. Click the citation (exact passage link)
    driver.find_element(*last_citation).click()


    # 8. Wait for the source passage panel/viewer to appear
    source_panel = (By.CSS_SELECTOR, "div[class='elements-container']")
    source_viewer = wait.until(EC.visibility_of_element_located(source_panel))

    # 9. Verify the source title (if present)
    try:
        source_title_locator = (
            By.XPATH,
            "//div[@class='source-title-container']//div[contains(@class,'source-title')]"
        )
        source_title_element = source_viewer.find_element(*source_title_locator)
        actual_source_title = source_title_element.text
        print("Source title:", actual_source_title)

        if EXPECTED_SOURCE_TITLE and EXPECTED_SOURCE_TITLE.strip():
            assert EXPECTED_SOURCE_TITLE in actual_source_title, (
                f"Expected source title to contain '{EXPECTED_SOURCE_TITLE}' "
                f"but got '{actual_source_title}'"
            )
    except NoSuchElementException:
        print(
            "Source title element not found – "
            "adjust locator if you want this assertion."
        )

    # 10. Collect highlighted span texts from the source passage panel
    highlighted_spans = driver.find_elements(
        By.XPATH,
        "//div[@class='elements-container']//span[contains(@class, 'highlighted')]"
    )

    passage_text = []
    for span in highlighted_spans:
        text = span.text.strip()
        if text:
            passage_text.append(text)
            
    passage_text = " ".join(passage_text)
    print("Source text:", passage_text)
    print(f"Notebook Answer: {answer_text_snippet}")
    # Optional: you could add an assertion that at least one highlighted span exists
    assert passage_text, "No highlighted spans found in the source passage."

    # --- Write artifacts for offline scoring ---
    artifacts_dir = Path(os.environ.get("NOTEBOOKLM_ARTIFACTS", "artifacts"))
    artifacts_dir.mkdir(parents=True, exist_ok=True)

    # Write expected (source/passage) and actual (AI answer) files for reuse
    expected_path = artifacts_dir / "expected.txt"
    actual_path = artifacts_dir / "actual.txt"
    expected_path.write_text(passage_text or "", encoding="utf-8")
    actual_path.write_text(answer_text_snippet or "", encoding="utf-8")

    # Use the reusable offline scoring helper to compute and write the semantic score
    from scripts.offline_scoring import compute_and_write_score

    try:
        threshold = float(os.environ.get("SEMANTIC_SIM_THRESHOLD", "0.65"))
    except Exception:
        threshold = 0.65

    test_name = f"{Path(__file__).stem}::{TEST_QUERY}"
    sim = compute_and_write_score(artifacts_dir, threshold=threshold, test_name=test_name)
    print(f"Semantic cosine similarity: {sim:.6f}")
    assert sim >= threshold, (
        f"Semantic similarity {sim:.4f} is below threshold {threshold}"
    )   