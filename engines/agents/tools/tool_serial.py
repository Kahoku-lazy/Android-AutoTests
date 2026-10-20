"""引擎侧设备日志工具：按型号和端口检查当前抓取文件里有没有关键词。

`check_device_log` 只读 `logs/serial_logs/{SKU}_{端口}.log` 这一份当前文件。
"""

from __future__ import annotations

import json
import re

from datetime import datetime, timedelta

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


def _logging_epoch(stamp: str) -> float | None:
    """logging 时间（逗号毫秒）转为本地时间的 epoch。"""
    try:
        moment = datetime.strptime(stamp.replace(",", ".", 1), "%Y-%m-%d %H:%M:%S.%f")
    except ValueError:
        return None
    return moment.replace(tzinfo=_local_tz()).timestamp()


def _millis(epoch: float) -> int:
    """epoch 收成毫秒，避免浮点比较把恰好落在终点的行判到窗外。"""
    return round(epoch * 1000)


def _capture_rows(sku: str, port: int) -> list[tuple[float, str, str]]:
    """当前抓取文件的全部可解析行：(epoch, logging 时间原文, 抓到的原文)。"""
    path = capture_file_path(sku, port)
    if not path.is_file():
        return []
    rows: list[tuple[float, str, str]] = []
    for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
        matched = _LOGGING_LINE.match(raw.strip())
        if matched is None:
            continue
        stamp = matched.group("stamp")
        epoch = _logging_epoch(stamp)
        if epoch is None:
            continue
        rows.append((epoch, stamp, matched.group("msg")))
    rows.sort(key=lambda item: item[0])
    return rows


def _check_result(*, timestamp: str = "", msg: str = "", result: str) -> str:
    """验收结论：timestamp / msg / result。"""
    return json.dumps(
        {"timestamp": timestamp, "msg": msg, "result": result},
        ensure_ascii=False,
    )


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
    找到则返回 logging 时间、该行原文且 result 为 PASS。
    最晚一行已盖满这 5 秒但没有关键词时，result 为 FAIL，msg 为「时间段内未抓到关键字」。
    起点之后没有可解析行时中断本轮并说明日志为空。
    起点之后有行、但最晚一行仍早于起点加 5 秒时，中断本轮并说明时间不满足 5 秒。
    缺少关键词、起点、型号或端口时返回 FAIL。

    Args:
        keyword: 日志关键词原文，例如 switch_off
        at: 起点时间，与 logging 相同：`YYYY-MM-DD HH:MM:SS,mmm`。
            从这一刻起向后 5 秒，含起点。也可只到秒（按该秒的 `,000`）
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
    after = [row for row in _capture_rows(sku, port_number) if _millis(row[0]) >= start_ms]
    if not after:
        raise ValueError(LOG_EMPTY)

    needle = wanted.lower()
    for epoch, stamp, msg in after:
        if _millis(epoch) <= end_ms and needle in msg.lower():
            return _check_result(timestamp=stamp, msg=msg, result="PASS")
    if _millis(after[-1][0]) < end_ms:
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
