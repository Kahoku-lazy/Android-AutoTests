"""跨模块前端 E2E fixtures。

依赖：pytest-playwright、前后端已启动。
环境变量：
  TEST_FRONTEND_URL  默认 http://localhost:5173
  TEST_BASE_URL      默认 http://localhost:8766（见 tests/conftest.py）
"""

from __future__ import annotations

import os

import allure
import pytest
import requests

from tests.e2e.helpers import FRONTEND_URL, clear_auth

# ── Session 探测 ──


def _reachable(url: str, timeout: float = 2.0) -> bool:
    try:
        requests.get(url, timeout=timeout)
        return True
    except requests.RequestException:
        return False


@pytest.fixture(scope="session")
def frontend_url() -> str:
    return os.environ.get("TEST_FRONTEND_URL", FRONTEND_URL).rstrip("/")


@pytest.fixture(scope="session")
def e2e_services(frontend_url: str, base_url: str):
    """前后端不可达时跳过整组 E2E，避免硬 fail。"""
    if not _reachable(frontend_url):
        pytest.skip(f"前端不可达: {frontend_url}")
    if not _reachable(base_url):
        pytest.skip(f"后端不可达: {base_url}")
    return {"frontend": frontend_url, "backend": base_url}


@pytest.fixture
def admin_creds() -> dict[str, str]:
    return {"username": "admin", "password": "admin123"}


@pytest.fixture
def clean_page(page, e2e_services, frontend_url: str):
    """每用例干净浏览器态。依赖 e2e_services 做 skip。"""
    _ = e2e_services
    clear_auth(page, frontend_url=frontend_url)
    page.goto(f"{frontend_url}/login", wait_until="domcontentloaded")
    return page


# ── 失败自动截图（挂到 Allure）──


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """用例 call 阶段失败时截取当前页并附加到 Allure。"""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call" or not report.failed:
        return

    page = item.funcargs.get("clean_page") or item.funcargs.get("page")
    if page is None:
        return
    try:
        png = page.screenshot(full_page=True)
        allure.attach(
            png,
            name=f"失败截图 · {item.name}",
            attachment_type=allure.attachment_type.PNG,
        )
        allure.attach(
            getattr(page, "url", "") or "(unknown)",
            name="失败时 URL",
            attachment_type=allure.attachment_type.TEXT,
        )
    except Exception as exc:  # noqa: BLE001 — 截图失败不应掩盖原失败
        allure.attach(
            str(exc),
            name="截图失败原因",
            attachment_type=allure.attachment_type.TEXT,
        )
