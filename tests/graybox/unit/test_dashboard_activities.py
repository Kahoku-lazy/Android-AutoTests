"""仪表盘活动时间线：任务卡 + 智能体合并、limit/offset 分页。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from apps.ai_assistant.models import AIAgent, AITask
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

User = get_user_model()
ACTIVITIES_URL = "/api/dashboard/activities/"


def _auth_headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


@pytest.fixture
def visible_agent(db):
    user = User.objects.create_user(
        username="dash-act-admin",
        password="x",
        is_superuser=True,
    )
    agent = AIAgent.objects.create(
        name="dash-act-agent",
        owner=user,
        model_provider="deepseek",
        model_name="deepseek-v4",
    )
    return user, agent


@pytest.mark.unit
def test_default_returns_at_most_ten(client, visible_agent):
    user, agent = visible_agent
    for i in range(12):
        AITask.objects.create(agent=agent, title=f"t-{i}", status="success")

    resp = client.get(ACTIVITIES_URL, **_auth_headers(user))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    assert isinstance(body["data"], list)
    assert len(body["data"]) <= 10


@pytest.mark.unit
def test_offset_skips_board_page(client, visible_agent):
    user, agent = visible_agent
    for i in range(15):
        AITask.objects.create(agent=agent, title=f"page-{i}", status="completed")

    first = client.get(ACTIVITIES_URL, **_auth_headers(user)).json()["data"]
    second = client.get(
        ACTIVITIES_URL, {"offset": 10, "limit": 50}, **_auth_headers(user)
    ).json()["data"]

    assert len(first) == 10
    assert isinstance(second, list)
    first_actions = {row["action"] for row in first}
    second_actions = {row["action"] for row in second}
    assert first_actions.isdisjoint(second_actions)


@pytest.mark.unit
def test_invalid_limit_rejected(client, visible_agent):
    user, _agent = visible_agent
    headers = _auth_headers(user)

    for bad in ("0", "51", "abc"):
        resp = client.get(ACTIVITIES_URL, {"limit": bad}, **headers)
        assert resp.status_code == 400
        body = resp.json()
        assert body.get("message") or (isinstance(body.get("data"), dict) and body["data"].get("message"))


@pytest.mark.unit
def test_task_maps_to_run_and_agent_maps_to_agent(client, visible_agent):
    user, agent = visible_agent
    AITask.objects.create(agent=agent, title="校准色温", status="success")

    rows = client.get(ACTIVITIES_URL, **_auth_headers(user)).json()["data"]
    types = {r["type"] for r in rows}
    assert "run" in types
    assert "agent" in types

    run_row = next(r for r in rows if r["type"] == "run")
    assert "校准色温" in run_row["action"]

    agent_row = next(r for r in rows if r["type"] == "agent")
    assert "dash-act-agent" in agent_row["action"]
