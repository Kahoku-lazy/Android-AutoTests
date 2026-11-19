"""用例身份文案：空、里程碑、一条、多条共用同一口径。"""

from __future__ import annotations

import pytest

from backend.apps.task_list.case_identity import case_identity_label, case_identity_rows

pytestmark = [pytest.mark.unit]


def test_empty_identity_has_no_label():
    assert case_identity_label({}) == ""
    assert case_identity_label(None) == ""
    assert case_identity_rows({}) == []


def test_milestone_label_is_fixed_and_has_no_rows():
    identity = {"source": "milestone", "rows": []}
    assert case_identity_label(identity) == "里程碑"
    assert case_identity_rows(identity) == []


def test_one_row_uses_title_without_count():
    identity = {"source": "platform", "rows": [{"project": "灯", "id": "1", "title": "定时"}]}
    assert case_identity_label(identity) == "定时"


def test_many_rows_count_from_the_first_title():
    identity = {
        "source": "platform",
        "rows": [
            {"project": "灯", "id": "2", "title": "场景"},
            {"project": "灯", "id": "1", "title": "定时"},
        ],
    }
    assert case_identity_label(identity) == "场景 · 共 2 条"
    assert [row["title"] for row in case_identity_rows(identity)] == ["场景", "定时"]


@pytest.mark.django_db
def test_rerun_keeps_snapshot_after_case_rename():
    from django.contrib.auth import get_user_model

    from backend.apps.case_manager import api as case_api
    from backend.apps.task_list import api

    user = get_user_model().objects.create_user(username="rerun-case", password="x")
    project_id = case_api.create_project(
        name="灯", library_kind="automation", user_id=str(user.id)
    )["id"]
    row = case_api.create_row(
        project_id=project_id,
        user_id=str(user.id),
        title="定时",
        steps=[{"action": "点电源", "assertion": "灯亮"}],
    )
    original = api.create_task(
        title="工作流",
        goal="",
        case_identity={
            "source": "platform",
            "rows": [{"project": "灯", "id": row["id"], "title": "定时"}],
        },
        created_by=str(user.id),
    )
    case_api.update_row(
        project_id=project_id, case_id=row["id"], user_id=str(user.id), title="定时已改"
    )
    cloned = api.rerun_task(original)
    assert cloned.case_identity["rows"][0]["title"] == "定时"


@pytest.mark.django_db
def test_list_row_sends_case_label_without_rereading_library():
    from backend.apps.task_list import api

    task = api.create_task(
        title="工作流",
        goal="",
        case_identity={
            "source": "platform",
            "rows": [
                {"project": "灯", "id": "gone", "title": "定时"},
                {"project": "灯", "id": "also-gone", "title": "场景"},
            ],
        },
    )
    row = api.serialize_agent_task_row(task)
    assert row["title"] == "工作流"
    assert row["case_label"] == "定时 · 共 2 条"
    assert row["case_rows"][1]["title"] == "场景"


@pytest.mark.django_db
def test_one_label_reaches_task_bug_and_dashboard(monkeypatch):
    import json

    from django.contrib.auth import get_user_model
    from django.test import RequestFactory
    from rest_framework.test import force_authenticate

    from backend.apps.bug_manager import api as bug_api
    from backend.apps.bug_manager.models import BugTicket
    from backend.apps.case_manager import api as case_api
    from backend.apps.dashboard.ai_usage import ai_recent_tasks
    from backend.apps.task_list import api
    from backend.apps.task_list.models import Task
    from backend.apps.task_list.views import TaskSubmitAPIView

    user = get_user_model().objects.create_user(username="same-label", password="x")
    project_id = case_api.create_project(
        name="灯", library_kind="automation", user_id=str(user.id)
    )["id"]
    first = case_api.create_row(
        project_id=project_id,
        user_id=str(user.id),
        title="定时",
        steps=[{"action": "点", "assertion": "亮"}],
    )
    second = case_api.create_row(
        project_id=project_id,
        user_id=str(user.id),
        title="场景",
        steps=[{"action": "点", "assertion": "亮"}],
    )
    monkeypatch.setattr(
        "backend.apps.task_list.api.dispatch_device", lambda *_args, **_kwargs: None
    )
    monkeypatch.setattr(
        "backend.apps.ai_assistant.api.get_sop_workflow",
        lambda workflow_id: type("Workflow", (), {"id": workflow_id})(),
    )
    request = RequestFactory().post(
        "/api/tasks/submit/",
        data={
            "title": "工作流",
            "workflow_id": "7",
            "device_serial": "R5",
            "case_source": "platform",
            "case_ids": json.dumps([first["id"], second["id"]]),
        },
    )
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    response = TaskSubmitAPIView.as_view()(request)
    assert response.status_code == 200, response.data
    task = Task.objects.get(id=response.data["id"])
    task.status = "failed"
    task.result = json.dumps(
        {"failed_steps": [{"seq": 1, "name": "定时 · 第 1 步", "kind": "verdict"}]},
        ensure_ascii=False,
    )
    task.save()
    bug_api.record_task_bugs(task)

    row = api.serialize_agent_task_row(task)
    bug = BugTicket.objects.get(task_id=task.id)
    recent = ai_recent_tasks(str(user.id))[0]
    assert row["title"] == "工作流"
    assert bug.title.startswith("步骤未通过")
    assert row["case_label"] == bug.case_label == recent["case_label"] == "定时 · 共 2 条"


def test_blank_title_is_named():
    identity = {"source": "platform", "rows": [{"project": "", "id": "1", "title": "  "}]}
    assert case_identity_label(identity) == "未命名用例"
