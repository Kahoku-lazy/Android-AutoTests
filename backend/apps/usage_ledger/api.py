"""模型用量账本写入口与仪表盘聚合。"""

from __future__ import annotations

import uuid

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any

from django.conf import settings
from django.db import OperationalError, ProgrammingError
from django.db.models import Count, Sum
from django.utils import timezone

from utils.logs import backend_log

from .models import ModelUsage
from .pricing import category_of, normalize_provider, price_usage


def _as_decimal(value: Any) -> Decimal:
    """转成 8 位 Decimal。"""
    return Decimal(str(value or 0)).quantize(Decimal("0.00000001"))


# 平台运行产物的时间戳格式：与事件记录器落盘时一致（下划线分隔，毫秒三位）。
_USAGE_STAMP = "%Y-%m-%d_%H-%M-%S.%f"

# 重算时回写的费用列；与 models.ModelUsage 的 8 位小数列一致。
_COST_FIELDS = (
    "cost_input",
    "cost_cache",
    "cost_output",
    "cost_total",
    "pricing_status",
    "pricing_snapshot",
)


def _usage_moment(text: object) -> datetime:
    """
    把平台运行产物的时间戳解析成时刻。

    Args:
        text: `YYYY-MM-DD_HH-MM-SS.mmm` 形式的字符串。

    Returns:
        本地时区的时刻；解析失败时退回当前时间，绝不抛错。
        是否带时区跟随项目配置（`USE_TZ`），与账本其它写入保持一致。
    """
    try:
        naive = datetime.strptime(str(text or ""), _USAGE_STAMP)
    except (TypeError, ValueError):
        return timezone.now()
    if settings.USE_TZ:
        return timezone.make_aware(naive, timezone.get_current_timezone())
    return naive


def _provider_of(api_key_env: object) -> str:
    """
    由密钥环境变量名推断厂商标签。

    Args:
        api_key_env: 形如 `DEEPSEEK_API_KEY` / `OPENAI_API_KEY` 的名字。

    Returns:
        `deepseek` / `dashscope` / 其它原样小写；交给账本再归一。
    """
    text = str(api_key_env or "").upper()
    if "DASHSCOPE" in text:
        return "dashscope"
    if "DEEPSEEK" in text:
        return "deepseek"
    if "OPENAI" in text:
        return "openai"
    return ""


def record_run_usages(
    usages: list[dict],
    *,
    execution_id: str,
    model: str = "",
    source: str = "agent",
) -> int:
    """
    把一次平台运行的逐次用量写进账本。

    幂等键取「来源:执行 ID:轮次」，同一轮重复写入会更新而非新增。
    单条失败不影响其它条，也不向上抛错——入账不得阻断主流程。

    Args:
        usages: 逐次用量字典，键与事件层用量记录一致。
        execution_id: 本次运行的执行 ID，写进账本用于追溯。
        model: 模型名；为空时该条跳过模型字段的推断。
        source: 来源标签，默认 `agent`。

    Returns:
        成功写入的条数。
    """
    written = 0
    for index, item in enumerate(usages or [], 1):
        if not isinstance(item, dict):
            continue
        round_index = item.get("round") or index
        result = record_usage(
            event_id=f"{source}:{execution_id}:{round_index}",
            provider=_provider_of(item.get("api_key_env")),
            model=model or str(item.get("model_name") or ""),
            occurred_at=_usage_moment(item.get("started_at")),
            input_tokens=int(item.get("input_tokens") or 0),
            output_tokens=int(item.get("output_tokens") or 0),
            cache_input_tokens=int(item.get("cache_input_tokens") or 0),
            cache_creation_tokens=int(item.get("cache_creation_input_tokens") or 0),
            category="LLM",
            source=source,
            execution_id=execution_id,
            metadata={"api_key_env": str(item.get("api_key_env") or "")},
        )
        if result is not None:
            written += 1
    return written


def _json_safe(value: Any) -> Any:
    """把 Decimal 等对象转成 JSONField 可序列化值。"""
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value


def _iso_moment(text: object) -> datetime:
    """
    把 ISO 格式时间戳解析成时刻。

    Args:
        text: ISO 格式字符串（如知识库用量事件的 occurred_at）。

    Returns:
        本地时区的时刻；解析失败时退回当前时间，绝不抛错。
    """
    try:
        moment = datetime.fromisoformat(str(text or ""))
    except (TypeError, ValueError):
        return timezone.now()
    if moment.tzinfo is not None:
        return moment
    if settings.USE_TZ:
        return timezone.make_aware(moment, timezone.get_current_timezone())
    return moment


