"""evaluator 写库收敛回归：view / serializer 不再直写 ORM，写全部经 api.py。

覆盖：
1. `mark_eval_run_failed` —— 失败态只落 status + report_json（**不写** finished_at，与收敛前一致）；
2. `finish_external_eval_run` —— 终态落 status / 分数 / 题数 / 报告 / finished_at；
3. `QuestionBankSerializer` 的建 / 改都经 api（spy 断言），且更新时 `order` 按数组下标重排
   —— 与 legacy `POST /banks/{id}/update` 路径一致（API-评估器.md §6.5）。
"""

from __future__ import annotations

import json

import pytest

from apps.evaluator import api as evaluator_api
from apps.evaluator.models import EvalRun, QuestionBank
from apps.evaluator.serializers import QuestionBankSerializer

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def _bank_payload(name: str, questions: list[dict]) -> dict:
    return {"name": name, "description": "", "questions": questions}


def test_mark_eval_run_failed_sets_status_and_message():
    """失败态：落 status + report_json；finished_at 保持 None。"""
    run = EvalRun.objects.create(status="running")

    evaluator_api.mark_eval_run_failed(run.id, "Unknown framework: x")

    run.refresh_from_db()
    assert run.status == "failed"
    assert json.loads(run.report_json)["message"] == "Unknown framework: x"
    assert run.finished_at is None


def test_finish_external_eval_run_persists_terminal_state():
    """终态：分数 / 题数 / 报告 / finished_at 全部落库。"""
    run = EvalRun.objects.create(status="running")

    evaluator_api.finish_external_eval_run(
        run.id,
        status="completed",
        total_score=4.5,
        total_questions=3,
        completed_questions=2,
        report={"framework": "evalscope", "total_score": 4.5},
    )

    run.refresh_from_db()
    assert run.status == "completed"
    assert run.total_score == 4.5
    assert run.total_questions == 3
    assert run.completed_questions == 2
    assert json.loads(run.report_json)["framework"] == "evalscope"
    assert run.finished_at is not None


def test_serializer_create_routes_through_api(monkeypatch):
    """收敛断言：serializer 的写必须调 api，而不是自己 ORM 写。"""
    calls: list[dict] = []
    real_create = evaluator_api.create_question_bank

    def spy_create(**kwargs):
        calls.append(kwargs)
        return real_create(**kwargs)

    monkeypatch.setattr(evaluator_api, "create_question_bank", spy_create)

    serializer = QuestionBankSerializer(
        data=_bank_payload("试卷A", [{"content": "q1", "category": "c", "order": 5}])
    )
    assert serializer.is_valid(), serializer.errors
    bank = serializer.save()

    assert calls, "serializer.create 未调用 api.create_question_bank"
    assert calls[0]["name"] == "试卷A"
    assert isinstance(bank, QuestionBank)
    assert [q.content for q in bank.questions.all()] == ["q1"]
    assert [q.order for q in bank.questions.all()] == [5]


def test_serializer_update_routes_through_api_and_reorders_by_index(monkeypatch):
    """收敛断言 + 口径一致：更新走 api，且 order 按数组下标重排（同 legacy §6.5）。"""
    created = evaluator_api.create_question_bank(
        name="试卷B", description="", questions_data=[{"content": "old"}]
    )
    instance = QuestionBank.objects.get(id=created["id"])

    calls: list[tuple] = []
    real_update = evaluator_api.update_question_bank

    def spy_update(bank_id, data):
        calls.append((bank_id, data))
        return real_update(bank_id, data)

    monkeypatch.setattr(evaluator_api, "update_question_bank", spy_update)

    serializer = QuestionBankSerializer(
        instance,
        data=_bank_payload(
            "试卷B",
            [{"content": "first", "order": 9}, {"content": "second", "order": 7}],
        ),
    )
    assert serializer.is_valid(), serializer.errors
    updated = serializer.save()

    assert calls, "serializer.update 未调用 api.update_question_bank"
    questions = list(updated.questions.order_by("order", "id"))
    assert [q.content for q in questions] == ["first", "second"]
    # 客户端传的 9/7 被忽略：与 legacy 路径一致，按数组下标重排
    assert [q.order for q in questions] == [0, 1]
