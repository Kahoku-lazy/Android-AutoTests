"""引擎侧设备日志工具：按时间读取，或按关键词检查是否出现。

`check_device_log` 直接读已落盘的型号日志文件，不依赖进程内日志总线。
"""

from __future__ import annotations

import json
import re
import time

from datetime import datetime, timedelta, timezone
from pathlib import Path

from engines.ai.base import ToolSpec
from engines.device.logbus import (
    BEIJING_TZ,
    LogSourceUnknown,
    format_stamp,
    get_log_bus,
    merge_lines_by_timestamp,
)
from engines.device.logfiles import range_lines

__all__ = [
    "LOG_EMPTY",
    "check_device_log",
    "read_device_log",
    "serial_tool_specs",
]

LOG_EMPTY = "日志为空，请检查断后是否正确连接，此轮执行终止"
_CHECK_WINDOW = timedelta(seconds=5)

LOG_SPAN_DEFAULT_SECONDS = 30.0
LOG_SPAN_MAX_SECONDS = 300.0
LOG_AT_FORMATS = (
    "%Y-%m-%d %H:%M:%S.%f",
    "%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%H:%M:%S",
)
_TOOL_ORDER = ("read_device_log", "check_device_log")


def _parse_log_at(value: str):
    """解析查询时间点。支持完整时间，或只给时刻（按当天北京时间）。

    可以带毫秒，也可以只到秒。只到秒时按该秒的 `.000`。
    """
    text = (value or "").strip()
    for fmt in LOG_AT_FORMATS:
        try:
            moment = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if fmt.startswith("%H"):
            today = datetime.now(BEIJING_TZ).date()
            moment = datetime.combine(today, moment.time())
        return moment.replace(tzinfo=BEIJING_TZ)

    raise ValueError(
        "时间点无法解析: "
        f"{value!r}；期望 `YYYY-MM-DD HH:MM:SS.mmm`、`YYYY-MM-DD HH:MM:SS`、"
        "`HH:MM:SS.mmm` 或 `HH:MM:SS`（北京时间）"
    )


def _clamp_log_span(seconds: float) -> float:
    """把查询跨度夹到 [1, 300]；未给时用 30 秒。"""
    span = float(seconds or 0) or LOG_SPAN_DEFAULT_SECONDS
    return max(1.0, min(span, LOG_SPAN_MAX_SECONDS))


def _log_stamp(epoch: float) -> str:
    """epoch 转为北京时间毫秒字符串。"""
    return format_stamp(datetime.fromtimestamp(epoch, tz=timezone.utc))


def _disabled_port_note(port: int) -> str:
    """已登记且监听关闭时返回说明；未登记或仍开启时返回空串。"""
    from apps.ai_assistant.log_port_service import disabled_port_note

    return disabled_port_note(int(port) if port else 0)


def _log_dir() -> Path:
    """平台实时写入的日志目录。"""
    return Path(__file__).resolve().parents[3] / "logs"


def _sku_token(sku: str) -> str:
    """型号收成文件名前缀；空串表示没有可用型号。"""
    return re.sub(r"[^0-9A-Za-z_.-]", "", str(sku or "").strip())


def _sku_log_files(sku: str) -> list[Path]:
    """按型号找日志文件：H6810 → `H6810_*.log`，H7011 → `H7011_*.log`。"""
    token = _sku_token(sku)
    directory = _log_dir()
    if not token or not directory.is_dir():
        return []
    return sorted(path for path in directory.glob(f"{token}_*.log") if path.is_file())


def _line_msg(line) -> str:
    """文件行还原成落盘原文。"""
    return f"{line.timestamp} [{line.source}] {line.text}"


def _check_result(*, timestamp: str = "", msg: str = "", result: str) -> str:
    """验收结论：timestamp / msg / result。"""
    return json.dumps(
        {"timestamp": timestamp, "msg": msg, "result": result},
        ensure_ascii=False,
    )


