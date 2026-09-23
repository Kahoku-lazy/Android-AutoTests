"""仪表盘 stats：cases.breakdown 按项目维度返回。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model

from apps.case_manager import api as case_api
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

User = get_user_model()
STATS_URL = "/api/dashboard/stats/"


def _auth_headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


@pytest.fixture
def two_users(db):
    owner = User.objects.create_user(username="dash-case-owner", password="x")
    other = User.objects.create_user(username="dash-case-other", password="x")
    return owner, other


@pytest.mark.unit
def test_breakdown_is_per_project_for_current_user(client, two_users):
    owner, other = two_users
    uid = str(owner.id)

    p_with = case_api.create_project(name="有用例项目", user_id=uid)
    p_empty = case_api.create_project(name="空项目", user_id=uid)
    f = case_api.create_file(project_id=p_with["id"], name="表", user_id=uid)
    case_api.create_definition(
        project_id=p_with["id"],
        file_id=f["id"],
        user_id=uid,
        title="用例1",
        steps="步骤",
        expected_result="预期",
    )
    case_api.create_definition(
        project_id=p_with["id"],
        file_id=f["id"],
        user_id=uid,
        title="用例2",
        steps="步骤",
        expected_result="预期",
    )
    # 他用户项目不得出现在当前用户 breakdown
    case_api.create_project(name="别人的项目", user_id=str(other.id))

    resp = client.get(STATS_URL, **_auth_headers(owner))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    cases = body["data"]["cases"]
    breakdown = cases["breakdown"]

    assert len(breakdown) == 2
    by_id = {row["project_id"]: row for row in breakdown}
    assert set(by_id) == {p_with["id"], p_empty["id"]}
    assert by_id[p_with["id"]]["name"] == "有用例项目"
    assert by_id[p_with["id"]]["total"] == 2
    assert by_id[p_empty["id"]]["name"] == "空项目"
    assert by_id[p_empty["id"]]["total"] == 0
    assert cases["total"] == sum(row["total"] for row in breakdown)
    assert cases["total"] == 2
    for row in breakdown:
        assert "type" not in row
