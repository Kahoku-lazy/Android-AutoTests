"""模型用量账本写入口与仪表盘聚合。"""

from __future__ import annotations

import uuid

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.db import OperationalError, ProgrammingError
from django.db.models import Count, Sum
from django.utils import timezone

from .models import ModelUsage
from .pricing import category_of, normalize_provider, price_usage


def _as_decimal(value: Any) -> Decimal:
    """转成 8 位 Decimal。"""
    return Decimal(str(value or 0)).quantize(Decimal("0.00000001"))


def _json_safe(value: Any) -> Any:
    """把 Decimal 等对象转成 JSONField 可序列化值。"""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def record_usage(
    *,
    event_id: str,
    provider: str,
    model: str,
    occurred_at: datetime,
    input_tokens: int = 0,
    output_tokens: int = 0,
    cache_input_tokens: int = 0,
    cache_creation_tokens: int = 0,
    characters: int = 0,
    category: str = "",
    source: str = "",
    execution_id: str = "",
    usage_id: uuid.UUID | None = None,
    metadata: dict | None = None,
    pricing_snapshot: dict | None = None,
    cost_input: Any = None,
    cost_cache: Any = None,
    cost_output: Any = None,
    cost_total: Any = None,
    pricing_status: str = "",
) -> ModelUsage | None:
    """
    幂等写入一条模型用量；event_id 相同则更新。

    Args:
        event_id: 事件流定位，必须唯一。
        provider: deepseek / dashscope。
        model: 模型名。
        occurred_at: 发生时间。
        input_tokens / output_tokens / cache_* / characters: 用量。
        category: 模型分类；空时按模型推断。
        source: task / voice / rag 等。
        execution_id: 任务或会话 ID。
        usage_id: 随机 UUID；不传则生成。
        metadata: 附加信息。
        pricing_snapshot: 已有价目快照。
        cost_* / pricing_status: 已有费用；不传则按价目表计算。

    Returns:
        写入的 ModelUsage；表不存在或数据非法时返回 None。
    """
    provider = normalize_provider(provider, model)
    category = category or category_of(model, provider)
    total = max(int(input_tokens or 0), 0) + max(int(output_tokens or 0), 0)
    if cost_total is None:
        priced = price_usage(
            provider,
            model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cache_input_tokens=cache_input_tokens,
            cache_creation_tokens=cache_creation_tokens,
            characters=characters,
            occurred_at=occurred_at,
        )
        cost_input = priced["cost_input"]
        cost_cache = priced["cost_cache"]
        cost_output = priced["cost_output"]
        cost_total = priced["cost_total"]
        pricing_status = priced["pricing_status"]
        pricing_snapshot = priced["pricing_snapshot"]

    payload = {
        "provider": provider,
        "category": category,
        "model": model[:80],
        "occurred_at": occurred_at,
        "input_tokens": max(int(input_tokens or 0), 0),
        "output_tokens": max(int(output_tokens or 0), 0),
        "cache_input_tokens": max(int(cache_input_tokens or 0), 0),
        "cache_creation_tokens": max(int(cache_creation_tokens or 0), 0),
        "total_tokens": total,
        "characters": max(int(characters or 0), 0),
        "cost_input": _as_decimal(cost_input),
        "cost_cache": _as_decimal(cost_cache),
        "cost_output": _as_decimal(cost_output),
        "cost_total": _as_decimal(cost_total),
        "currency": "CNY",
        "pricing_status": pricing_status or "priced",
        "pricing_snapshot": _json_safe(pricing_snapshot or {}),
        "source": source[:32],
        "execution_id": execution_id[:128],
        "metadata": _json_safe(metadata or {}),
    }
    try:
        existing = ModelUsage.objects.filter(event_id=event_id[:180]).first()
        if existing is not None:
            for field, value in payload.items():
                setattr(existing, field, value)
            existing.save()
            return existing
        return ModelUsage.objects.create(
            usage_id=usage_id or uuid.uuid4(),
            event_id=event_id[:180],
            **payload,
        )
    except (OperationalError, ProgrammingError):
        return None


