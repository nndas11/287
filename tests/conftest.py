import os
import shutil
import tempfile
import pytest

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait

# Persistent Selenium session profile — Google session is saved here after first login.
# Chrome's security policy blocks DevTools on the real default profile, so we use
# a separate directory. First run requires a one-time manual login in the Chrome window.
SESSION_PROFILE = "/tmp/notebooklm-selenium-session"


@pytest.fixture(scope="session")
def driver():
    """Create a single Chrome webdriver for the entire pytest session."""
    if os.environ.get("RUN_SELENIUM") != "1":
        pytest.skip("Selenium tests are disabled by default. Set RUN_SELENIUM=1 to enable.")

    user_data = os.environ.get("USER_DATA_DIR")
    temp_profile = None

    chrome_options = Options()

    if user_data:
        profile_dir = SESSION_PROFILE
        chrome_options.add_argument(f"--user-data-dir={profile_dir}")
    else:
        temp_profile = tempfile.mkdtemp(prefix="selenium-profile-")
        chrome_options.add_argument(f"--user-data-dir={temp_profile}")
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")

    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--start-maximized")
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option("useAutomationExtension", False)

    driver = webdriver.Chrome(service=Service(), options=chrome_options)
    driver.execute_cdp_cmd(
        "Page.addScriptToEvaluateOnNewDocument",
        {"source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"},
    )

    driver.get("https://notebooklm.google.com/")

    # If redirected to Google sign-in, wait up to 3 minutes for the user to log in
    if "accounts.google.com" in (driver.current_url or ""):
        print("\n" + "="*60)
        print("ACTION REQUIRED: Log into Google in the Chrome window.")
        print("Tests will start automatically once you are signed in.")
        print("="*60 + "\n")
        WebDriverWait(driver, 180).until(
            lambda d: d.current_url is not None
                      and "notebooklm.google.com" in d.current_url
                      and "accounts.google.com" not in d.current_url
        )
        print("Logged in — starting tests...\n")

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
