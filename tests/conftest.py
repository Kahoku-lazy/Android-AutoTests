"""tests/ 共享 fixtures — 所有测试模块共用的前置依赖。"""

import os

import pytest
import requests

# ── 环境配置 ──

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8766")
LOGIN_PATH = "/api/ai/auth/login"


# ── Fixtures ──


@pytest.fixture(scope="session")
def base_url() -> str:
    """被测服务根地址，默认 http://localhost:8766。可通过 TEST_BASE_URL 环境变量覆盖。"""
    return BASE_URL


@pytest.fixture(scope="function")
def api_session() -> requests.Session:
    """预配置 Content-Type 的 requests.Session，每个测试函数独立实例。"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session
