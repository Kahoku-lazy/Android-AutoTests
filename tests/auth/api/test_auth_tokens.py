import pytest

from tests.api_kit.loader import execute_case, load_cases

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
    _, tokens = admin_login
    execute_case(base_url, api_session, case, _token_ctx(tokens))


@pytest.mark.parametrize("case", AUTH_CASES, ids=lambda c: f"{c['id']} {c['name']}")
@pytest.mark.api
@pytest.mark.auth
def test_auth_tokens_authenticated(base_url, admin_login, case):
    session, tokens = admin_login
    execute_case(base_url, session, case, _token_ctx(tokens))
