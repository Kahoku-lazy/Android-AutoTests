"""认证 E2E 专用 fixtures。"""

from __future__ import annotations

import time
import uuid

import pytest
import requests

from tests.auth.conftest import REGISTER_URL

# 共享 fixtures 经 pytest_plugins 加载，声明已移至根 conftest.py（pytest ≥ 8.1 禁止在非顶层 conftest 声明）


@pytest.fixture
def second_user(base_url: str, e2e_services) -> dict[str, str]:
    """API 预注册临时用户，供多账号场景。删不掉也不阻断。"""
    _ = e2e_services
    username = f"E2E-{int(time.time())}-{uuid.uuid4().hex[:4]}"
    password = "E2ePass123"
    email = f"{username}@example.com"
    resp = requests.post(
        f"{base_url}{REGISTER_URL}",
        json={
            "username": username,
            "password": password,
            "password2": password,
            "email": email,
        },
        timeout=15,
    )
    body = resp.json() if resp.content else {}
    assert resp.status_code == 200 and body.get("status") is True, (
        f"预注册失败: {resp.status_code} {body}"
    )
    yield {"username": username, "password": password, "email": email}
