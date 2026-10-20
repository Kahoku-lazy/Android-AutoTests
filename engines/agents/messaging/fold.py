"""
python -m 调试路径: engines.agents.messaging.fold

本模块的业务功能如下：
1. step: 把一条事件折成文本日志行和结构化记录。不写文件，不写库。
"""

from __future__ import annotations

import time

from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo

from .billing import DeepSeekBilling
from .record import EventRecord

_SHANGHAI = ZoneInfo("Asia/Shanghai")
_ZERO = Decimal("0.00000000")
_ROLE_KIND = {
    "executor_role": "executor",
    "verifier_role": "verifier",
}


class StepResult:
    """一次折叠的产出：日志行、记录。"""

    def __init__(self) -> None:
        self.log_lines: list[tuple[str, str]] = []
        self.records: list[EventRecord] = []


def step(event, state: dict, models: dict[str, str] | None = None) -> StepResult:
    """按事件类型更新状态，返回本条要写的日志和要交出的记录。

    Args:
        event: 事件流里的一条事件。
        state: 跨事件的累积状态。增量、角色、模型名和本轮费用都在这里。
        models: 角色名到模型名。发言开始早于模型调用时用它填写模型。

    Returns:
        本条事件的日志行和结构化记录。认不出的事件两者都为空。
    """
    kind = type(event).__name__
    for handle in (
        _flow_boundary,
        _reply,
        _model_start,
        _content_delta,
        _content_end,
        _data_start,
        _data_delta,
        _data_end,
        _tool_call,
        _tool_result,
        _model_end,
    ):
        result = handle(event, state, kind, models)
        if result is not None:
            return result
    return StepResult()


def _flow_boundary(event, state: dict, kind: str, models) -> StepResult | None:
    """步骤边界不写日志，也不交出记录。"""
    del event, state, models
    if kind != "CustomEvent":
        return None
    return StepResult()


def _reply(event, state: dict, kind: str, models) -> StepResult | None:
    """一轮发言的起止。开始时记住角色，结束时写出本轮合计。"""
    if kind == "ReplyStartEvent":
        role = str(getattr(event, "name", "") or "")
        model = str((models or {}).get(role) or "").strip() or "-"
        state.clear()
        state["_model"] = model
        state["_started"] = time.monotonic()
        state["_started_at"] = _now()
        state["_role"] = role
        state["_kind"] = _ROLE_KIND.get(role, "")
        result = StepResult()
        result.log_lines.append((model, f"开始 | {role}"))
        result.records.append(
            _record(
                state,
                kind,
                "开始",
                "reply",
                started_at=state["_started_at"],
                payload={"role": role, "model": model},
            )
        )
        return result
    if kind == "ReplyEndEvent":
        model = str(state.get("_model") or "-")
        detail, duration_ms = _reply_elapsed(state)
        ended = _now()
        started_at = state.get("_started_at")
        if not isinstance(started_at, datetime):
            started_at = ended
        tokens = state.get("_tok") or [0, 0, 0]
        fees = state.get("_fee") or [_ZERO, _ZERO, _ZERO]
        result = StepResult()
        result.log_lines.extend(
            [
                (model, f"结束 | {getattr(event, 'finished_reason', '')}"),
                (model, f"本轮执行时间 | {detail}"),
                (model, f"本轮执行总计量 | {_token_action(*tokens)}"),
                (model, f"本轮执行总计量 | {_fee_action(*fees)}"),
            ]
        )
        result.records.append(
            _record(
                state,
                kind,
                "结束",
                "reply",
                started_at=started_at,
                ended_at=ended,
                duration_ms=duration_ms,
                cost_input=fees[0],
                cost_output=fees[1],
                cost_cache=fees[2],
                payload={"finished_reason": str(getattr(event, "finished_reason", "") or "")},
            )
        )
        return result
    return None


def _model_start(event, state: dict, kind: str, models) -> StepResult | None:
    """模型调用开始只记住模型名和起点。"""
    del models
    if kind != "ModelCallStartEvent":
        return None
    name = str(getattr(event, "model_name", "") or "").strip()
    if name:
        state["_model"] = name
    state["_call_at"] = _now()
    return StepResult()


def _content_delta(event, state: dict, kind: str, models) -> StepResult | None:
    """正文和思考的增量只累积，不交记录。"""
    del models
    block = {"TextBlockDeltaEvent": "text", "ThinkingBlockDeltaEvent": "thinking"}.get(kind)
    if block is None:
        return None
    block_id = event.block_id
    state.setdefault(f"txt:{block_id}", []).append(event.delta)
    state.setdefault(f"txtat:{block_id}", _now())
    return StepResult()


def _content_end(event, state: dict, kind: str, models) -> StepResult | None:
    """正文和思考在块结束时交一条记录。只有思考写日志。"""
    del models
    block = {"TextBlockEndEvent": "text", "ThinkingBlockEndEvent": "thinking"}.get(kind)
    if block is None:
        return None
    parts = state.pop(f"txt:{event.block_id}", [])
    joined = "".join(parts)
    text = joined or (getattr(event, "text", None) or "")
    started_at, ended_at, duration_ms = _span(state, f"txtat:{event.block_id}")
    result = StepResult()
    if block == "thinking":
        shown = text.strip()
        action = f"思考 | {shown}" if shown else "思考"
        result.log_lines.append((str(state.get("_model") or "-"), action))
    result.records.append(
        _record(
            state,
            kind,
            "推理",
            block,
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            payload={"text": text, "delta_count": len(parts), "chars": len(text)},
        )
    )
    return result


