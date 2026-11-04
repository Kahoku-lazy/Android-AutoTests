"""
文件名: ➡️ tool_serial.py 🏁
路径: ➡️ engines/agents/tools/tool_serial.py 🏁
模块功能：➡️ 引擎侧设备日志工具：按型号和端口检查当前抓取文件里有没有关键词 🏁
Python 调试：➡️ python -m engines.agents.tools.tool_serial 🏁
时间：➡️ 2026-10-20 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. check_device_log: 在指定端口的当前抓取文件里检查关键词是否出现在起点之后的 5 秒内
2. serial_tool_specs: 按固定顺序产出日志工具的 `ToolSpec` 列表
3. _capture_rows: 按（长度, 修改时间, 文件身份）缓存已解析行，第二次起只解析新增部分
🏁
关联模块：➡️
1. utils.logs: 导入 capture_file_path
🏁
测试：➡️
1. tests/engines/agents/test_tool_serial.py: 单文件调试指令：python -m pytest tests/engines/agents/test_tool_serial.py -vv --tb=short
🏁
"""

from __future__ import annotations

import json
import re
import threading

from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from utils.logs import capture_file_path

from .tool_base import ToolSpec

__all__ = [
    "LOG_EMPTY",
    "LOG_KEYWORD_MISS",
    "LOG_SPAN_SHORT",
    "check_device_log",
    "serial_tool_specs",
]

LOG_EMPTY = "日志为空，请检查断后是否正确连接，此轮执行终止"
LOG_SPAN_SHORT = "从起始点开始日志内容时间不满足5s"
LOG_KEYWORD_MISS = "时间段内未抓到关键字"
_CHECK_WINDOW = timedelta(seconds=5)

LOG_AT_FORMATS = (
    "%Y-%m-%d %H:%M:%S,%f",
    "%H:%M:%S,%f",
    "%Y-%m-%d %H:%M:%S.%f",
    "%H:%M:%S.%f",
    "%Y-%m-%d %H:%M:%S",
    "%H:%M:%S",
)
_TOOL_ORDER = ("check_device_log",)
_LOGGING_LINE = re.compile(
    r"^(?P<stamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})"
    r" - \S+ - (?:DEBUG|INFO|WARNING|ERROR|CRITICAL) - (?P<msg>.*)$"
)


@dataclass(frozen=True)
class _ParsedLog:
    """
    一份日志的已解析快照，用于下一轮只解析新增部分。

    Attributes:
        size: 上次解析时的文件字节数。
        mtime_ns: 上次解析时的修改时间（纳秒），用于发现被改写。
        inode: 文件身份，用于发现轮转；平台取不到时为 0。
        parsed_bytes: 已解析到的字节偏移，总是落在换行之后。
        rows: 已解析出的 (epoch, logging 时间原文, 抓到原文)。
    """

    size: int
    mtime_ns: int
    inode: int
    parsed_bytes: int
    rows: tuple[tuple[float, str, str], ...]


_cache: dict[str, _ParsedLog] = {}
_lock = threading.Lock()


def _local_tz():
    """与 logging 的 asctime 同一套本地时区。"""
    return datetime.now().astimezone().tzinfo


def _parse_log_at(value: str):
    """解析查询时间点。优先认 logging 的逗号毫秒，也接受点号毫秒和只到秒。

    只到秒时按该秒的 `,000`。只给时刻时日期按本地当天。

    Args:
        value: 时间点字符串。

    Returns:
        带本地时区的 `datetime`。

    Raises:
        ValueError: 支持的格式都匹配不上。
    """
    text = (value or "").strip()
    for fmt in LOG_AT_FORMATS:
        try:
            moment = datetime.strptime(text, fmt)
        except ValueError:
            # 当前格式不匹配，继续尝试下一个格式
            continue
        if fmt.startswith("%H"):
            moment = datetime.combine(datetime.now().astimezone().date(), moment.time())
        return moment.replace(tzinfo=_local_tz())

    raise ValueError(
        "时间点无法解析: "
        f"{value!r}；期望 `YYYY-MM-DD HH:MM:SS,mmm`、`YYYY-MM-DD HH:MM:SS`、"
        "`HH:MM:SS,mmm` 或 `HH:MM:SS`"
    )


