from __future__ import annotations

from pathlib import Path

import pytest

from django.contrib.auth import get_user_model
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.api import grant_assistant_author
from backend.apps.ai_assistant.models import AssistantEvalCase, AssistantEvalScore
from backend.apps.ai_assistant.views_drf import (
    EvalCaseDetailView,
    EvalCaseView,
    EvalMethodView,
    EvalReportView,
)

pytestmark = [pytest.mark.django_db, pytest.mark.api]


def _author(name: str):
    user = get_user_model().objects.create_user(username=name, password="pass")
    grant_assistant_author(user.id)
    return user


def _call(view, user, method: str, path: str, payload: dict | None = None, **kwargs):
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, payload or {}, format="json")
    request.user_id = str(user.id)
    force_authenticate(request, user=user)
    return view.as_view()(request, **kwargs)


def test_author_edits_case_bank_and_reads_methods():
    board_dir = Path("temps/eval_case_test")
    board_dir.mkdir(parents=True, exist_ok=True)
    author = _author("case-author")

    methods = _call(EvalMethodView, author, "get", "/api/ai/eval-methods/")
    assert methods.status_code == 200
    keys = sorted(item["key"] for item in methods.data["methods"])
    assert keys == ["case_suite", "handover_quality", "prompt_quality"]
    assert all(item["criteria"] for item in methods.data["methods"])

    created = _call(
        EvalCaseView,
        author,
        "post",
        "/api/ai/eval-cases/",
        {
            "title": "打开设置",
            "steps": [{"action": "点设置", "assertion": "进入设置页", "anchor": {"page": "桌面"}}],
        },
    )
    assert created.status_code == 200
    case_id = created.data["case"]["id"]
    assert AssistantEvalCase.objects.filter(pk=case_id, title="打开设置").exists()

    updated = _call(
        EvalCaseDetailView,
        author,
        "patch",
        f"/api/ai/eval-cases/{case_id}/",
        {"title": "打开 WLAN", "steps": [{"action": "点 WLAN", "assertion": "看到开关"}]},
        case_id=case_id,
    )
    assert updated.status_code == 200
    assert updated.data["case"]["title"] == "打开 WLAN"
    assert AssistantEvalCase.objects.get(pk=case_id).steps.count() == 1

    listed = _call(EvalCaseView, author, "get", "/api/ai/eval-cases/")
    assert [row["id"] for row in listed.data["cases"]] == [case_id]

    run = AssistantEvalScore.objects.create(
        target_kind="suite",
        target_id="assistant:1",
        report_html=str(board_dir / "board.html"),
    )
    (board_dir / "board.html").write_text("<html>提示词质量</html>", encoding="utf-8")
    report = _call(EvalReportView, author, "get", f"/api/ai/eval-reports/{run.pk}/", run_id=run.pk)
    assert report.status_code == 200
    assert b"html" in b"".join(report.streaming_content)

    deleted = _call(
        EvalCaseDetailView, author, "delete", f"/api/ai/eval-cases/{case_id}/", case_id=case_id
    )
    assert deleted.status_code == 200
    assert not AssistantEvalCase.objects.filter(pk=case_id).exists()
