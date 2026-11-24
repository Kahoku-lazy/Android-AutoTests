from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.api import grant_assistant_author
from backend.apps.ai_assistant.models import (
    AIAssistant,
    AIModelConfig,
    AIRole,
    AISopWorkflow,
    AssistantLiveRun,
    AssistantRelease,
)
from backend.apps.ai_assistant.views_drf import (
    AssistantPublishView,
    AssistantViewSet,
    WorkflowPublishView,
)

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def _role(prompt: str = "第一版提示词") -> AIRole:
    config = AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name=f"model-{prompt}",
    )
    return AIRole.objects.create(
        role_id="20261118abc",
        name="执行配置",
        model_config=config,
        system_prompt=prompt,
    )


def _user(name: str, *, author: bool = False):
    user = get_user_model().objects.create_user(username=name, password="pass")
    if author:
        grant_assistant_author(user.id)
    return user


def _call(user, method: str, data=None, *, assistant_id=None, action="list"):
    factory = APIRequestFactory()
    request = getattr(factory, method)("/api/ai/assistants/", data or {}, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    if assistant_id and method == "get":
        return AssistantViewSet.as_view({"get": "retrieve"})(request, assistant_id=assistant_id)
    if assistant_id and method == "patch":
        return AssistantViewSet.as_view({"patch": "partial_update"})(
            request, assistant_id=assistant_id
        )
    return AssistantViewSet.as_view({"get": action, "post": "create"})(request)


def test_plain_user_cannot_see_draft_author_can():
    role = _role()
    author = _user("release-author", author=True)
    plain = _user("release-plain")
    created = _call(
        author, "post", {"display_name": "草稿助手", "role_id": role.role_id, "tools": []}
    )
    assert created.status_code == 201
    assistant_id = created.data["assistant_id"]

    hidden = _call(plain, "get", assistant_id=assistant_id)
    visible = _call(author, "get")

    assert hidden.status_code == 404
    assert any(row["assistant_id"] == assistant_id for row in visible.data)


def test_publish_keeps_old_prompt_after_role_changes():
    role = _role("发布时的提示词")
    author = _user("release-author-2", author=True)
    created = _call(
        author, "post", {"display_name": "可发布", "role_id": role.role_id, "tools": []}
    )
    assistant_id = created.data["assistant_id"]
    factory = APIRequestFactory()
    request = factory.post(f"/api/ai/assistants/{assistant_id}/publish/", {}, format="json")
    request.user_id = str(author.id)
    force_authenticate(request, user=author)

    from backend.apps.ai_assistant.api import create_live_run, finish_live_run

    payload = {
        "role_id": role.role_id,
        "system_prompt": role.system_prompt,
        "tools": [],
        "model_config_id": role.model_config_id,
        "model_name": role.model_config.model_name,
        "provider": "deepseek",
        "api_key_env": "DEEPSEEK_API_KEY",
    }
    run = create_live_run("assistant", assistant_id, payload, ["A1", "S1", "S2", "S3"])
    finish_live_run(run.pk, status=AssistantLiveRun.STATUS_DONE, failures=[])
    published = AssistantPublishView.as_view()(request, assistant_id=assistant_id)
    role.system_prompt = "改过的提示词"
    role.save(update_fields=["system_prompt"])

    assert published.status_code == 200
    assert published.data["has_secret"] is False
    stored = AssistantRelease.objects.get(
        target_kind="assistant", target_id=assistant_id, version=1
    )
    assert stored.payload["system_prompt"] == "发布时的提示词"
    assert AIAssistant.objects.get(assistant_id=assistant_id).release_state == "published"


def test_runtime_edit_returns_to_draft_display_name_does_not():
    role = _role()
    author = _user("release-author-3", author=True)
    created = _call(author, "post", {"display_name": "名字", "role_id": role.role_id, "tools": []})
    card = AIAssistant.objects.get(assistant_id=created.data["assistant_id"])
    card.release_state = "published"
    card.save(update_fields=["release_state"])

    renamed = _call(
        author,
        "patch",
        {"display_name": "新名字", "revision": card.revision},
        assistant_id=card.assistant_id,
    )
    card.refresh_from_db()
    assert renamed.status_code == 200
    assert card.release_state == "published"

    changed = _call(
        author,
        "patch",
        {"tools": [{"domain": "adb", "include": []}], "revision": card.revision},
        assistant_id=card.assistant_id,
    )
    card.refresh_from_db()
    assert changed.status_code == 200
    assert card.release_state == "draft"


def test_publish_without_eval_is_rejected_even_for_superuser():
    role = _role("未测")
    root = get_user_model().objects.create_user(
        username="release-root",
        password="pass",
        is_superuser=True,
    )
    created = _call(root, "post", {"display_name": "未测", "role_id": role.role_id, "tools": []})
    factory = APIRequestFactory()
    request = factory.post("/publish/", {}, format="json")
    request.user_id = str(root.id)
    force_authenticate(request, user=root)

    response = AssistantPublishView.as_view()(request, assistant_id=created.data["assistant_id"])

    assert response.status_code == 400
    assert (
        AIAssistant.objects.get(assistant_id=created.data["assistant_id"]).release_state == "draft"
    )


def test_stale_revision_conflicts_and_keeps_content():
    role = _role()
    author = _user("release-author-4", author=True)
    created = _call(author, "post", {"display_name": "原名", "role_id": role.role_id, "tools": []})
    card = AIAssistant.objects.get(assistant_id=created.data["assistant_id"])

    response = _call(
        author,
        "patch",
        {"display_name": "后保存", "revision": card.revision - 1},
        assistant_id=card.assistant_id,
    )

    card.refresh_from_db()
    assert response.status_code == 409
    assert card.display_name == "原名"


def _publish_workflow(user, workflow_id: int):
    factory = APIRequestFactory()
    request = factory.post(f"/api/ai/sop-workflows/{workflow_id}/publish/", {}, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return WorkflowPublishView.as_view()(request, workflow_id=workflow_id)


def test_sop_publish_without_eval_is_rejected_goal_is_not():
    role = _role("流程")
    author = _user("release-flow", author=True)
    created = _call(
        author, "post", {"display_name": "流程助手", "role_id": role.role_id, "tools": []}
    )
    card = AIAssistant.objects.get(assistant_id=created.data["assistant_id"])
    card.release_state = "published"
    card.save(update_fields=["release_state"])
    sop = AISopWorkflow.objects.create(
        name="SOP",
        orchestration="sop",
        kind="ui_automation",
        executor_assistant_id=card.assistant_id,
        verifier_assistant_id=card.assistant_id,
    )
    goal = AISopWorkflow.objects.create(
        name="目标",
        orchestration="goal",
        kind="case_authoring",
        executor_assistant_id=card.assistant_id,
        verifier_assistant_id=card.assistant_id,
    )

    rejected = _publish_workflow(author, sop.id)
    accepted = _publish_workflow(author, goal.id)

    assert rejected.status_code == 400
    assert accepted.status_code == 200