def _data_start(event, state: dict, kind: str, models) -> StepResult | None:
    """数据块开始只记媒体类型和起点。"""
    del models
    if kind != "DataBlockStartEvent":
        return None
    state[f"b64at:{event.block_id}"] = _now()
    state[f"b64mt:{event.block_id}"] = str(getattr(event, "media_type", "") or "")
    return StepResult()


def _data_delta(event, state: dict, kind: str, models) -> StepResult | None:
    """数据块的 base64 增量只拼接。"""
    del models
    if kind != "DataBlockDeltaEvent":
        return None
    block_id = event.block_id
    state.setdefault(f"b64:{block_id}", []).append(getattr(event, "data", None) or "")
    state[f"b64mt:{block_id}"] = str(getattr(event, "media_type", "") or "")
    state.setdefault(f"b64at:{block_id}", _now())
    return StepResult()


def _data_end(event, state: dict, kind: str, models) -> StepResult | None:
    """数据块结束时交出拼好的 base64，不写日志。"""
    del models
    if kind != "DataBlockEndEvent":
        return None
    image = "".join(state.pop(f"b64:{event.block_id}", []))
    media_type = str(state.pop(f"b64mt:{event.block_id}", "") or "")
    started_at, ended_at, duration_ms = _span(state, f"b64at:{event.block_id}")
    result = StepResult()
    result.records.append(
        _record(
            state,
            kind,
            "推理",
            "data",
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            media_type=media_type,
            image_b64=image,
            payload={"media_type": media_type, "bytes": len(image)},
        )
    )
    return result


def _tool_call(event, state: dict, kind: str, models) -> StepResult | None:
    """工具入参：开始不落行，增量逐条落行，结束交出拼好的入参。"""
    del models
    if kind == "ToolCallStartEvent":
        call_id = event.tool_call_id
        state[f"call:{call_id}"] = []
        state[f"callname:{call_id}"] = event.tool_call_name
        state[f"callat:{call_id}"] = _now()
        return StepResult()
    if kind == "ToolCallDeltaEvent":
        call_id = event.tool_call_id
        bucket = state.setdefault(f"call:{call_id}", [])
        index = len(bucket)
        bucket.append(event.delta)
        result = StepResult()
        result.records.append(
            _record(
                state,
                kind,
                "推理",
                "tool_call",
                is_delta=True,
                ended_at=_now(),
                payload={"delta": event.delta, "idx": index},
            )
        )
        return result
    if kind == "ToolCallEndEvent":
        call_id = event.tool_call_id
        args = "".join(state.pop(f"call:{call_id}", []))
        name = state.pop(f"callname:{call_id}", "-")
        started_at, ended_at, duration_ms = _span(state, f"callat:{call_id}")
        model = str(state.get("_model") or "-")
        result = StepResult()
        result.log_lines.append((model, f"工具调用 | {name} | {args}"))
        result.records.append(
            _record(
                state,
                kind,
                "推理",
                "tool_call",
                started_at=started_at,
                ended_at=ended_at,
                duration_ms=duration_ms,
                payload={"tool_name": name, "args": args},
            )
        )
        return result
    return None


def _tool_result(event, state: dict, kind: str, models) -> StepResult | None:
    """工具返回：文本增量逐条落行，图片只拼接，结束时写一行日志。"""
    del models
    if kind == "ToolResultStartEvent":
        call_id = event.tool_call_id
        state[f"res:{call_id}"] = []
        state[f"resname:{call_id}"] = event.tool_call_name
        state[f"resat:{call_id}"] = _now()
        return StepResult()
    if kind == "ToolResultTextDeltaEvent":
        call_id = event.tool_call_id
        bucket = state.setdefault(f"res:{call_id}", [])
        index = len(bucket)
        bucket.append(event.delta)
        result = StepResult()
        result.records.append(
            _record(
                state,
                kind,
                "执行",
                "tool_result",
                is_delta=True,
                ended_at=_now(),
                payload={"delta": event.delta, "idx": index},
            )
        )
        return result
    if kind == "ToolResultDataDeltaEvent":
        call_id = event.tool_call_id
        data = getattr(event, "data", None) or ""
        note = f"图片 {event.media_type} {len(data)}字符base64"
        state.setdefault(f"imgnote:{call_id}", []).append(note)
        state.setdefault(f"imgb64:{call_id}", []).append(data)
        state[f"imgmt:{call_id}"] = event.media_type
        return StepResult()
    if kind == "ToolResultEndEvent":
        call_id = event.tool_call_id
        name = state.pop(f"resname:{call_id}", "-")
        out = "".join(state.pop(f"res:{call_id}", []))
        notes = state.pop(f"imgnote:{call_id}", [])
        image = "".join(state.pop(f"imgb64:{call_id}", []))
        media_type = str(state.pop(f"imgmt:{call_id}", "") or "")
        action = f"工具返回 | {name} | {event.state} | {out}"
        if notes:
            action = f"{action} | {' | '.join(notes)}"
        started_at, ended_at, duration_ms = _span(state, f"resat:{call_id}")
        model = str(state.get("_model") or "-")
        result = StepResult()
        result.log_lines.append((model, action))
        result.records.append(
            _record(
                state,
                kind,
                "执行",
                "tool_result",
                started_at=started_at,
                ended_at=ended_at,
                duration_ms=duration_ms,
                media_type=media_type,
                image_b64=image,
                payload={"tool_name": name, "status": str(event.state), "result": out},
            )
        )
        return result
    return None


