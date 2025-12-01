import os
import shutil
import tempfile
import pytest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait


@pytest.fixture(scope="session")
def driver():
    """Create a single Chrome webdriver for the entire pytest session.

    Behavior:
    - If `RUN_SELENIUM` != "1", tests using this fixture will be skipped.
    - If `USER_DATA_DIR` is set in the environment, it will be passed to Chrome
      (use a copied profile if the real profile is in-use).
    - Otherwise, Chrome runs in headless mode with a temporary profile.
    """
    if os.environ.get("RUN_SELENIUM") != "1":
        pytest.skip("Selenium tests are disabled by default. Set RUN_SELENIUM=1 to enable.")

    chrome_options = Options()
    user_data = os.environ.get("USER_DATA_DIR")
    temp_profile = None
    if user_data:
        # Use provided profile directory
        chrome_options.add_argument(f"user-data-dir={user_data}")
    else:
        # Use a temporary profile in headless mode to avoid interfering with local Chrome
        temp_profile = tempfile.mkdtemp(prefix="selenium-profile-")
        chrome_options.add_argument(f"user-data-dir={temp_profile}")
        chrome_options.add_argument("--headless=new")

    # Common flags to improve reliability in CI/local envs
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")

    service = Service()
    driver = webdriver.Chrome(service=service, options=chrome_options)
    driver.maximize_window()

    yield driver

    try:
        driver.quit()
    finally:
        if temp_profile and os.path.isdir(temp_profile):
            shutil.rmtree(temp_profile, ignore_errors=True)


@pytest.fixture
def wait(driver):
    timeout = int(os.environ.get("WEBDRIVER_WAIT", "120"))
    return WebDriverWait(driver, timeout)
