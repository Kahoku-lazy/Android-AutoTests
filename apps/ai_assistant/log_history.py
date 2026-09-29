"""设备日志「历史取证」—— 按给定时刻从日志文件回溯切出证据块（调试台用）。

模型调试台里的验收对话没有「本步动作」这个概念：点击往往发生在几分钟前，早于内存缓冲的
保留时长（`DEVICE_LOG_BUFFER_SECONDS`，默认 10 分钟），所以只能从 `device-log-file-archive`
落盘的日志文件里回溯取窗。

切窗、命中判定、等级与合并口径**全部复用** `engines.device.logbus.build_evidence`
（与任务链路同一份真相源），本模块只做三件事：识别基准时刻、定位并解析日志文件、
按基准算出入参。

无端口在监听 / 文件缺失或不可读 / 窗口内确实没有日志时如实返回空证据，MUST NOT 打开端口、
MUST NOT 用别的时段或别的设备的日志顶替。
"""

from __future__ import annotations

import logging
import re

from datetime import timedelta
from typing import Any

from django.conf import settings

from apps.ai_assistant.log_evidence import source_specs
from engines.device.logbus import (
    DEFAULT_BASELINE_SECONDS,
    DEFAULT_WINDOW_SECONDS,
    KeywordIndex,
    LogLine,
    build_evidence,
    format_stamp,
    now_stamp,
    parse_stamp,
)
from engines.device.logfiles import log_file_path, parse_log_line, tail_lines

logger = logging.getLogger("ai_assistant.log_history")

__all__ = [
    "BASIS_PATTERN",
    "HISTORY_TAIL_LINES",
    "extract_basis_time",
    "history_evidence",
    "keyword_catalog_text",
]

# 基准时刻：北京时间毫秒（与采集层写入日志文件的时间戳同一格式）
BASIS_PATTERN = re.compile(r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}")

# 尾部读取行数：一次 5 秒取证窗的行数远小于它；读不到更早的行时如实给「窗口内无日志」
HISTORY_TAIL_LINES = 20000

NOTE_NO_DIR = "日志目录未配置或不存在"
NOTE_NO_FILE = "该端口的日志文件不存在"
NOTE_NO_LOG = "窗口内无日志"
NOTE_NO_SOURCE = "没有登记任何日志端口来源"
NOTE_NO_LISTEN = "日志端口都未开启监听（平台不会为调试打开端口）"


def extract_basis_time(text: str) -> str:
    """取文本里**第一个**北京时间毫秒时间戳作为取证基准；没有则返回空串。

    调试验收时用户会把执行模型的回复（含点击时刻）贴进来，基准天然就在消息里；
    取第一个是确定且可解释的口径（响应里会把实际用到的基准回显出来）。
    """
    matched = BASIS_PATTERN.search(str(text or ""))
    return matched.group(0) if matched else ""


def _shift(stamp: str, seconds: float) -> str:
    """时间戳平移若干秒；解析失败原样返回。"""
    moment = parse_stamp(stamp)
    if moment is None:
        return stamp
    return format_stamp(moment + timedelta(seconds=seconds))


def _read_lines(path, channel: str, limit: int) -> list[LogLine]:
    """日志文件 → 带 epoch 的行对象（与采集层同一字段口径，供 build_evidence 复用）。"""
    rows: list[LogLine] = []
    for raw in tail_lines(path, limit):
        parsed = parse_log_line(raw)
        if parsed is None:
            continue
        moment = parse_stamp(parsed.timestamp)
        if moment is None:
            continue
        rows.append(
            LogLine(
                channel=channel,
                timestamp=parsed.timestamp,
                epoch=moment.timestamp(),
                source=parsed.source,
                text=parsed.text,
            )
        )
    return rows


def keyword_catalog_text() -> str:
    """当前日志关键词表 → 给验收模型看的「关键词 → 功能点」对照文本（取不到返回空串）。

    取自运行中的采集索引（`DEVICE_LOG_KEYWORD_FILE`），MUST NOT 写死在提示词里：
    关键词表改了以后不需要改提示词。读取失败/未配置时返回空串，由调用方如实不附。
    """
    index = _keywords()
    mapping = index.mapping
    if not mapping:
        return ""
    lines = [
        "本平台日志关键词表（检查日志时从这里选关键词，报给 check_device_log）：",
    ]
    for keyword, features in mapping.items():
        marks = "、".join(
            f"#{item.get('id')} {item.get('module')}-{item.get('feature')}"
            for item in features or []
        )
        lines.append(f"  - {keyword} → {marks}" if marks else f"  - {keyword}")
    return "\n".join(lines)


def _capture_available(explicit: bool | None) -> bool:
    """采集是否可用：显式给了就用它，否则问「采集总闸 + 端口监听开关」当前状态。"""
    if explicit is not None:
        return bool(explicit)
    from apps.ai_assistant.api import get_log_port_enabled_map

    if not bool(getattr(settings, "DEVICE_LOG_ENABLED", False)):
        return False
    states = get_log_port_enabled_map()
    return any(states.values()) if states else True


