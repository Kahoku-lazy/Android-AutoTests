import pytest

from tests.api_kit.loader import execute_case, load_cases

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