def record_embedding_usages(
    events: list[dict],
    *,
    execution_id: str,
    source: str = "knowledge",
) -> int:
    """
    把知识库嵌入用量事件逐调用写进账本。

    幂等键取「来源:执行 ID:轮次」，同一事件重复提交会更新而非新增。
    零 token 事件跳过；单条失败只记日志，不向上抛错——入账不得阻断检索。

    Args:
        events: 用量事件字典列表，键与 knowledge.usage.UsageEvent.as_dict() 一致。
        execution_id: 本次检索或索引批的执行 ID。
        source: 来源标签，默认 knowledge；评测传 knowledge_eval。

    Returns:
        成功写入的条数。
    """
    written = 0
    for index, item in enumerate(events or [], 1):
        if not isinstance(item, dict):
            continue
        tokens = int(item.get("tokens") or 0)
        if tokens <= 0:
            continue
        round_key = str(item.get("usage_id") or index)
        try:
            result = record_usage(
                event_id=f"{source}:{execution_id}:{round_key}",
                provider=_provider_of(item.get("api_key_env")),
                model=str(item.get("model") or ""),
                occurred_at=_iso_moment(item.get("occurred_at")),
                input_tokens=tokens,
                output_tokens=0,
                category="Embedding",
                source=source,
                execution_id=execution_id,
                metadata={
                    "api_key_env": str(item.get("api_key_env") or ""),
                    "phase": str(item.get("phase") or ""),
                    "base": str(item.get("base") or ""),
                },
            )
        except Exception:
            backend_log.exception(
                "embedding usage ledger write failed source=%s execution=%s",
                source,
                execution_id,
            )
            continue
        if result is not None:
            written += 1
    return written


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


def recalculate_usage_costs(
    *,
    provider: str = "",
    source: str = "",
    batch_size: int = 500,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    从 ai_usage_records 读 token 用量，按当前价目重算费用并回写。

    计费口径与写入账本时一致：DeepSeek 走 engines.backend_bridge.model_billing，
    其它厂商走本 App 的价目表；价目未收录的行按 unpriced 记 0。

    用于官方调价后的历史回填与按库核对。按 usage_id 分批读取，每批只回写有变化的行，
    因此重复执行幂等；`dry_run` 只计算不写库。

    Args:
        provider: 只重算该厂商（deepseek / dashscope）；空串表示全部。
        source: 只重算该来源（task / voice / chat 等）；空串表示全部。
        batch_size: 每批处理的行数，最小 1。
        dry_run: 为 True 时只计算、不写库。

    Returns:
        含 scanned / changed / cost_before / cost_after / dry_run 的字典；
        金额单位为元、保留 8 位小数。`changed` 在 dry_run 下表示「将会变更」的行数。
    """
    result: dict[str, Any] = {
        "scanned": 0,
        "changed": 0,
        "cost_before": Decimal("0.00000000"),
        "cost_after": Decimal("0.00000000"),
        "dry_run": dry_run,
    }
    rows = ModelUsage.objects.all()
    if provider:
        rows = rows.filter(provider=normalize_provider(provider))
    if source:
        rows = rows.filter(source=source)
    size = max(int(batch_size or 1), 1)
    last_id = None
    while True:
        page = rows.order_by("usage_id")
        if last_id is not None:
            page = page.filter(usage_id__gt=last_id)
        chunk = list(page[:size])
        if not chunk:
            break
        changed: list[ModelUsage] = []
        for row in chunk:
            before = _as_decimal(row.cost_total)
            priced = price_usage(
                row.provider,
                row.model,
                input_tokens=row.input_tokens,
                output_tokens=row.output_tokens,
                cache_input_tokens=row.cache_input_tokens,
                cache_creation_tokens=row.cache_creation_tokens,
                characters=row.characters,
                occurred_at=row.occurred_at,
            )
            after = _as_decimal(priced["cost_total"])
            snapshot = _json_safe(priced["pricing_snapshot"])
            result["scanned"] += 1
            result["cost_before"] += before
            result["cost_after"] += after
            if (
                _as_decimal(row.cost_input) == _as_decimal(priced["cost_input"])
                and _as_decimal(row.cost_cache) == _as_decimal(priced["cost_cache"])
                and _as_decimal(row.cost_output) == _as_decimal(priced["cost_output"])
                and before == after
                and row.pricing_status == priced["pricing_status"]
                and (row.pricing_snapshot or {}) == snapshot
            ):
                continue
            row.cost_input = _as_decimal(priced["cost_input"])
            row.cost_cache = _as_decimal(priced["cost_cache"])
            row.cost_output = _as_decimal(priced["cost_output"])
            row.cost_total = after
            row.pricing_status = priced["pricing_status"]
            row.pricing_snapshot = snapshot
            changed.append(row)
        if changed:
            result["changed"] += len(changed)
            if not dry_run:
                ModelUsage.objects.bulk_update(changed, _COST_FIELDS)
        last_id = chunk[-1].usage_id
    return result


def summarize_execution_cost(execution_id: str, source: str = "task") -> tuple[dict, list[str]]:
    """按执行 ID 汇总已入账费用。未计价行不进合计，但要在说明里可见。"""
    from decimal import Decimal

    rows = ModelUsage.objects.filter(execution_id=str(execution_id), source=source)
    totals = {
        "cost_input": Decimal("0"),
        "cost_cache": Decimal("0"),
        "cost_output": Decimal("0"),
        "cost_total": Decimal("0"),
    }
    notes: list[str] = []
    for row in rows:
        if row.pricing_status == "unpriced":
            notes.append(f"第 {row.event_id} 次调用未计价")
            continue
        totals["cost_input"] += row.cost_input
        totals["cost_cache"] += row.cost_cache
        totals["cost_output"] += row.cost_output
        totals["cost_total"] += row.cost_total
    return totals, notes


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
