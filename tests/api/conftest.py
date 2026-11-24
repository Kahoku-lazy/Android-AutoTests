import uuid

import pytest
import requests


@pytest.fixture(scope="function")
def api_session() -> requests.Session:
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture
def unique_username() -> str:
    return f"test_{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="function")
def admin_login(base_url) -> tuple[requests.Session, dict]:
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    resp = session.post(
        f"{base_url}/api/auth/login/", json={"username": "admin", "password": "admin123"}
    )
    assert resp.status_code == 200, f"登录失败: {resp.text}"
    data = resp.json()["data"]
    session.headers.update({"Authorization": f"Bearer {data['access_token']}"})
    return session, {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
    }


@pytest.fixture(scope="function")
def auth_session(admin_login) -> requests.Session:
    return admin_login[0]