def read_device_log(
    at: str = "",
    seconds: float = 0,
    port: int = 0,
    keyword: str = "",
    user_id: str = "",
) -> str:
    """查询平台已采集的设备日志（只读，不连设备、不改设备状态）。
    排查「设备到底响应了没有」「某个功能点打印了没有」时用；不要每一步都调用。
    取数是**内存缓冲 + 已落盘的日志文件**：缓冲覆盖不到的更早时段会从日志文件回溯，
    因此查一个几分钟前的时刻同样查得到（不再受缓冲保留时长限制）。
    同一时间戳的日志会合并成一条（text 内保留换行），且**最新的时间排在最上面**。

    Args:
        at: 时间点（北京时间）。可写 `2026-09-28 13:05:37.500` 或 `2026-09-28 13:05:37`，
            也可只写 `13:05:37.500` 或 `13:05:37`（按今天）。不带毫秒时按该秒的 `.000`。
            给了就返回**该时刻之后**一个跨度的日志；不传则返回**最近**一个跨度
        seconds: 跨度秒数，默认 30，最大 300
        port: 日志来源端口，默认平台配置的端口（现场 7005）；传未配置的端口不报错，返回「端口 X 未配置为日志来源」的结论
        keyword: 可选，只看包含该关键词的日志行（忽略大小写），并还原命中的功能模块 / 功能点
    """
    del user_id
    bus = get_log_bus()
    if bus is None:
        raise ValueError("设备日志采集未启动：平台未开启日志采集（DEVICE_LOG_ENABLED）或无可用来源")

    span = _clamp_log_span(seconds)
    if at:
        start = _parse_log_at(at)
        start_epoch = start.timestamp()
        end_epoch = start_epoch + span
        start_stamp, end_stamp = _log_stamp(start_epoch), _log_stamp(end_epoch)
    else:
        end_epoch = time.time()
        start_epoch = end_epoch - span
        start_stamp, end_stamp = _log_stamp(start_epoch), _log_stamp(end_epoch)

    wanted = (keyword or "").strip()
    query = {
        "port": int(port) if port else 0,
        "channel": "",
        "from": start_stamp,
        "to": end_stamp,
        "span_seconds": span,
        "keyword": wanted,
    }

    disabled_port = _disabled_port_note(int(port) if port else 0)
    if disabled_port:
        query["port"] = int(port)
        return json.dumps(
            {
                "query": query,
                "line_count": 0,
                "conclusion": "port_disabled",
                "note": disabled_port,
                "lines": [],
                "keyword_hits": [],
            },
            ensure_ascii=False,
        )

    try:
        found = bus.read_range(
            start_epoch=start_epoch,
            end_epoch=end_epoch,
            port=int(port) if port else None,
        )
    except LogSourceUnknown as exc:
        return json.dumps(
            {
                "query": query,
                "line_count": 0,
                "conclusion": "port_not_configured",
                "note": str(exc),
                "lines": [],
                "keyword_hits": [],
            },
            ensure_ascii=False,
        )

    rows = found["lines"]
    query["port"] = int(found["port"])
    query["channel"] = found["channel"]
    hits: list[dict] = []
    if wanted:
        matched = [line for line in rows if wanted.lower() in line.text.lower()]
        for line in matched:
            for name, features in bus.keywords.match(line.text):
                hits.append({"keyword": name, "timestamp": line.timestamp, "features": features})
        rows = matched

    if not rows:
        conclusion = "no_keyword_hit" if wanted else "no_log"
        note = (
            f"该时间范围内没有包含 {wanted!r} 的日志"
            if wanted
            else "该时间范围内无日志（已查内存缓冲与已落盘的日志文件）"
        )
    else:
        conclusion = "ok"
        note = ""

    raw_line_count = len(rows)
    merged = merge_lines_by_timestamp(rows)
    payload = {
        "query": query,
        "line_count": len(merged),
        "raw_line_count": raw_line_count,
        "sources": {
            "buffer_lines": int(found.get("buffer_lines") or 0),
            "file_lines": int(found.get("file_lines") or 0),
        },
        "conclusion": conclusion,
        "note": note,
        "lines": merged,
        "keyword_hits": hits,
    }
    return json.dumps(payload, ensure_ascii=False, default=str)


def check_device_log(
    keyword: str,
    at: str = "",
    sku: str = "",
    user_id: str = "",
) -> str:
    """在型号日志文件里检查传入的关键词是否出现在起点之后的 5 秒内。
    型号决定文件：H6810 读 `H6810_*.log`，H7011 读 `H7011_*.log`。
    keyword 按传入字符串在日志行中查找（忽略大小写）。
    找到关键词返回该行原文且 result 为 PASS；窗口内有日志但没有关键词则 result 为 FAIL。
    起点之后 5 秒内没有任何日志时中断本轮。

    Args:
        keyword: 日志关键词原文，例如 switch_off
        at: 起点时间（北京时间）。从这一刻起向后 5 秒，含起点。
            可写到毫秒，也可只到秒（按该秒的 `.000`）
        sku: 设备型号，例如 H6810 或 H7011
    """
    del user_id
    wanted = str(keyword or "").strip()
    if not wanted or not str(at or "").strip() or not _sku_token(sku):
        return _check_result(result="FAIL")

    start = _parse_log_at(at)
    start_epoch = start.timestamp()
    end_epoch = (start + _CHECK_WINDOW).timestamp()
    files = _sku_log_files(sku)
    rows = []
    for path in files:
        rows.extend(range_lines(path, start_epoch, end_epoch))
    rows.sort(key=lambda line: line.timestamp)
    if not rows:
        raise ValueError(LOG_EMPTY)

    needle = wanted.lower()
    for line in rows:
        msg = _line_msg(line)
        if needle in msg.lower():
            return _check_result(timestamp=line.timestamp, msg=msg, result="PASS")
    return _check_result(result="FAIL")


def serial_tool_specs() -> list[ToolSpec]:
    """按固定顺序产出日志工具的 `ToolSpec` 列表。"""
    impls = {
        "read_device_log": read_device_log,
        "check_device_log": check_device_log,
    }
    return [
        ToolSpec(name=name, handler=impls[name], read_only=True, auto_allow=True)
        for name in _TOOL_ORDER
    ]
