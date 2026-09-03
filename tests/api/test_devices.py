"""设备管理接口测试 — 鉴权 / 响应结构 / 404 错误路径。

黑盒 HTTP（live server），保持约定不依赖 django_db。
扫描/连接成功等需真实设备、400/409 需设备记录的路径，留给集成测试与真机验证。

用例源：tests/api/case/devices.yaml
"""

import pytest

from tests.api.loader import execute_case, load_cases

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