def _sku_token(sku: str) -> str:
    """型号收成文件名前缀；空串表示没有可用型号。"""
    return re.sub(r"[^0-9A-Za-z_.-]", "", str(sku or "").strip())


def _positive_port(value: object) -> int | None:
    """正整数端口。数字字符串先转成整数；0、负数和非数字返回 None。"""
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value if value > 0 else None
    text = str(value).strip()
    if not text.isdigit():
        return None
    number = int(text)
    return number if number > 0 else None


def _logging_epoch(stamp: str, tz) -> float | None:
    """logging 时间（逗号毫秒）转为 epoch，时区由调用方一次取好传进来。

    Args:
        stamp: 日志行的时间戳原文，形如 `2026-11-04 12:25:15,842`。
        tz: 本地时区对象，每次解析只取一次，避免逐行取时区。

    Returns:
        对应 epoch 秒；时间戳格式不认识时为 None。
    """
    try:
        moment = datetime.strptime(stamp.replace(",", ".", 1), "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return None
    return moment.replace(tzinfo=tz).timestamp()


def _millis(epoch: float) -> int:
    """epoch 收成毫秒，避免浮点比较把恰好落在终点的行判到窗外。"""
    return round(epoch * 1000)


def _parse_tail(path: Path, offset: int) -> tuple[list[tuple[float, str, str]], int]:
    """从字节偏移起解析到最后一个完整行为止。

    Args:
        path: 抓取文件路径。
        offset: 已解析到的字节偏移，必须是换行之后的位置。

    Returns:
        (新增的可解析行, 新的已解析字节位)；结尾没有换行的半行留到下次。
    """
    with path.open("rb") as handle:
        handle.seek(offset)
        chunk = handle.read()
    end = chunk.rfind(b"\n")
    if end < 0:
        return [], offset
    tz = _local_tz()
    rows: list[tuple[float, str, str]] = []
    for raw in chunk[: end + 1].decode("utf-8", errors="replace").splitlines():
        matched = _LOGGING_LINE.match(raw.strip())
        if matched is None:
            continue
        epoch = _logging_epoch(matched.group("stamp"), tz)
        if epoch is None:
            continue
        rows.append((epoch, matched.group("stamp"), matched.group("msg")))
    return rows, offset + end + 1


def _capture_rows(sku: str, port: int) -> list[tuple[float, str, str]]:
    """当前抓取文件的全部可解析行：(epoch, logging 时间原文, 抓到的原文)。

    同一份文件第二次及之后只解析新增的完整行；文件变短、被改写或换了文件身份时
    丢弃缓存按全量重解析，保证结果与「整份解析一次」一致。

    Args:
        sku: 设备型号，决定文件名前缀。
        port: 日志端口。

    Returns:
        按时间升序的可解析行；文件不存在时为空列表。
    """
    path = capture_file_path(sku, port)
    if not path.is_file():
        return []
    stat = path.stat()
    key = str(path)
    inode = _inode(stat)
    with _lock:
        cached = _cache.get(key)
    if (
        cached is not None
        and inode == cached.inode
        and stat.st_size >= cached.size
        and stat.st_mtime_ns >= cached.mtime_ns
    ):
        if stat.st_size == cached.size:
            return list(cached.rows)
        fresh, parsed = _parse_tail(path, cached.parsed_bytes)
        rows = cached.rows + tuple(fresh)
        return _remember(key, stat, inode, parsed, rows)
    fresh, parsed = _parse_tail(path, 0)
    return _remember(key, stat, inode, parsed, tuple(fresh))


def _inode(stat: Any) -> int:
    """文件身份；平台取不到时统一为 0，退化成只比长度与修改时间。"""
    return int(getattr(stat, "st_ino", 0) or 0)


def _remember(
    key: str,
    stat: Any,
    inode: int,
    parsed: int,
    rows: tuple[tuple[float, str, str], ...],
) -> list[tuple[float, str, str]]:
    """把这次的解析结果记进缓存，并返回按时间排好序的行。

    Args:
        key: 文件绝对路径。
        stat: 本次 `Path.stat()` 的结果。
        inode: 文件身份。
        parsed: 已解析到的字节偏移。
        rows: 已解析出的全部行。

    Returns:
        按时间升序的行列表。
    """
    ordered = sorted(rows, key=lambda item: item[0])
    with _lock:
        _cache[key] = _ParsedLog(
            size=int(stat.st_size),
            mtime_ns=int(stat.st_mtime_ns),
            inode=inode,
            parsed_bytes=parsed,
            rows=tuple(ordered),
        )
    return list(ordered)


def _clear_cache() -> None:
    """清空解析缓存；只在测试里用。"""
    with _lock:
        _cache.clear()


def _check_result(
    *,
    timestamp: str = "",
    msg: str = "",
    result: str,
    offset_seconds: float | None = None,
) -> str:
    """验收结论：timestamp / msg / result（命中时附相对起点的偏移秒数）。

    Args:
        timestamp: 命中行的 logging 时间原文。
        msg: 命中行原文或未命中说明。
        result: PASS / FAIL。
        offset_seconds: 命中行相对起点的秒数；负数表示比起点更早。

    Returns:
        JSON 字符串。
    """
    payload: dict[str, object] = {"timestamp": timestamp, "msg": msg, "result": result}
    if offset_seconds is not None:
        payload["offset_seconds"] = offset_seconds
    return json.dumps(payload, ensure_ascii=False)


def check_device_log(
    keyword: str,
    at: str = "",
    sku: str = "",
    port: int | str = 0,
    user_id: str = "",
) -> str:
    """在指定端口的当前抓取文件里检查关键词是否出现在起点之后的 5 秒内。
    文件是 logs/serial_logs/{SKU}_{端口}.log。只匹配抓到的原文（忽略大小写），
    不读其它端口、轮转备份或内存缓冲。
    找到则返回 logging 时间、该行原文、相对起点的偏移秒数（必然 >= 0），result 为 PASS。
    最晚一行已盖满 5 秒但没有关键词时，result 为 FAIL，msg 为「时间段内未抓到关键字」。
    窗口内没有可解析行时中断本轮并说明日志为空。
    窗口内有行、但最晚一行仍早于起点加 5 秒时，中断本轮并说明时间不满足 5 秒。
    缺少关键词、起点、型号或端口时返回 FAIL。
    起点**之前**的行一律不参与匹配：日志只在动作触发之后才出现，更早的行属于上一个动作。
    因此调用方必须把 `at` 给成「触发该日志的那次动作」的时刻，给晚了会整段漏掉。

    Args:
        keyword: 日志关键词原文，例如 switch_off
        at: 起点时间，与 logging 相同：`YYYY-MM-DD HH:MM:SS,mmm`。
            匹配区间是「起点 ~ 起点后 5 秒」，含两端。也可只到秒（按该秒的 `,000`）
        sku: 设备型号，例如 H6810 或 H7011
        port: 日志端口，例如 7005。必须指定，不从平台配置猜测

    Raises:
        ValueError: at 时间点无法解析。
        ValueError: 起点之后没有可解析行（日志为空），中断本轮。
        ValueError: 起点之后的日志还没盖满 5 秒，中断本轮。
    """
    del user_id
    wanted = str(keyword or "").strip()
    port_number = _positive_port(port)
    if not wanted or not str(at or "").strip() or not _sku_token(sku) or port_number is None:
        return _check_result(result="FAIL")

    start = _parse_log_at(at)
    start_ms = _millis(start.timestamp())
    end_ms = _millis((start + _CHECK_WINDOW).timestamp())
    rows = _capture_rows(sku, port_number)
    window = [row for row in rows if start_ms <= _millis(row[0]) <= end_ms]

    # 日志只在动作触发之后才出现：起点之前的行属于上一个动作，不参与本次判定
    needle = wanted.lower()
    for epoch, stamp, msg in window:
        if needle in msg.lower():
            offset = round((_millis(epoch) - start_ms) / 1000, 3)
            return _check_result(
                timestamp=stamp,
                msg=msg,
                result="PASS",
                offset_seconds=offset,
            )

    if not window:
        raise ValueError(LOG_EMPTY)
    if _millis(rows[-1][0]) < end_ms:
        raise ValueError(LOG_SPAN_SHORT)
    return _check_result(msg=LOG_KEYWORD_MISS, result="FAIL")


def serial_tool_specs() -> list[ToolSpec]:
    """按固定顺序产出日志工具的 `ToolSpec` 列表。"""
    impls = {
        "check_device_log": check_device_log,
    }
    return [
        ToolSpec(name=name, handler=impls[name], read_only=True, auto_allow=True)
        for name in _TOOL_ORDER
    ]
