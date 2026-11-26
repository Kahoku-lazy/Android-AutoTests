from __future__ import annotations

import json

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.api import grant_assistant_author
from backend.apps.ai_assistant.models import (
    AIAssistant,
    AIModelConfig,
    AIRole,
    AssistantEvalScore,
)
from backend.apps.ai_assistant.services import eval_scores
from backend.apps.ai_assistant.views_drf import EvalScoreView

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def _card(prompt: str = "你是执行者。") -> AIAssistant:
    config = AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name="deepseek-flash",
    )
    role = AIRole.objects.create(
        role_id="20261125sc1",
        name="评分配置",
        model_config=config,
        system_prompt=prompt,
    )
    return AIAssistant.objects.create(
        assistant_id="20261125_SC1",
        display_name="评分助手",
        marker="teal",
        role_id=role.role_id,
        tools=[],
    )


def _author(name: str):
    user = get_user_model().objects.create_user(username=name, password="pass")
    grant_assistant_author(user.id)
    return user


def _fake_judge(monkeypatch) -> None:
    def _run_single(**kwargs):
        scores = [
            {
                "metric_key": "prompt_quality",
                "score": 0.75,
                "reason": f"评了 {len(kwargs['prompt_body'])} 字",
            }
        ]
        if str(kwargs.get("handover_body") or "").strip():
            scores.append(
                {
                    "metric_key": "handover_quality",
                    "score": 0.75,
                    "reason": f"评了 {len(kwargs['handover_body'])} 字",
                }
            )
        return {
            "scores": scores,
            "dashboard_html": "",
            "test_run_json": "",
            "judge_model": "deepseek-chat",
            "judge_usage": [{"model": "deepseek-chat", "input_tokens": 10, "output_tokens": 2}],
        }

    monkeypatch.setattr(eval_scores, "run_single", _run_single)
    monkeypatch.setattr(eval_scores, "_bill", lambda usages, run_id: None)


def _post(user, payload: dict):
    factory = APIRequestFactory()
    request = factory.post("/api/ai/eval-scores/", payload, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return EvalScoreView.as_view()(request)


def _get(user, params: str):
    factory = APIRequestFactory()
    request = factory.get(f"/api/ai/eval-scores/?{params}")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return EvalScoreView.as_view()(request)


def test_author_gets_scores_and_history(monkeypatch, tmp_path):
    _fake_judge(monkeypatch)
    card = _card()
    run_file = tmp_path / "20261125_120000_x.aligned.json"
    run_file.write_text(
        json.dumps(
            {
                "input": {"user_message": "打开设置"},
                "summary": {"final_text": "已停在设置页", "phase": "completed"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )
    monkeypatch.setattr(
        eval_scores, "_runs", lambda kind, target_id, limit=30: [(1.0, "task:r1:f", run_file)]
    )
    author = _author("score-author")

    first = _post(author, {"kind": "assistant", "target_id": card.assistant_id})
    second = _post(author, {"kind": "assistant", "target_id": card.assistant_id})

    assert first.status_code == 200
    assert second.status_code == 200
    detail = first.data["score"]
    keys = sorted(item["metric_key"] for item in detail["items"])
    assert keys == ["handover_quality", "prompt_quality"]
    assert detail["judge_model"]
    assert AssistantEvalScore.objects.count() == 2

    listed = _get(author, f"kind=assistant&target_id={card.assistant_id}")
    assert listed.status_code == 200
    rows = listed.data["scores"]
    assert len(rows) == 2
    assert rows[0]["id"] > rows[1]["id"]
    assert len(rows[0]["items"]) == 2


def test_missing_handover_is_reported_not_invented(monkeypatch):
    _fake_judge(monkeypatch)
    card = _card()
    monkeypatch.setattr(eval_scores, "_runs", lambda kind, target_id, limit=30: [])
    author = _author("score-author-2")

    response = _post(author, {"kind": "assistant", "target_id": card.assistant_id})

    assert response.status_code == 200
    detail = response.data["score"]
    assert [item["metric_key"] for item in detail["items"]] == ["prompt_quality"]
    assert detail["missing"][0]["metric_key"] == "handover_quality"
    assert "没有可用的运行产物" in detail["missing"][0]["reason"]


def test_blank_prompt_is_rejected(monkeypatch):
    _fake_judge(monkeypatch)
    card = _card(prompt="   ")
    author = _author("score-author-3")

    response = _post(author, {"kind": "assistant", "target_id": card.assistant_id})

    assert response.status_code == 400
    assert AssistantEvalScore.objects.count() == 0


def test_unknown_target_returns_404(monkeypatch):
    _fake_judge(monkeypatch)
    author = _author("score-author-4")

    response = _post(author, {"kind": "assistant", "target_id": "20260101_XX"})

    assert response.status_code == 404
