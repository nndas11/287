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
NOTEBOOK_NAME = "Automated Software Testing"
TEST_QUERY = "Name two advantages of automated software testing."
EXPECTED_SOURCE_TITLE = os.environ.get("EXPECTED_SOURCE_TITLE", "Automated software testing")


# Using shared `driver` and `wait` fixtures from `tests/conftest.py`


def test_verify_exact_passage_link(driver, wait):
    # 1. Go to NotebookLM home
    driver.get(NOTEBOOKLM_URL)

    # 2. Open the specific notebook by name
    notebook_title = wait.until(
        EC.visibility_of_element_located(
            (
                By.XPATH,
                (
                    "//span[contains(@class,'project-button-title') and "
                    f"contains(normalize-space(.), '{NOTEBOOK_NAME}')]"
                ),
            )
        )
    )
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", notebook_title)
    clickable_targets = [
        *notebook_title.find_elements(
            By.XPATH,
            (
                "./ancestor::mat-card[contains(@class,'project-button-card')]"
                "|./ancestor::project-button"
                "|./ancestor::*[self::a or self::button or @role='button' or contains(@class,'primary-action-button')]"
            ),
        ),
        notebook_title,
    ]
    clicked = False
    for target in clickable_targets:
        try:
            wait.until(lambda _: target.is_displayed() and target.is_enabled())
            try:
                target.click()
            except Exception:
                driver.execute_script("arguments[0].click();", target)
            clicked = True
            break
        except Exception:
            continue
    assert clicked, f"Could not click notebook card for '{NOTEBOOK_NAME}'"

    save_note = (By.XPATH, "//span[text()='Save to note']")
    wait.until(EC.visibility_of_element_located(save_note))

    # 3. Wait for the chat input to be visible
    chat_input = wait.until(
        lambda d: (
            d.find_elements(By.CSS_SELECTOR, "textarea[placeholder='Start typing...']")
            or d.find_elements(By.CSS_SELECTOR, "textarea[placeholder*='Start']")
            or d.find_elements(By.CSS_SELECTOR, "textarea[aria-label*='Ask']")
            or d.find_elements(By.CSS_SELECTOR, "textarea")
        )[0]
    )

    # 4. Send a query that should produce a citation
    input_el = chat_input
    input_el.click()
    input_el.clear()
    input_el.send_keys(TEST_QUERY)
    input_el.send_keys(Keys.ENTER)

    # 5. Wait for the AI response to render and stabilize
    wait.until(EC.visibility_of_element_located(save_note))
    thinking_modal = (By.XPATH, "//div[contains(@class,'thinking-animation-container')]")
    wait.until(EC.invisibility_of_element_located(thinking_modal))

    last_answer_container = (
        By.XPATH,
        "//mat-card-content[contains(@class,'to-user-message-inner-content')]",
    )
    answer_container = wait.until(EC.visibility_of_element_located(last_answer_container))
    wait.until(lambda d: len((answer_container.text or "").strip()) > 30)
    answer_text_snippet = answer_container.text.strip()

    # 6. Locate the exact passage / citation link inside the answer (citation "1")
    def _first_citation_button(d):
        candidates = (
            d.find_elements(By.XPATH, "//button[@dialoglabel='Citation Details']//span[normalize-space()='1']/ancestor::button[1]")
            or d.find_elements(By.XPATH, "//button[contains(@aria-label,'Citation') and .//span[normalize-space()='1']]")
            or d.find_elements(By.XPATH, "//button[.//span[normalize-space()='1'] and (@dialoglabel='Citation Details' or contains(@aria-label,'Citation'))]")
            or d.find_elements(By.XPATH, "//button[.//*[normalize-space()='1'] and contains(@class,'citation')]")
        )
        return candidates[0] if candidates else False

    citation_btn = wait.until(_first_citation_button)

    # 7. Click the citation (exact passage link)
    try:
        citation_btn.click()
    except Exception:
        driver.execute_script("arguments[0].click();", citation_btn)


    # 8. Wait for the source passage panel/viewer to appear
    def _source_viewer(d):
        candidates = (
            d.find_elements(By.CSS_SELECTOR, "div.elements-container")
            or d.find_elements(By.XPATH, "//div[contains(@class,'elements-container')]")
            or d.find_elements(By.XPATH, "//div[contains(@class,'source') and .//span[contains(@class,'highlight')]]")
            or d.find_elements(By.XPATH, "//div[.//span[contains(@class,'highlighted')]]")
        )
        return candidates[0] if candidates else False

    source_viewer = wait.until(_source_viewer)

    # 9. Verify the source title (if present)
    source_title_candidates = (
        source_viewer.find_elements(By.XPATH, ".//div[contains(@class,'source-title')]")
        or source_viewer.find_elements(By.XPATH, ".//div[contains(@class,'source-title-container')]//div")
        or driver.find_elements(By.XPATH, "//div[contains(@class,'source-title')]")
    )
    if source_title_candidates:
        actual_source_title = source_title_candidates[0].text
        print("Source title:", actual_source_title)
        if EXPECTED_SOURCE_TITLE and EXPECTED_SOURCE_TITLE.strip():
            assert EXPECTED_SOURCE_TITLE in actual_source_title, (
                f"Expected source title to contain '{EXPECTED_SOURCE_TITLE}' "
                f"but got '{actual_source_title}'"
            )
    else:
        print("Source title element not found; continuing with highlighted passage validation.")

    # 10. Collect highlighted span texts from the source passage panel
    highlighted_spans = wait.until(
        lambda d: (
            source_viewer.find_elements(By.XPATH, ".//span[contains(@class, 'highlighted')]")
            or source_viewer.find_elements(By.XPATH, ".//*[contains(@class, 'highlight')]")
            or d.find_elements(By.XPATH, "//div[contains(@class,'elements-container')]//span[contains(@class,'highlighted')]")
            or d.find_elements(By.XPATH, "//*[contains(@class,'highlighted')]")
        )
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