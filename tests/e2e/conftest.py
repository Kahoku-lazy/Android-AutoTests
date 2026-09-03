"""黑盒·端到端测试层 fixtures — Playwright 真实浏览器。

依赖：pytest-playwright、前后端已启动。
环境变量：
  TEST_FRONTEND_URL        默认 http://localhost:5173
  TEST_BASE_URL            默认 http://localhost:8766（见 tests/conftest.py）
  TEST_ADMIN_USERNAME      默认 admin
  TEST_ADMIN_PASSWORD      必填（禁止硬编码）
"""

import os

import allure
import pytest
import requests

FRONTEND_URL = os.environ.get("TEST_FRONTEND_URL", "http://localhost:5173")


def _reachable(url: str, timeout: float = 2.0) -> bool:
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False


@pytest.fixture(scope="session")
def frontend_url() -> str:
    return FRONTEND_URL.rstrip("/")


@pytest.fixture(scope="session")
def e2e_services(frontend_url: str, base_url: str) -> dict:
    """前后端不可达时跳过整组 E2E，避免硬 fail。"""
    if not _reachable(frontend_url):
        pytest.skip(f"前端不可达: {frontend_url}")
    if not _reachable(base_url):
        pytest.skip(f"后端不可达: {base_url}")
    return {"frontend": frontend_url, "backend": base_url}


@pytest.fixture
def admin_creds() -> dict:
    username = os.environ.get("TEST_ADMIN_USERNAME", "admin")
    password = os.environ.get("TEST_ADMIN_PASSWORD", "")
    if not password:
        pytest.skip("未设置环境变量 TEST_ADMIN_PASSWORD，跳过 E2E")
    return {"username": username, "password": password}


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例 call 阶段失败时截图挂到 Allure。"""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return
    page = item.funcargs.get("page")
    if page is None:
        return
    try:
        png = page.screenshot(full_page=True)
        allure.attach(png, name=f"失败截图 · {item.name}", attachment_type=allure.attachment_type.PNG)
        allure.attach(getattr(page, "url", ""), name="失败时 URL", attachment_type=allure.attachment_type.TEXT)
    except Exception:  # noqa: BLE001 — 截图失败不掩盖原失败
        pass
