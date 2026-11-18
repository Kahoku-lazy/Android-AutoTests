"""嵌入用量入账单测：逐调用一条、幂等、零 token 跳过、写失败不抛。"""

from __future__ import annotations

import pytest

from backend.apps.usage_ledger.api import record_embedding_usages
from backend.apps.usage_ledger.models import ModelUsage

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _event(tokens: int = 12, **extra) -> dict:
    """造一条知识库用量事件字典。

    Args:
        tokens: token 数。
        **extra: 覆盖字段。

    Returns:
        事件字典。
    """
    event = {
        "model": "text-embedding-v4",
        "api_key_env": "DASHSCOPE_API_KEY",
        "tokens": tokens,
        "time": 0.25,
        "phase": "retrieve",
        "base": "product_manuals",
        "occurred_at": "2026-11-18T10:00:00.000",
    }
    event.update(extra)
    return event


def test_each_call_gets_one_embedding_row():
    """每次嵌入调用各记一条 Embedding，token 与事件一致。"""
    written = record_embedding_usages(
        [_event(12, phase="index"), _event(7)],
        execution_id="exec-1",
    )
    assert written == 2
    rows = ModelUsage.objects.filter(source="knowledge", execution_id="exec-1")
    assert rows.count() == 2
    assert all(row.category == "Embedding" for row in rows)
    assert all(row.provider == "dashscope" for row in rows)
    assert sorted(row.input_tokens for row in rows) == [7, 12]
    assert all(row.output_tokens == 0 for row in rows)


def test_resubmit_does_not_double():
    """同一批事件重复提交不翻倍，token 以后一次为准。"""
    events = [_event(12)]
    record_embedding_usages(events, execution_id="exec-2")
    record_embedding_usages([_event(20)], execution_id="exec-2")
    rows = ModelUsage.objects.filter(source="knowledge", execution_id="exec-2")
    assert rows.count() == 1
    assert rows.first().input_tokens == 20


def test_zero_tokens_skipped():
    """零 token 与非法条目不入账。"""
    written = record_embedding_usages(
        [_event(0), _event(-3), "not-a-dict", _event(5)],
        execution_id="exec-3",
    )
    assert written == 1
    assert ModelUsage.objects.filter(execution_id="exec-3").count() == 1


def test_write_failure_does_not_raise(monkeypatch):
    """单条写失败只记日志，不向上抛，也不影响其它条。"""
    import backend.apps.usage_ledger.api as ledger_api

    real_record = ledger_api.record_usage
    calls = {"n": 0}

    def flaky_record(**kwargs):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("账本暂时不可写")
        return real_record(**kwargs)

    monkeypatch.setattr(ledger_api, "record_usage", flaky_record)
    written = record_embedding_usages([_event(1), _event(2)], execution_id="exec-4")
    assert written == 1
    assert ModelUsage.objects.filter(execution_id="exec-4").count() == 1


def test_eval_source_is_separate():
    """评测来源写 knowledge_eval，与检索来源互不串键。"""
    record_embedding_usages([_event(9)], execution_id="run-1", source="knowledge_eval")
    row = ModelUsage.objects.get(execution_id="run-1")
    assert row.source == "knowledge_eval"
    assert row.event_id == "knowledge_eval:run-1:1"
