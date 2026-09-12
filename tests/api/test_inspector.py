"""设备检查器接口测试 — 鉴权 / 参数校验 / 404/400 错误路径。

黑盒 HTTP（live server），保持约定不依赖 django_db。
抓取成功等需真实设备的路径，留给集成测试与真机验证。

用例源：tests/api/case/inspector.yaml
"""

import pytest

from tests.api.loader import execute_case, load_cases

CASES = load_cases("inspector.yaml")

UNAUTH_CASES = [c for c in CASES if c.get("auth") == "none"]
AUTH_CASES = [c for c in CASES if c.get("auth", "required") == "required"]


@pytest.mark.parametrize("case", UNAUTH_CASES, ids=lambda c: f"{c['id']} {c['name']}")
@pytest.mark.api
@pytest.mark.device_inspector
def test_inspector_unauthenticated(base_url, api_session, case):
    """无 token 访问，期望 401。"""
    execute_case(base_url, api_session, case, {})


@pytest.mark.parametrize("case", AUTH_CASES, ids=lambda c: f"{c['id']} {c['name']}")
@pytest.mark.api
@pytest.mark.device_inspector
def test_inspector_authenticated(base_url, auth_session, case):
    """带 token 访问，期望对应状态码与结构。"""
    execute_case(base_url, auth_session, case, {})
