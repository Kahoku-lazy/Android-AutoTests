"""认证模块测试共享基础设施 — fixtures / 端点常量 / allure 工具。

此 conftest.py 与 tests/conftest.py 分层：
  tests/conftest.py       → 全局 fixture（base_url, api_session）
  tests/auth/conftest.py  → 认证模块 fixture（端点常量, 动态用户名）
"""

import uuid

import allure
import pytest

# ── 端点常量（避免 URL 字符串散落各测试函数） ──

LOGIN_URL = "/api/auth/login"
REGISTER_URL = "/api/auth/register"
REFRESH_URL = "/api/auth/refresh"
LOGOUT_URL = "/api/auth/logout"
ME_URL = "/api/auth/me"


# ── 动态数据工厂 ──


@pytest.fixture
def unique_username() -> str:
    """每次调用生成唯一用户名，避免注册测试间 DB 冲突。"""
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="session")
def auth_token(base_url: str) -> dict:
    """登录获取有效 Token 对，供 logout / me 测试复用。

    Returns:
        dict: {"access_token": str, "refresh_token": str}
    """
    import requests

    resp = requests.post(
        f"{base_url}{LOGIN_URL}",
        json={"username": "admin", "password": "admin123"},
        timeout=10,
    )
    body = resp.json()
    assert body.get("status") is True, body
    data = body["data"]
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


# ── Allure 元数据辅助 ──


def set_allure_metadata(
    feature: str,
    story: str,
    title: str,
    description: str,
    severity: str,
    tags: tuple[str, ...],
) -> None:
    """单次调用完成 Allure 报告元数据设置。

    Args:
        feature: allure.feature（如 "认证模块"）
        story: allure.story（如 "注册接口"）
        title: allure.title（如 "TC-REG-004: 用户名和密码均为空"）
        description: allure.description（多行文本）
        severity: allure.severity_level 属性名（"blocker"/"critical"/"normal"/"minor"）
        tags: allure.tag 元组（如 ("auth", "api", "P0")）
    """
    allure.dynamic.feature(feature)
    allure.dynamic.story(story)
    allure.dynamic.title(title)
    allure.dynamic.description(description)
    allure.dynamic.severity(getattr(allure.severity_level, severity.upper()))
    allure.dynamic.tag(*tags)
