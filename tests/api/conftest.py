"""接口测试层 fixtures — 黑盒 HTTP（live server）。

约定：
  - 不依赖 django_db，直接对运行中的后端发 HTTP 请求
  - 用例定义在 tests/api/case/*.yaml，JSONSchema 在 tests/api/schemas.py
  - 测试凭据为开发环境默认种子账号（admin/admin123），直接写进 YAML 用例
"""

import uuid

import pytest
import requests


@pytest.fixture(scope="function")
def api_session() -> requests.Session:
    """预配置 JSON Content-Type 的 requests.Session，每个测试函数独立实例。"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def unique_username() -> str:
    """每次调用生成唯一用户名，供 {{unique_username}} 占位符使用。"""
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def auth_session(base_url) -> requests.Session:
    """登录获取 access_token，返回带 Authorization 头的 session（供鉴权端点用）。"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    resp = session.post(
        f"{base_url}/api/auth/login", json={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    token = resp.json()["data"]["access_token"]
    session.headers.update({"Authorization": f"Bearer {token}"})
    return session
