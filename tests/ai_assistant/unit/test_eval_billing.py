"""评测用量：一条调用一条账，重复不翻倍，失败不中断。"""

from __future__ import annotations

from datetime import datetime

import pytest

from backend.apps.ai_assistant.services.eval_billing import record_eval_usages
from backend.apps.usage_ledger.models import ModelUsage

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def _event(round_key: str) -> dict:
    return {
        "round": round_key,
        "provider": "deepseek",
        "model": "deepseek-chat",
        "occurred_at": datetime(2026, 11, 18, 17, 0, 0),
        "input_tokens": 10,
        "output_tokens": 4,
    }


def test_one_call_one_record_and_repeat_updates():
    assert record_eval_usages([_event("1")], "run-1") == 1
    assert record_eval_usages([_event("1")], "run-1") == 1
    assert ModelUsage.objects.filter(execution_id="run-1", source="assistant_eval").count() == 1


def test_write_failure_does_not_stop_the_rest(monkeypatch):
    import backend.apps.usage_ledger.api as ledger_api

    real = ledger_api.record_usage
    calls = {"n": 0}

    def flaky(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("账本暂时不可写")
        return real(**kwargs)

    monkeypatch.setattr(ledger_api, "record_usage", flaky)
    written = record_eval_usages([_event("1"), _event("2")], "run-2")

    assert written == 1
    assert ModelUsage.objects.filter(execution_id="run-2").count() == 1
