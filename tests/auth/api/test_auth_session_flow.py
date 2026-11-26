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
    session, tokens = admin_login
    logout = session.post(f"{base_url}/api/auth/logout/")
    assert logout.status_code == 200, f"前置登出失败: {logout.status_code} {logout.text}"

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
