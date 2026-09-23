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
def admin_login(base_url) -> tuple[requests.Session, dict]:
    """现场登录种子账号，返回 (带 Authorization 头的 session, {"access_token", "refresh_token"})。

    令牌现场签发而不是写进 YAML：JWT 默认 1 小时过期，写死的令牌第二天就会让用例变红；
    同时保证「登出 → 断言失效」类用例吊销的正是这份凭证所属的那个会话（同 sid）。
    """
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    resp = session.post(
        f"{base_url}/api/auth/login/", json={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    data = resp.json()["data"]
    session.headers.update({"Authorization": f"Bearer {data['access_token']}"})
    return session, {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


@pytest.fixture(scope="function")
def auth_session(admin_login) -> requests.Session:
    """带 Authorization 头的 session（供鉴权端点用）；令牌来源见 admin_login。"""
    return admin_login[0]