def record_voice_event(
    payload: dict,
    session_id: str,
    user_id: str = "",
    *,
    source: str = "voice",
) -> ModelUsage | None:
    """把知识库助手的 JSONL 用量事件写成账本。

    Args:
        payload: 日志里的用量事件（含 provider / model / tokens）。
        session_id: 会话 id，写入 execution_id。
        user_id: 当前登录用户 id。
        source: 来源标识；语音会话为 voice，文字会话为 chat。

    Returns:
        写入的 ModelUsage；表不存在或数据非法时返回 None。
    """
    kind = str(payload.get("event") or "")
    provider = normalize_provider(
        str(payload.get("provider") or ""),
        str(payload.get("model") or ""),
    )
    model = str(payload.get("model") or "")
    if not model:
        model = "qwen3.5-omni-plus-realtime" if provider == "dashscope" else "deepseek-flash"
    category = str(payload.get("category") or "")
    if not category:
        if kind == "asr_usage":
            category = "ASR"
        elif kind == "tts_usage":
            category = "TTS"
        elif kind == "embedding_usage":
            category = "Embedding"
    usage_id_text = str(payload.get("usage_id") or uuid.uuid4().hex)
    try:
        usage_id = uuid.UUID(usage_id_text)
    except ValueError:
        usage_id = uuid.uuid4()
        payload["usage_id"] = usage_id.hex
    reply_id = str(payload.get("reply_id") or "unknown")
    event_id = f"{source}:{session_id}:{reply_id}:{kind}:{usage_id.hex}"
    occurred_at = timezone.now()
    return record_usage(
        event_id=event_id,
        provider=provider,
        model=model,
        occurred_at=occurred_at,
        input_tokens=int(
            payload.get("input_tokens")
            or (payload.get("tokens") if kind == "embedding_usage" else 0)
            or 0,
        ),
        output_tokens=int(payload.get("output_tokens") or 0),
        cache_input_tokens=int(payload.get("cache_input_tokens") or 0),
        cache_creation_tokens=int(payload.get("cache_creation_input_tokens") or 0),
        characters=int(payload.get("characters") or 0),
        category=category,
        source=source,
        execution_id=session_id,
        usage_id=usage_id,
        metadata={
            "kind": kind,
            "reply_id": reply_id,
            "user_id": user_id,
        },
    )


def _period_start(period: str) -> datetime | None:
    """按 today/7d/30d 返回起始时间；all 返回 None。"""
    now = timezone.now()
    if period == "today":
        return now.replace(hour=0, minute=0, second=0, microsecond=0)
    if period == "7d":
        return now - timedelta(days=7)
    if period == "30d":
        return now - timedelta(days=30)
    return None


def _scoped_usage(start: datetime | None, source: str = ""):
    """按周期与来源取用量查询集；分类/厂商维度由调用方一次分组。"""
    qs = ModelUsage.objects.all()
    if start is not None:
        qs = qs.filter(occurred_at__gte=start)
    if source:
        qs = qs.filter(source=source)
    return qs


def _provider_label(provider: object) -> str:
    """厂商展示名：dashscope → DASHSCOPE，其余 → DeepSeek。"""
    return "DASHSCOPE" if str(provider or "").lower() == "dashscope" else "DeepSeek"


def _grouped_rows(start: datetime | None, source: str = "") -> list[dict]:
    """一次按 category + provider 分组，避免「每个分类再查一次厂商」的 N+1。"""
    return list(
        _scoped_usage(start, source)
        .values("category", "provider")
        .annotate(
            tokens=Sum("total_tokens"),
            cost=Sum("cost_total"),
            calls=Count("usage_id"),
        ),
    )