def _model_end(event, state: dict, kind: str, models) -> StepResult | None:
    """模型调用结束：费用只算一次，日志和记录共用这组 8 位数。"""
    del models
    if kind != "ModelCallEndEvent":
        return None
    incoming = int(getattr(event, "input_tokens", 0) or 0)
    outgoing = int(getattr(event, "output_tokens", 0) or 0)
    cache_hit = int(getattr(event, "cache_input_tokens", 0) or 0)
    model = str(state.get("_model") or "-")
    moment = _created_at(event)
    billing = DeepSeekBilling()
    input_cost, output_cost, cache_cost = billing.cost(model, incoming, outgoing, cache_hit, moment)
    tokens = state.setdefault("_tok", [0, 0, 0])
    tokens[0] += incoming
    tokens[1] += outgoing
    tokens[2] += cache_hit
    fees = state.setdefault("_fee", [_ZERO, _ZERO, _ZERO])
    fees[0] += input_cost
    fees[1] += output_cost
    fees[2] += cache_cost
    started_at, ended_at, duration_ms = _span(state, "_call_at")
    result = StepResult()
    result.log_lines.append((model, _token_action(incoming, outgoing, cache_hit)))
    result.log_lines.append((model, _fee_action(input_cost, output_cost, cache_cost)))
    result.records.append(
        _record(
            state,
            kind,
            "推理",
            "model_call",
            started_at=started_at,
            ended_at=ended_at,
            duration_ms=duration_ms,
            cost_input=input_cost,
            cost_output=output_cost,
            cost_cache=cache_cost,
            pricing_snapshot=billing.snapshot(model, moment),
            payload={
                "model": model,
                "finished_reason": str(getattr(event, "finished_reason", "") or ""),
                "input_tokens": incoming,
                "output_tokens": outgoing,
                "cache_input_tokens": cache_hit,
            },
        )
    )
    return result


def _record(state: dict, kind: str, phase: str, block_type: str, **kwargs) -> EventRecord:
    """用本轮已记住的角色和模型填一条记录。"""
    return EventRecord(
        event_type=kind,
        phase=phase,
        block_type=block_type,
        role_name=str(state.get("_role") or ""),
        role_kind=str(state.get("_kind") or ""),
        model=str(state.get("_model") or ""),
        **kwargs,
    )


def _now() -> datetime:
    """当前北京时间。"""
    return datetime.now(_SHANGHAI)


def _span(state: dict, key: str) -> tuple[datetime, datetime, int]:
    """取出起点并给出结束时刻与毫秒耗时。没有起点时起止相同。"""
    ended = _now()
    started = state.pop(key, None)
    if not isinstance(started, datetime):
        started = ended
    duration_ms = max(int((ended - started).total_seconds() * 1000), 0)
    return started, ended, duration_ms


def _reply_elapsed(state: dict) -> tuple[str, int]:
    """本轮耗时的日志文本和毫秒数。没有起点时文本为 -。"""
    started = state.get("_started")
    if not isinstance(started, int | float):
        return "-", 0
    elapsed = time.monotonic() - started
    return f"{elapsed:.3f}秒", max(int(round(elapsed * 1000)), 0)


def _as_million(count: int) -> str:
    """token 个数换成百万，保留 6 位小数，单位 M。"""
    amount = Decimal(int(count)) / Decimal(1_000_000)
    return f"{amount:.6f}M"


def _as_yuan(amount: Decimal) -> str:
    """费用保留 8 位小数，单位元。"""
    return f"{amount:.8f}元"


def _token_action(incoming: int, outgoing: int, cache_hit: int) -> str:
    """模型 token 行：输入、输出、缓存，单位 M。"""
    return f"模型token：{_as_million(incoming)}，{_as_million(outgoing)}，{_as_million(cache_hit)}"


def _fee_action(input_cost: Decimal, output_cost: Decimal, cache_cost: Decimal) -> str:
    """模型费用行：输入、输出、缓存，单位元，8 位小数。"""
    return f"模型费用：{_as_yuan(input_cost)}，{_as_yuan(output_cost)}，{_as_yuan(cache_cost)}"


def _created_at(event) -> datetime | None:
    """事件上的调用时刻。空或无法解析时返回 None，计费按空闲时段。"""
    text = str(getattr(event, "created_at", "") or "").strip()
    if not text:
        return None
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        return None
