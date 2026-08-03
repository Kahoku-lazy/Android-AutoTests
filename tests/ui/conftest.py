"""Pytest fixtures for frontend integration tests."""
import pytest
import requests
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


BASE_URL = "http://localhost:5173"
API_URL = "http://localhost:8765/api"


@pytest.fixture(scope="session")
def driver():
    """Session-scoped Chrome WebDriver with headless mode."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.implicitly_wait(5)
    yield driver
    driver.quit()


@pytest.fixture(scope="session")
def api():
    """Session-scoped requests session for API testing."""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def wait(driver):
    """Per-test explicit wait helper."""
    return WebDriverWait(driver, 10)


def pytest_configure(config):
    config.addinivalue_line("markers", "smoke: Quick smoke tests")
    config.addinivalue_line("markers", "navigation: Page routing tests")
    config.addinivalue_line("markers", "api: API integration tests")
    config.addinivalue_line("markers", "functional: Business logic tests")


# ── Helper fixtures ──

@pytest.fixture
def navigate(driver, wait):
    """Navigate to a page and wait for it to load."""
    def _navigate(path=""):
        url = f"{BASE_URL}/{path}" if path else BASE_URL
        driver.get(url)
        wait.until(lambda d: d.execute_script("return document.readyState") == "complete")
    return _navigate
