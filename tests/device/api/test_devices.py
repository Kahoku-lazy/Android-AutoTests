import pytest

from tests.api_kit.loader import execute_case, load_cases

CASES = load_cases("devices.yaml")

UNAUTH_CASES = [c for c in CASES if c.get("auth") == "none"]
AUTH_CASES = [c for c in CASES if c.get("auth", "required") == "required"]


@pytest.mark.parametrize("case", UNAUTH_CASES, ids=lambda c: f"{c['id']} {c['name']}")
@pytest.mark.api
@pytest.mark.device_pool
def test_devices_unauthenticated(base_url, api_session, case):
    execute_case(base_url, api_session, case, {})


@pytest.mark.parametrize("case", AUTH_CASES, ids=lambda c: f"{c['id']} {c['name']}")
@pytest.mark.api
@pytest.mark.device_pool
def test_devices_authenticated(base_url, auth_session, case):
    execute_case(base_url, auth_session, case, {})
