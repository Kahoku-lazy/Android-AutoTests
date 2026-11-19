"""评测入口：作者可选择助手或工作流，普通用户被拒绝。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.api import grant_assistant_author
from backend.apps.ai_assistant.models import AIAssistant, AIModelConfig, AIRole, AISopWorkflow
from backend.apps.ai_assistant.views_drf import EvalRunView, LiveEvalDetailView

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def _card() -> AIAssistant:
    config = AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name="deepseek-eval",
    )
    role = AIRole.objects.create(role_id="20261118ev1", name="评测配置", model_config=config)
    return AIAssistant.objects.create(
        assistant_id="20261118_EV1",
        display_name="评测助手",
        marker="teal",
        role_id=role.role_id,
        tools=[],
    )


def _call(user, payload: dict):
    factory = APIRequestFactory()
    request = factory.post("/api/ai/evals/run/", payload, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return EvalRunView.as_view()(request)


def test_author_can_evaluate_selected_assistant_and_workflow():
    author = get_user_model().objects.create_user(username="eval-author", password="pass")
    grant_assistant_author(author.id)
    card = _card()
    workflow = AISopWorkflow.objects.create(
        name="评测流程",
        executor_assistant_id=card.assistant_id,
        verifier_assistant_id=card.assistant_id,
    )

    assistant_result = _call(author, {"kind": "assistant", "target_id": card.assistant_id})
    workflow_result = _call(author, {"kind": "workflow", "target_id": workflow.id})

    assert assistant_result.status_code == 200
    assert assistant_result.data["id"]
    assert workflow_result.status_code == 200
    assert workflow_result.data["status"] == "pending"


def test_live_detail_hides_secrets_and_reports_progress():
    author = get_user_model().objects.create_user(username="eval-detail", password="pass")
    grant_assistant_author(author.id)
    plain = get_user_model().objects.create_user(username="eval-detail-plain", password="pass")
    from backend.apps.ai_assistant import api

    run = api.create_live_run("assistant", "20261118_EV1", {"api_key_env": "SECRET"}, ["A1"])
    api.append_live_sample(
        run.pk,
        "A1",
        "同栏",
        True,
        [],
        [{"role": "assistant", "text": "你好", "tool": "", "input": {}, "image": "secret-bytes"}],
    )

    factory = APIRequestFactory()
    denied = factory.get(f"/api/ai/evals/runs/{run.pk}/")
    denied.user_id = str(plain.id)
    force_authenticate(denied, user=plain)
    blocked = LiveEvalDetailView.as_view()(denied, run_id=run.pk)

    allowed = factory.get(f"/api/ai/evals/runs/{run.pk}/")
    allowed.user_id = str(author.id)
    force_authenticate(allowed, user=author)
    response = LiveEvalDetailView.as_view()(allowed, run_id=run.pk)

    assert blocked.status_code == 403
    assert response.status_code == 200
    assert response.data["progress_done"] == 1
    assert response.data["progress_total"] == 1
    body = str(response.data)
    assert "SECRET" not in body
    assert "secret-bytes" not in body
    assert response.data["samples"][0]["steps"][0]["text"] == "你好"


def test_goal_and_team_are_rejected_without_a_run():
    author = get_user_model().objects.create_user(username="eval-goal", password="pass")
    grant_assistant_author(author.id)
    card = _card()
    goal = AISopWorkflow.objects.create(
        name="目标",
        orchestration="goal",
        kind="case_authoring",
        executor_assistant_id=card.assistant_id,
        verifier_assistant_id=card.assistant_id,
    )

    response = _call(author, {"kind": "workflow", "target_id": goal.id})

    assert response.status_code == 400
    assert "不能评测" in str(response.data)
    from backend.apps.ai_assistant.models import AssistantLiveRun

    assert AssistantLiveRun.objects.filter(target_id=str(goal.id)).count() == 0


def test_plain_user_cannot_run_eval():
    plain = get_user_model().objects.create_user(username="eval-plain", password="pass")
    response = _call(plain, {"kind": "assistant", "target_id": "20261118_EV1"})
    assert response.status_code == 403
