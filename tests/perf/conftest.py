from __future__ import annotations

import os

from pathlib import Path

import pytest
import requests

from playwright.sync_api import sync_playwright

from tests.perf.page_load import launch_browser, load_budgets, login_tokens

DEFAULT_DEV_URL = "http://localhost:5173"
DEFAULT_PREVIEW_URL = "http://localhost:4173"
DEFAULT_API_URL = "http://localhost:8766"
REPORT_DIR = Path(__file__).resolve().parents[1] / "reports" / "perf"


def _enabled() -> bool:
    return os.environ.get("PERF_RUN") == "1" or bool(os.environ.get("PERF_BASE_URL"))


def _profile_for(base_url: str) -> str:
    explicit = os.environ.get("PERF_PROFILE")
    if explicit:
        return explicit
    return "preview" if ":4173" in base_url else "dev"


@pytest.fixture(scope="session")
def perf_base_url() -> str:
    if not _enabled():
        pytest.skip("perf 需显式开启：设置 PERF_RUN=1 或 PERF_BASE_URL=<前端地址>")
    return os.environ.get("PERF_BASE_URL", DEFAULT_DEV_URL)


@pytest.fixture(scope="session")
def perf_report_dir() -> Path:
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    return REPORT_DIR


@pytest.fixture(scope="session")
def perf_session(perf_base_url: str):
    try:
        requests.get(perf_base_url, timeout=3)
    except requests.RequestException:
        pytest.skip(f"前端不可达：{perf_base_url}（先用 python -m run start frontend 启动）")

    api_url = os.environ.get("PERF_API_URL", DEFAULT_API_URL)
    tokens = login_tokens(
        api_url,
        os.environ.get("PERF_USERNAME", "e2e_probe"),
        os.environ.get("PERF_PASSWORD", "e2e-probe-password"),
        os.environ.get("PERF_EMAIL", "e2e_probe@example.com"),
    )
    profile = _profile_for(perf_base_url)

    with sync_playwright() as pw:
        browser = launch_browser(pw, os.environ.get("PERF_CHANNEL", "chrome"))
        try:
            yield {
                "browser": browser,
                "tokens": tokens,
                "base_url": perf_base_url,
                "api_url": api_url,
                "profile": profile,
                "budgets": load_budgets(profile),
                "runs": int(os.environ.get("PERF_RUNS", "3")),
                "warmup": int(os.environ.get("PERF_WARMUP", "1")),
                "settle_ms": int(os.environ.get("PERF_SETTLE_MS", "2500")),
            }
        finally:
            browser.close()