def _keywords() -> KeywordIndex:
    return KeywordIndex.from_file(str(getattr(settings, "DEVICE_LOG_KEYWORD_FILE", "") or ""))


def history_evidence(
    basis_time: str = "",
    *,
    window_seconds: float = 0.0,
    baseline_seconds: float = 0.0,
    tail_limit: int = HISTORY_TAIL_LINES,
    capture_enabled: bool | None = None,
) -> dict[str, Any]:
    """按基准时刻从日志文件回溯切出证据块（与任务链路同一份判定口径）。

    Args:
        basis_time: 取证基准时刻（北京时间毫秒）。调用方从消息里识别到的时刻就传这里；
            空串时以「最近一个取证窗」为基准（取证窗 = 最新 threshold 秒），
            并在返回里标 `from_message=False`。
        window_seconds: 取证阈值；0 取平台配置。
        baseline_seconds: 动作前基线长度；0 取平台配置。
        tail_limit: 每个端口最多回读的日志行数。
        capture_enabled: 采集是否可用（总闸 + 端口监听开关）。None 表示问平台当前状态；
            显式传 False（例如单测、或调用方已判定不可用）时不读文件、如实说明。

    Returns:
        {"basis_time", "from_message", "files", "evidence"（build_evidence 结果或 None）, "note"}
        `note` 为空串表示取到了窗口日志；否则是如实原因（窗口内无日志 / 文件不存在 …）。
    """
    threshold = float(
        window_seconds or getattr(settings, "DEVICE_LOG_WINDOW_SECONDS", DEFAULT_WINDOW_SECONDS)
    )
    baseline = float(
        baseline_seconds
        or getattr(settings, "DEVICE_LOG_BASELINE_SECONDS", DEFAULT_BASELINE_SECONDS)
    )
    from_message = bool(extract_basis_time(basis_time))
    if from_message:
        basis = extract_basis_time(basis_time)
    else:
        # 最近一个取证窗：窗口右端 = 现在，左端 = 现在 − 阈值
        moment = parse_stamp(now_stamp())
        basis = format_stamp(moment - timedelta(seconds=threshold)) if moment else ""

    directory = str(getattr(settings, "DEVICE_LOG_LOG_DIR", "") or "")
    specs = source_specs()
    if not specs:
        return _empty(basis, from_message, [], NOTE_NO_SOURCE)
    if not _capture_available(capture_enabled):
        # 监听开关归用户：关着就不取证据、也不替他打开端口（与生产同口径）
        return _empty(basis, from_message, [], NOTE_NO_LISTEN)
    if not directory:
        return _empty(basis, from_message, [], NOTE_NO_DIR)

    keywords = _keywords()
    basis_moment = parse_stamp(basis)
    basis_epoch = basis_moment.timestamp() if basis_moment else None
    # 只把「动作前基线 ~ 窗口末端后一小段」的行喂给判定：多余的尾行会让
    # build_evidence 把窗口后的行也算进 window_line_count，让「窗口内无日志」判不出来；
    # 留一段（再一个阈值）是为了仍能识别「超窗」的命中。
    low = basis_epoch - baseline if basis_epoch is not None else None
    high = basis_epoch + threshold * 2 if basis_epoch is not None else None

    files: list[str] = []
    best: dict | None = None
    best_rank = -1
    for spec in specs:
        path = log_file_path(directory, spec.sku, spec.port)
        rows = _read_lines(path, spec.channel, tail_limit)
        if rows:
            files.append(str(path).replace("\\", "/"))
        if not rows:
            logger.info("历史取证：端口 %s 没有可用日志行（file=%s）", spec.port, path)
        elif low is not None and high is not None:
            rows = [row for row in rows if low <= row.epoch <= high]
        evidence = build_evidence(
            channel=spec.channel,
            window_id="model-debug-history",
            window_opened_at=_shift(basis, -baseline),
            lines=rows,
            keywords=keywords,
            action_times=[basis],
            threshold_seconds=threshold,
            baseline_seconds=baseline,
        )
        # 有命中的端口优先；其次有窗口日志的端口；都没有就留一份空结论
        rank = 2 if evidence["hits"] else (1 if evidence["window_line_count"] else 0)
        if rank > best_rank:
            best, best_rank = evidence, rank
        if best_rank == 2:
            break

    note = "" if best and best["window_line_count"] else NOTE_NO_LOG
    if not files and not (best and best["window_line_count"]):
        note = NOTE_NO_FILE
    return {
        "basis_time": basis,
        "from_message": from_message,
        "files": files,
        "evidence": best,
        "note": note,
    }


def _empty(basis: str, from_message: bool, files: list[str], note: str) -> dict[str, Any]:
    return {
        "basis_time": basis,
        "from_message": from_message,
        "files": files,
        "evidence": None,
        "note": note,
    }