def _shape_summary(rows: list[dict], period: str) -> dict:
    """把分组行拼成 {total, categories(含 providers)}，分类与厂商按 token 降序。"""
    total_tokens = 0
    total_cost = Decimal(0)
    total_calls = 0
    buckets: dict[str, dict] = {}
    for row in rows:
        tokens = int(row["tokens"] or 0)
        cost = Decimal(row["cost"] or 0)
        calls = int(row["calls"] or 0)
        total_tokens += tokens
        total_cost += cost
        total_calls += calls

        category = row["category"] or "Other"
        bucket = buckets.setdefault(
            category,
            {"tokens": 0, "cost": Decimal(0), "calls": 0, "providers": {}},
        )
        bucket["tokens"] += tokens
        bucket["cost"] += cost
        bucket["calls"] += calls
        provider = _provider_label(row["provider"])
        provider_bucket = bucket["providers"].setdefault(
            provider,
            {"tokens": 0, "cost": Decimal(0), "calls": 0},
        )
        provider_bucket["tokens"] += tokens
        provider_bucket["cost"] += cost
        provider_bucket["calls"] += calls

    categories = []
    for name, bucket in sorted(buckets.items(), key=lambda item: item[1]["tokens"], reverse=True):
        providers = [
            {
                "provider": provider,
                "tokens": values["tokens"],
                "cost": float(values["cost"]),
                "calls": values["calls"],
            }
            for provider, values in sorted(
                bucket["providers"].items(),
                key=lambda item: item[1]["tokens"],
                reverse=True,
            )
        ]
        categories.append(
            {
                "category": name,
                "tokens": bucket["tokens"],
                "cost": float(bucket["cost"]),
                "calls": bucket["calls"],
                "providers": providers,
            },
        )
    return {
        "period": period,
        "total": {
            "tokens": total_tokens,
            "cost": float(total_cost),
            "calls": total_calls,
        },
        "categories": categories,
    }


def _recent_records(start: datetime | None, source: str, limit: int) -> list[dict]:
    """最近明细；limit <= 0 时不查。"""
    if limit <= 0:
        return []
    rows = _scoped_usage(start, source).order_by("-occurred_at")[:limit]
    return [_record_payload(record) for record in rows]


def usage_summary(
    period: str = "today",
    recent_limit: int = 20,
    source: str = "",
) -> dict:
    """
    仪表盘用量汇总：总量、分类、厂商、最近明细。

    Args:
        period: today/7d/30d/all。
        recent_limit: 最近明细条数。
        source: 按来源过滤，如 voice/task；空串不过滤。

    Returns:
        可直接 JSON 序列化的汇总。
    """
    try:
        summary = _shape_summary(_grouped_rows(_period_start(period), source), period)
        summary["recent"] = _recent_records(_period_start(period), source, recent_limit)
        return summary
    except (OperationalError, ProgrammingError):
        return {
            "period": period,
            "total": {"tokens": 0, "cost": 0.0, "calls": 0},
            "categories": [],
            "recent": [],
        }


def usage_dashboard() -> dict:
    """
    仪表盘一次取齐五个用量口径，避免重复聚合。

    Returns:
        含 today / total / voice_today / voice_total / recent 的字典；
        结构分别与 `usage_summary` 同口径。
    """
    start = _period_start("today")
    try:
        today = _shape_summary(_grouped_rows(start), "today")
        total = _shape_summary(_grouped_rows(None), "all")
        voice_today = _shape_summary(_grouped_rows(start, "voice"), "today")
        voice_total = _shape_summary(_grouped_rows(None, "voice"), "all")
        recent = _recent_records(start, "", 20)
    except (OperationalError, ProgrammingError):
        empty = {
            "period": "today",
            "total": {"tokens": 0, "cost": 0.0, "calls": 0},
            "categories": [],
        }
        return {
            "today": {**empty, "recent": []},
            "total": {**empty, "period": "all", "recent": []},
            "voice_today": {**empty, "recent": []},
            "voice_total": {**empty, "period": "all", "recent": []},
            "recent": [],
        }
    return {
        "today": {**today, "recent": []},
        "total": {**total, "recent": []},
        "voice_today": {**voice_today, "recent": []},
        "voice_total": {**voice_total, "recent": []},
        "recent": recent,
    }


def _record_payload(record: ModelUsage) -> dict:
    """最近明细的展示字段。"""
    provider = "DASHSCOPE" if str(record.provider).lower() == "dashscope" else "DeepSeek"
    return {
        "usage_id": str(record.usage_id),
        "event_id": record.event_id,
        "execution_id": record.execution_id,
        "occurred_at": record.occurred_at.isoformat(),
        "provider": provider,
        "category": record.category,
        "model": record.model,
        "source": record.source,
        "tokens": record.total_tokens,
        "characters": record.characters,
        "cost": f"{record.cost_total:.8f}",
        "pricing_status": record.pricing_status,
    }
