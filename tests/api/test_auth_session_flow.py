"""会话生命周期流程用例 — 登出后 access 与 refresh 同时失效。

这组用例在 YAML 里带 `setup: logout`：loader 是单请求模型，前置步骤由本驱动完成 ——
先以现场登录的 session 调一次登出，再用**同一份凭证**断言后续请求被拒。
期望值（状态码 / schema / 文案）仍写在 YAML 里，与其它 32 条用例同源。

用例源：tests/api/case/{logout,refresh,me}.yaml
"""

import pytest

from tests.api.loader import execute_case, load_cases

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
