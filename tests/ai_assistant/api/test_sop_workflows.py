from __future__ import annotations

from uuid import uuid4

import pytest

from django.contrib.auth import get_user_model
from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.api import grant_assistant_author
from backend.apps.ai_assistant.models import AIAssistant, AIModelConfig, AIRole, AISopWorkflow
from backend.apps.ai_assistant.views_drf import SopWorkflowDetailView, SopWorkflowView

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def _card(assistant_id: str, display_name: str) -> AIAssistant:
    config, _ = AIModelConfig.objects.get_or_create(
        api_key_env="DEEPSEEK_API_KEY",
        model_name="deepseek-flash",
        defaults={"provider": "deepseek"},
    )
    role = AIRole.objects.create(
        role_id=f"20261117{assistant_id[-3:]}",
        name=f"配置{assistant_id[-3:]}",
        model_config=config,
    )
    return AIAssistant.objects.create(
        assistant_id=assistant_id,
        display_name=display_name,
        marker="teal",
        role_id=role.role_id,
        tools=[],
    )


def _call(method: str, workflow_id: int | None = None, data: dict | None = None, *, author=True):
    user = get_user_model().objects.create_user(username=f"wf-{uuid4().hex[:8]}", password="pass")
    if author:
        grant_assistant_author(user.id)
    factory = APIRequestFactory()
    path = (
        "/api/ai/sop-workflows/" if workflow_id is None else f"/api/ai/sop-workflows/{workflow_id}/"
    )
    request = getattr(factory, method)(path, data or {}, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    if workflow_id is None:
        return SopWorkflowView.as_view()(request)
    return SopWorkflowDetailView.as_view()(request, workflow_id=workflow_id)


def test_plain_user_cannot_create_patch_or_delete():
    card = _card("20261117_PD1", "留着")
    workflow = AISopWorkflow.objects.create(
        name="原样",
        executor_assistant_id=card.assistant_id,
        verifier_assistant_id=card.assistant_id,
    )
    payload = {
        "name": "不该写成",
        "executor_assistant_id": card.assistant_id,
        "verifier_assistant_id": card.assistant_id,
    }

    created = _call("post", data=payload, author=False)
    patched = _call("patch", workflow.id, payload, author=False)
    deleted = _call("delete", workflow.id, author=False)

    assert created.status_code == 403
    assert patched.status_code == 403
    assert deleted.status_code == 403
    stored = AISopWorkflow.objects.get(pk=workflow.pk)
    assert stored.name == "原样"
    assert AISopWorkflow.objects.count() == 1


def test_routes_resolve():
    assert resolve("/api/ai/sop-workflows/").func.cls is SopWorkflowView
    assert resolve("/api/ai/sop-workflows/7/").func.cls is SopWorkflowDetailView


def test_patch_rewrites_name_and_bindings():
    executor = _card("20261117_PA1", "执行甲")
    verifier = _card("20261117_PA2", "验收甲")
    replacement = _card("20261117_PA3", "执行乙")
    workflow = AISopWorkflow.objects.create(
        name="旧名字",
        executor_assistant_id=executor.assistant_id,
        verifier_assistant_id=verifier.assistant_id,
    )

    response = _call(
        "patch",
        workflow.id,
        {
            "name": "新名字",
            "executor_assistant_id": replacement.assistant_id,
            "verifier_assistant_id": verifier.assistant_id,
        },
    )

    assert response.status_code == 200
    stored = AISopWorkflow.objects.get(pk=workflow.pk)
    assert stored.name == "新名字"
    assert stored.executor_assistant_id == replacement.assistant_id
    assert stored.verifier_assistant_id == verifier.assistant_id


def test_patch_missing_card_returns_readable_400():
    executor = _card("20261117_PB1", "执行丙")
    verifier = _card("20261117_PB2", "验收丙")
    workflow = AISopWorkflow.objects.create(
        name="原名字",
        executor_assistant_id=executor.assistant_id,
        verifier_assistant_id=verifier.assistant_id,
    )

    response = _call(
        "patch",
        workflow.id,
        {
            "name": "改坏的名字",
            "executor_assistant_id": executor.assistant_id,
            "verifier_assistant_id": "20261117_NO1",
        },
    )

    assert response.status_code == 400
    assert "验收助手" in str(response.data)
    stored = AISopWorkflow.objects.get(pk=workflow.pk)
    assert stored.name == "原名字"
    assert stored.verifier_assistant_id == verifier.assistant_id


def test_patch_unknown_workflow_returns_404():
    response = _call(
        "patch",
        9999,
        {
            "name": "随便",
            "executor_assistant_id": "20261117_XX1",
            "verifier_assistant_id": "20261117_XX2",
        },
    )

    assert response.status_code == 404
    assert "工作流不存在" in str(response.data)


def test_delete_removes_only_workflow():
    card = _card("20261117_PC1", "留着")
    workflow = AISopWorkflow.objects.create(
        name="待删",
        executor_assistant_id=card.assistant_id,
        verifier_assistant_id=card.assistant_id,
    )

    response = _call("delete", workflow.id)

    assert response.status_code == 200
    assert not AISopWorkflow.objects.filter(pk=workflow.pk).exists()
    assert AIAssistant.objects.filter(pk=card.pk).exists()


def test_editing_published_workflow_returns_to_draft_and_republishes():
    from backend.apps.ai_assistant.api import publish_workflow

    executor = _card("20261117_ED1", "编辑执行")
    verifier = _card("20261117_ED2", "编辑验收")
    for card in (executor, verifier):
        card.release_state = "published"
        card.save(update_fields=["release_state"])
    workflow = AISopWorkflow.objects.create(
        name="可编辑",
        executor_assistant_id=executor.assistant_id,
        verifier_assistant_id=verifier.assistant_id,
        orchestration="sop",
        kind="ui_automation",
    )
    first = publish_workflow(workflow)
    workflow.refresh_from_db()
    assert workflow.release_state == "published"

    patched = _call(
        "patch",
        workflow.id,
        {
            "name": "可编辑",
            "executor_assistant_id": verifier.assistant_id,
            "verifier_assistant_id": executor.assistant_id,
        },
    )

    assert patched.status_code == 200
    workflow.refresh_from_db()
    assert workflow.release_state == "draft"
    second = publish_workflow(workflow)
    assert second.version == first.version + 1


def test_team_publish_requires_published_members():
    from backend.apps.ai_assistant.views_drf import WorkflowPublishView

    leader = _card("20261117_TL1", "队长")
    member = _card("20261117_TM1", "成员甲")
    other = _card("20261117_TM2", "成员乙")
    for card in (leader, other):
        card.release_state = "published"
        card.save(update_fields=["release_state"])
    workflow = AISopWorkflow.objects.create(
        name="团队流程",
        orchestration="team",
        kind="requirement_breakdown",
        leader_assistant_id=leader.assistant_id,
        members=[
            {"assistant_id": member.assistant_id, "description": "拆需求"},
            {"assistant_id": other.assistant_id, "description": "写用例"},
        ],
    )
    user = get_user_model().objects.create_user(username="wf-team-publish", password="pass")
    grant_assistant_author(user.id)

    def _publish():
        factory = APIRequestFactory()
        request = factory.post(f"/api/ai/sop-workflows/{workflow.id}/publish/")
        request.user_id = str(user.id)
        force_authenticate(request, user=user)
        return WorkflowPublishView.as_view()(request, workflow_id=workflow.id)

    blocked = _publish()
    assert blocked.status_code == 400
    assert "队长与成员" in str(blocked.data)

    member.release_state = "published"
    member.save(update_fields=["release_state"])
    allowed = _publish()
    assert allowed.status_code == 200
    assert allowed.data["version"] == 1
