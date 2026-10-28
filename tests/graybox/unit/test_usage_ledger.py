"""模型用量账本单测：价目、写入幂等与分类汇总。"""

from __future__ import annotations

from decimal import Decimal

import pytest

from django.utils import timezone

from backend.apps.usage_ledger.api import record_usage, record_voice_event, usage_summary
from backend.apps.usage_ledger.models import ModelUsage
from backend.apps.usage_ledger.pricing import category_of, price_usage

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def test_deepseek_price_uses_billing_rates():
    """DeepSeek 走现有计费口径。"""
    priced = price_usage(
        "deepseek",
        "deepseek-flash",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
    )

    assert priced["category"] == "LLM"
    assert priced["pricing_status"] == "priced"
    assert priced["cost_total"] > Decimal("0")


def test_tts_price_uses_characters():
    """Sambert 按字符计价，不按 token。"""
    priced = price_usage(
        "dashscope",
        "sambert-zhichu-v1",
        characters=10_000,
    )

    assert priced["category"] == "TTS"
    assert priced["cost_total"] == Decimal("1.00000000")


def test_unknown_model_is_unpriced():
    """未收录模型不伪造金额。"""
    priced = price_usage("dashscope", "unknown-model", input_tokens=100)

    assert priced["pricing_status"] == "unpriced"
    assert priced["cost_total"] == 0


def test_category_labels():
    """分类标签覆盖 LLM / TTS / Realtime / Embedding / ASR。"""
    assert category_of("deepseek-flash") == "LLM"
    assert category_of("sambert-zhichu-v1") == "TTS"
    assert category_of("qwen3.5-omni-plus-realtime") == "Realtime"
    assert category_of("text-embedding-v4") == "Embedding"
    assert category_of("qwen3-asr-flash-realtime") == "ASR"


def test_record_usage_is_idempotent():
    """同一 event_id 重写不新增行。"""
    fields = {
        "event_id": "task:1:1",
        "provider": "deepseek",
        "model": "deepseek-flash",
        "occurred_at": timezone.now(),
        "input_tokens": 100,
        "output_tokens": 10,
        "category": "LLM",
        "source": "task",
    }

    first = record_usage(**fields)
    second = record_usage(**fields)

    assert first is not None and second is not None
    assert first.usage_id == second.usage_id
    assert ModelUsage.objects.filter(event_id="task:1:1").count() == 1


def test_voice_event_writes_uuid_and_summary():
    """语音事件写账本，汇总按分类返回。"""
    record_voice_event(
        {
            "event": "model_usage",
            "provider": "deepseek",
            "category": "LLM",
            "model": "deepseek-flash",
            "reply_id": "resp_1",
            "input_tokens": 50,
            "output_tokens": 5,
        },
        "session-1",
        "user-1",
    )

    record_usage(
        event_id="task:1:1",
        provider="deepseek",
        model="deepseek-flash",
        occurred_at=timezone.now(),
        input_tokens=10,
        output_tokens=1,
        category="LLM",
        source="task",
    )

    summary = usage_summary("today")
    voice_summary = usage_summary("today", source="voice")

    assert summary["total"]["calls"] == 2
    assert summary["categories"][0]["category"] == "LLM"
    assert voice_summary["total"]["calls"] == 1
    record = ModelUsage.objects.get(source="voice")
    assert len(str(record.usage_id)) == 36
    assert record.usage_id.hex in record.event_id
