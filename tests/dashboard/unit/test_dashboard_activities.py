"""仪表盘活动时间线：任务卡 + 智能体合并、limit/offset 分页。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from backend.apps.task_list.models import Task
from backend.models.constants import TaskKind
from backend.shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

User = get_user_model()
ACTIVITIES_URL = "/api/dashboard/activities/"


def _auth_headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


@pytest.fixture
def visible_user(db):
    return User.objects.create_user(
        username="dash-act-admin",
        password="x",
        is_superuser=True,
    )


@pytest.mark.unit
def test_default_returns_at_most_ten(client, visible_user):
    user = visible_user
    for i in range(12):
        Task.objects.create(title=f"t-{i}", status="success", task_kind=TaskKind.ASSISTANT_SOP)

    resp = client.get(ACTIVITIES_URL, **_auth_headers(user))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) <= 10


@pytest.mark.unit
def test_offset_skips_board_page(client, visible_user):
    user = visible_user
    for i in range(15):
        Task.objects.create(title=f"page-{i}", status="completed", task_kind=TaskKind.ASSISTANT_SOP)

    first = client.get(ACTIVITIES_URL, **_auth_headers(user)).json()["data"]
    second = client.get(ACTIVITIES_URL, {"offset": 10, "limit": 50}, **_auth_headers(user)).json()[
        "data"
    ]

    assert len(first) == 10
    assert isinstance(second, list)
    first_actions = {row["action"] for row in first}
    second_actions = {row["action"] for row in second}
    assert first_actions.isdisjoint(second_actions)


@pytest.mark.unit
def test_invalid_limit_rejected(client, visible_user):
    user = visible_user
    headers = _auth_headers(user)

    for bad in ("0", "51", "abc"):
        resp = client.get(ACTIVITIES_URL, {"limit": bad}, **headers)
        assert resp.status_code == 400
        body = resp.json()
        assert body.get("message") or (
            isinstance(body.get("data"), dict) and body["data"].get("message")
        )


@pytest.mark.unit
def test_task_maps_to_run(client, visible_user):
    user = visible_user
    Task.objects.create(title="校准色温", status="success", task_kind=TaskKind.ASSISTANT_SOP)
    Task.objects.create(title="退役任务", status="success", task_kind=TaskKind.DEVICE_CONTROL)

    rows = client.get(ACTIVITIES_URL, **_auth_headers(user)).json()["data"]
    run_row = next(r for r in rows if r["type"] == "run")
    assert "校准色温" in run_row["action"]
    assert not any(r["type"] == "agent" for r in rows)
    assert not any("退役任务" in r["action"] for r in rows)
