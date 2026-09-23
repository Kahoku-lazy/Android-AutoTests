"""认证令牌类接口测试 — refresh / logout / me 的单请求用例。

用例源：tests/api/case/{refresh,logout,me}.yaml
带 setup 的多步用例（登出后再断言）由 tests/api/test_auth_session_flow.py 执行。
令牌占位符 {{admin_access_token}} / {{admin_refresh_token}} 由 admin_login fixture 现场登录签发。

按 YAML 里的 auth 字段分流 session（与 test_devices.py 同一约定）：
  - auth: none      → api_session（不带 Authorization）
  - auth: required  → admin_login 的 session（带 Authorization）
"""

import pytest

from tests.api.loader import execute_case, load_cases

CASES = [
    case for filename in ("refresh.yaml", "logout.yaml", "me.yaml") for case in load_cases(filename)
]
SINGLE = [case for case in CASES if not case.get("setup")]
UNAUTH_CASES = [case for case in SINGLE if case.get("auth") == "none"]
AUTH_CASES = [case for case in SINGLE if case.get("auth", "required") == "required"]


def _token_ctx(tokens: dict) -> dict:
    return {
        "admin_access_token": tokens["access_token"],
        "admin_refresh_token": tokens["refresh_token"],
    }


@pytest.mark.parametrize("case", UNAUTH_CASES, ids=lambda c: f"{c['id']} {c['name']}")
@pytest.mark.api
@pytest.mark.auth
def test_auth_tokens_unauthenticated(base_url, api_session, admin_login, case):
    """不带 Authorization 头：refresh 系列与「未带令牌登出」。"""
    _, tokens = admin_login
    execute_case(base_url, api_session, case, _token_ctx(tokens))


@pytest.mark.parametrize("case", AUTH_CASES, ids=lambda c: f"{c['id']} {c['name']}")
@pytest.mark.api
@pytest.mark.auth
def test_auth_tokens_authenticated(base_url, admin_login, case):
    """带 Authorization 头：正常登出与读取身份。"""
    session, tokens = admin_login
    execute_case(base_url, session, case, _token_ctx(tokens))
