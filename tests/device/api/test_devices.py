"""
模块功能：➡️ 设备管理接口测试 — 鉴权 / 响应结构 / 404 错误路径 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/device/api/test_devices.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/device_pool
🏁
"""

import pytest

from tests.api_kit.loader import execute_case, load_cases

CASES = load_cases("devices.yaml")

UNAUTH_CASES = [c for c in CASES if c.get("auth") == "none"]
AUTH_CASES = [c for c in CASES if c.get("auth", "required") == "required"]


@pytest.mark.parametrize("case", UNAUTH_CASES, ids=lambda c: f"{c['id']} {c['name']}")
@pytest.mark.api
@pytest.mark.device_pool
def test_devices_unauthenticated(base_url, api_session, case):
    """无 token 访问，期望 401。"""
    execute_case(base_url, api_session, case, {})


@pytest.mark.parametrize("case", AUTH_CASES, ids=lambda c: f"{c['id']} {c['name']}")
@pytest.mark.api
@pytest.mark.device_pool
def test_devices_authenticated(base_url, auth_session, case):
    """带 token 访问，期望对应状态码与结构。"""
    execute_case(base_url, auth_session, case, {})
