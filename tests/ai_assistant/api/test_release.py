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
    AssistantEvalScore,
    AssistantEvalScoreItem,
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


def _publish(user, assistant_id: str):
    factory = APIRequestFactory()
    request = factory.post(f"/api/ai/assistants/{assistant_id}/publish/", {}, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return AssistantPublishView.as_view()(request, assistant_id=assistant_id)


def _score(card: AIAssistant, value: str = "0.200") -> AssistantEvalScore:
    run = AssistantEvalScore.objects.create(
        target_kind="assistant",
        target_id=card.assistant_id,
        prompt_fingerprint="ignored",
        judge_model="deepseek-chat",
    )
    AssistantEvalScoreItem.objects.create(
        run=run,
        metric_key="prompt_quality",
        score=value,
        reason="分数很低",
        threshold="0.500",
    )
    return run


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

    published = _publish(author, assistant_id)

    role.system_prompt = "改过的提示词"
    role.save(update_fields=["system_prompt"])

    assert published.status_code == 200
    again = _publish(author, assistant_id)
    assert again.status_code == 400
    assert published.data["has_secret"] is False
    stored = AssistantRelease.objects.get(
        target_kind="assistant", target_id=assistant_id, version=1
    )
    assert stored.payload["system_prompt"] == "发布时的提示词"
    assert AIAssistant.objects.get(assistant_id=assistant_id).release_state == "published"


def test_low_score_does_not_block_publish():
    role = _role()
    author = _user("release-author-low", author=True)
    created = _call(
        author, "post", {"display_name": "低分也能发", "role_id": role.role_id, "tools": []}
    )
    assistant_id = created.data["assistant_id"]
    card = AIAssistant.objects.get(assistant_id=assistant_id)
    _score(card)

    published = _publish(author, assistant_id)

    assert published.status_code == 200
    assert published.data["version"] == 1


def test_never_scored_publish_is_allowed():
    role = _role()
    author = _user("release-author-none", author=True)
    created = _call(
        author, "post", {"display_name": "没评过也能发", "role_id": role.role_id, "tools": []}
    )
    assistant_id = created.data["assistant_id"]

    published = _publish(author, assistant_id)

    assert published.status_code == 200
    assert AssistantEvalScore.objects.count() == 0


def test_workflow_publish_does_not_require_scores():
    role = _role()
    author = _user("release-author-flow", author=True)
    created = _call(author, "post", {"display_name": "流程", "role_id": role.role_id, "tools": []})
    assistant_id = created.data["assistant_id"]
    card = AIAssistant.objects.get(assistant_id=assistant_id)
    card.release_state = "published"
    card.save(update_fields=["release_state"])
    workflow = AISopWorkflow.objects.create(
        name="发布流程",
        executor_assistant_id=assistant_id,
        verifier_assistant_id=assistant_id,
        orchestration="sop",
    )
    factory = APIRequestFactory()
    request = factory.post(f"/api/ai/sop-workflows/{workflow.id}/publish/", {}, format="json")
    request.user_id = str(author.id)
    force_authenticate(request, user=author)

    response = WorkflowPublishView.as_view()(request, workflow_id=workflow.id)

    assert response.status_code == 200
    assert response.data["version"] == 1


def test_publish_requires_existing_agent_config():
    role = _role()
    author = _user("release-author-norole", author=True)
    created = _call(
        author, "post", {"display_name": "没配置", "role_id": role.role_id, "tools": []}
    )
    assistant_id = created.data["assistant_id"]
    role.delete()

    published = _publish(author, assistant_id)

    assert published.status_code == 400
    assert "Agent 配置" in str(published.data)
    assert not AssistantRelease.objects.filter(
        target_kind="assistant", target_id=assistant_id
    ).exists()


def test_workflow_run_name_follows_rename_but_version_keeps_history():
    from backend.apps.ai_assistant import api as assistant_api

    role = _role()
    executor = AIAssistant.objects.create(
        assistant_id="20261118EX1",
        display_name="旧执行名",
        marker="teal",
        role_id=role.role_id,
        tools=[],
        release_state="published",
    )
    verifier = AIAssistant.objects.create(
        assistant_id="20261118VE1",
        display_name="验收名",
        marker="ink",
        role_id=role.role_id,
        tools=[],
        release_state="published",
    )
    workflow = AISopWorkflow.objects.create(
        name="改名流程",
        executor_assistant_id=executor.assistant_id,
        verifier_assistant_id=verifier.assistant_id,
        orchestration="sop",
        kind="ui_automation",
    )

    release = assistant_api.publish_workflow(workflow)
    assert release.payload["executor"]["run_name"] == "旧执行名"

    executor.display_name = "新执行名"
    executor.save(update_fields=["display_name"])

    resolved = assistant_api.resolve_sop_release(workflow.id, release.version)
    assert resolved["executor"]["run_name"] == "新执行名"
    release.refresh_from_db()
    assert release.payload["executor"]["run_name"] == "旧执行名"


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
        {"tools": [{"domain": "adb", "preset": "all"}], "revision": card.revision},
        assistant_id=card.assistant_id,
    )
    card.refresh_from_db()
    assert changed.status_code == 200
    assert card.release_state == "draft"
