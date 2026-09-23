"""登录页面接口测试 — POST /api/auth/login 与 /api/auth/register。

登录页（LoginView）同时含登录卡与注册卡，两个端点统一在此模块测试，
按 YAML 用例的 path 区分登录（/api/auth/login）与注册（/api/auth/register）。
用例源：
  - tests/api/case/login.yaml
  - tests/api/case/register.yaml
"""

import pytest

from tests.api.loader import execute_case, load_cases

# 只取单请求用例：带 setup（多步流程，见 test_auth_session_flow.py）或
# concurrent（多请求，见 test_auth_register_concurrency.py）的用例由各自驱动执行。
CASES = [
    case
    for case in load_cases("login.yaml") + load_cases("register.yaml")
    if not case.get("setup") and not case.get("concurrent")
]


@pytest.mark.parametrize("case", CASES, ids=lambda c: f"{c['id']} {c['name']}")
@pytest.mark.api
@pytest.mark.auth
def test_login_page(base_url, api_session, unique_username, case):
    execute_case(base_url, api_session, case, {"unique_username": unique_username})
