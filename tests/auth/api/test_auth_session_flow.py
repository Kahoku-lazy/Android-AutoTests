"""
模块功能：➡️ 会话生命周期流程用例 — 登出后 access 与 refresh 同时失效 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/auth/api/test_auth_session_flow.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 backend/apps/accounts（账号与会话）
🏁
"""

import pytest

from tests.api_kit.loader import execute_case, load_cases

FLOW_CASES = [
    case
    for filename in ("logout.yaml", "refresh.yaml", "me.yaml")
    for case in load_cases(filename)
    if case.get("setup") == "logout"
]


@pytest.mark.parametrize("case", FLOW_CASES, ids=lambda c: f"{c['id']} {c['name']}")
@pytest.mark.api
@pytest.mark.auth
def test_logout_invalidates_session(base_url, api_session, admin_login, case):
    """前置：登出当前会话；断言：原 access / 原 refresh 均被拒。"""
    session, tokens = admin_login
    logout = session.post(f"{base_url}/api/auth/logout/")
    assert logout.status_code == 200, f"前置登出失败: {logout.status_code} {logout.text}"

    # 「登出后再刷新」不需要带令牌；「登出后再读 me」必须带（且已被吊销）原 access
    request_session = session if case.get("auth", "required") == "required" else api_session
    execute_case(
        base_url,
        request_session,
        case,
        {
            "admin_access_token": tokens["access_token"],
            "admin_refresh_token": tokens["refresh_token"],
        },
    )
