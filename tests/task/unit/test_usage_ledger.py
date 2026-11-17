"""模型用量账本单测：价目、写入幂等与分类汇总。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from django.utils import timezone

from backend.apps.usage_ledger.api import (
    recalculate_usage_costs,
    record_usage,
    record_voice_event,
    usage_dashboard,
    usage_summary,
)
from backend.apps.usage_ledger.models import ModelUsage
from backend.apps.usage_ledger.pricing import category_of, price_usage
from backend.apps.usage_ledger.rates import lookup_rate

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


def test_lookup_rate_uses_model_name():
    """基数按模型名取；未知模型返回空，不得当成已计价。"""
    assert lookup_rate("deepseek-flash")["currency"] == "CNY"
    assert lookup_rate("grok-4.7")["long_context_threshold"] == 200_000
    assert lookup_rate("deepseek-v4.1-flash")["alias_of"] == "deepseek-flash"
    assert lookup_rate("qwen3.5-omni-plus-realtime")["basis"] == "official-trial-audio"
    assert lookup_rate("not-a-model") is None


def test_cache_hit_is_not_added_to_input():
    """缓存是输入的子集，未命中只按差额计价。"""
    priced = price_usage(
        "govee",
        "deepseek-flash",
        input_tokens=1_000_000,
        cache_input_tokens=400_000,
        output_tokens=0,
    )

    assert priced["cost_input"] == Decimal("0.60000000")
    assert priced["cost_cache"] == Decimal("0.00800000")


def test_grok_long_context_uses_high_tier_for_whole_call():
    """输入达到 20 万时，整笔使用高档美元价并折成人民币。"""
    priced = price_usage("govee", "grok-4.7", input_tokens=200_000, output_tokens=0)
    short = price_usage("govee", "grok-4.7", input_tokens=199_999, output_tokens=0)

    assert priced["cost_total"] == Decimal("5.37056000")
    assert short["cost_total"] == Decimal("2.68526657")
    assert priced["pricing_snapshot"]["long_context"] is True
    assert priced["pricing_snapshot"]["currency"] == "USD"


def test_missing_moment_uses_idle_rate():
    """没有调用起点时按空闲，不套高峰。"""
    idle = price_usage("deepseek", "deepseek-flash", input_tokens=1_000_000)
    peak = price_usage(
        "deepseek",
        "deepseek-flash",
        input_tokens=1_000_000,
        occurred_at=datetime(2026, 10, 8, 10, 0, 0),
    )

    assert idle["cost_total"] == Decimal("1.00000000")
    assert idle["pricing_snapshot"]["peak"] is False
    assert peak["cost_total"] == Decimal("2.00000000")


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


def test_usage_dashboard_matches_single_summary():
    """批量口径与单次汇总一致：分类、厂商、金额都不因合并聚合而变。"""
    now = timezone.now()
    record_usage(
        event_id="dash:llm",
        provider="deepseek",
        model="deepseek-flash",
        occurred_at=now,
        input_tokens=100,
        output_tokens=10,
        category="LLM",
        source="task",
    )
    record_usage(
        event_id="dash:realtime",
        provider="dashscope",
        model="qwen3.5-omni-plus-realtime",
        occurred_at=now,
        input_tokens=50,
        output_tokens=5,
        category="Realtime",
        source="voice",
    )

    dashboard = usage_dashboard()
    plain_today = usage_summary("today")
    plain_voice = usage_summary("today", source="voice")

    assert dashboard["today"]["total"] == plain_today["total"]
    assert dashboard["today"]["categories"] == plain_today["categories"]
    assert dashboard["total"]["total"] == usage_summary("all")["total"]
    assert dashboard["voice_today"]["total"] == plain_voice["total"]
    assert dashboard["recent"] == plain_today["recent"]


def test_usage_dashboard_uses_five_queries():
    """四个口径 + 最近明细 = 5 条查询，分类数不影响查询数。"""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext

    during = timezone.now()
    for index, category in enumerate(("LLM", "TTS", "Realtime", "Embedding")):
        record_usage(
            event_id=f"dash:budget:{index}",
            provider="deepseek",
            model="deepseek-flash",
            occurred_at=during,
            input_tokens=10 + index,
            output_tokens=1,
            category=category,
            source="task",
        )

    with CaptureQueriesContext(connection) as ctx:
        usage_dashboard()

    assert len(ctx.captured_queries) == 5


def _stale_row(
    event_id: str,
    *,
    provider: str = "deepseek",
    model: str = "deepseek-flash",
    source: str = "task",
    **usage,
):
    """写一条「token 已入库、费用为 0」的旧账，模拟调价前或未计价的行。"""
    return record_usage(
        event_id=event_id,
        provider=provider,
        model=model,
        occurred_at=timezone.now(),
        category="LLM",
        source=source,
        cost_input=0,
        cost_cache=0,
        cost_output=0,
        cost_total=0,
        **usage,
    )


def test_recalculate_costs_rewrites_from_stored_tokens():
    """读库重算：费用按库里的 token 与发生时刻重算，并回写快照。"""
    row = _stale_row("recalc:1", input_tokens=1_000_000, output_tokens=1_000_000)

    result = recalculate_usage_costs()

    assert result["scanned"] == 1
    assert result["changed"] == 1
    row.refresh_from_db()
    expected = price_usage(
        "deepseek",
        "deepseek-flash",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        occurred_at=row.occurred_at,
    )
    assert row.cost_input == expected["cost_input"]
    assert row.cost_cache == expected["cost_cache"]
    assert row.cost_output == expected["cost_output"]
    assert row.cost_total == expected["cost_total"]
    assert row.pricing_status == "priced"
    assert row.pricing_snapshot["model"] == "deepseek-flash"


def test_recalculate_costs_is_idempotent():
    """重复执行不再产生变更，费用合计前后一致。"""
    _stale_row("recalc:2", input_tokens=1000, output_tokens=100)

    first = recalculate_usage_costs()
    second = recalculate_usage_costs()

    assert first["changed"] == 1
    assert second["changed"] == 0
    assert second["cost_before"] == second["cost_after"]


def test_recalculate_costs_dry_run_does_not_write():
    """dry-run 只报「将会变更」，库里的费用保持原样。"""
    row = _stale_row("recalc:3", input_tokens=1000, output_tokens=100)

    result = recalculate_usage_costs(dry_run=True)

    assert result["changed"] == 1
    row.refresh_from_db()
    assert row.cost_total == 0


def test_recalculate_costs_filters_provider_and_source():
    """按厂商过滤，只重算命中的行；TTS 仍按字符计价。"""
    _stale_row("recalc:4:deepseek", input_tokens=1000, output_tokens=100)
    _stale_row(
        "recalc:4:tts",
        provider="dashscope",
        model="sambert-zhichu-v1",
        source="voice",
        characters=10_000,
    )

    result = recalculate_usage_costs(provider="dashscope")

    assert result["scanned"] == 1
    assert ModelUsage.objects.get(event_id="recalc:4:tts").cost_total == Decimal("1.00000000")
    assert ModelUsage.objects.get(event_id="recalc:4:deepseek").cost_total == 0


def test_recalculate_costs_marks_unknown_model_unpriced():
    """价目未收录的模型照记 token，费用归 0 并标 unpriced。"""
    row = _stale_row(
        "recalc:5",
        provider="dashscope",
        model="unknown-model",
        input_tokens=100,
    )

    recalculate_usage_costs()

    row.refresh_from_db()
    assert row.pricing_status == "unpriced"
    assert row.cost_total == 0


def test_platform_billing_uses_backend_bridge_peak_rule():
    """高峰判断仍复用 backend_bridge，不回退到 agents 旧包。"""
    from backend.apps.usage_ledger import pricing
    from engines.backend_bridge.model_billing.billing import DeepSeekBilling

    assert pricing.DeepSeekBilling is DeepSeekBilling


def test_recalc_command_runs_as_dry_run():
    """管理命令可被 Django 发现，并透传 dry-run。"""
    from io import StringIO

    from django.core.management import call_command

    _stale_row("recalc:cmd", input_tokens=1000, output_tokens=100)
    out = StringIO()

    call_command("recalc_usage_costs", "--dry-run", stdout=out)

    assert "扫描 1 条" in out.getvalue()
    assert ModelUsage.objects.get(event_id="recalc:cmd").cost_total == 0


def test_recalculate_costs_pages_through_all_rows():
    """batch_size=1 时也按 usage_id 翻页跑完全部行，不重复、不漏。"""
    rows = [
        _stale_row(f"recalc:page:{index}", input_tokens=1000 + index, output_tokens=100)
        for index in range(3)
    ]

    result = recalculate_usage_costs(batch_size=1)

    assert result["scanned"] == 3
    assert result["changed"] == 3
    for row in rows:
        row.refresh_from_db()
        assert row.cost_total > 0
