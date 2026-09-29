"""灰盒·单元测试 — 设备日志只读查询工具（变更 add-device-log-read-tool）。

零设备、零真实端口（用 tcp_port=0 的假总线 + 直接 feed）：
覆盖端口维度与来源登记、时间点「之后一个跨度」语义、跨度钳制、关键词过滤与功能点还原、
四种失败口径（未配置端口 / 已关闭监听 / 无日志 / 无关键词命中）、工具箱登记与执行模型装配。
"""

from __future__ import annotations

import json
import time

from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from django.test import override_settings

from apps.ai_assistant.tools import (
    LOG_SPAN_DEFAULT_SECONDS,
    LOG_SPAN_MAX_SECONDS,
    _clamp_log_span,
    _parse_log_at,
    list_tool_schemas,
    read_device_log,
)
from engines.ai.agents.config import VERIFIER_TOOLS, VISION_TOOLS
from engines.device.logbus import (
    BEIJING_TZ,
    LogBus,
    LogBusConfig,
    LogSourceUnknown,
    now_stamp,
    start_log_bus,
    stop_log_bus,
)

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

SKU_CHANNEL = "H6810"
TOOL_NAME = "read_device_log"
REPO_ROOT = Path(__file__).resolve().parents[3]
KEYWORD_FILE = REPO_ROOT / "config" / "device_log_keywords.json"


@pytest.fixture
def bus():
    """装一个真实但不起采集线程的总线（tcp_port=0），供工具读取。"""
    instance = start_log_bus(
        LogBusConfig(
            enabled=True,
            tcp_port=0,
            channel=SKU_CHANNEL,
            source_channels={7005: SKU_CHANNEL, 9100: "H6199"},
            keyword_file=str(KEYWORD_FILE),
        )
    )
    try:
        yield instance
    finally:
        stop_log_bus()


def _payload(result: str) -> dict:
    return json.loads(result)


# ── 1.1 / 1.2 / 1.3 端口维度与来源登记 ───────────────────────


def test_line_records_source_port() -> None:
    """日志行记录来源端口，可按端口区分。"""
    instance = LogBus(LogBusConfig(enabled=True, tcp_port=0, channel=SKU_CHANNEL))
    instance.feed("from-7005", port=7005)
    instance.feed("from-9100", port=9100)
    ports = {item["text"]: item["port"] for item in instance.snapshot()}
    assert ports == {"from-7005": 7005, "from-9100": 9100}


def test_configured_ports_fall_back_to_single_source() -> None:
    """未显式登记来源时，退化为「配置端口 → 默认通道」一条。"""
    instance = LogBus(
        LogBusConfig(enabled=True, tcp_port=7005, channel=SKU_CHANNEL, source_channels={})
    )
    assert instance.configured_ports() == [7005]
    assert instance.channel_for_port(7005) == SKU_CHANNEL


def test_unknown_port_raises_readable_message() -> None:
    """总线层：查未登记端口抛可读错误（消息只说明端口未配置）。"""
    instance = LogBus(LogBusConfig(enabled=True, tcp_port=0, source_channels={7005: SKU_CHANNEL}))
    with pytest.raises(LogSourceUnknown) as excinfo:
        instance.channel_for_port(9100)
    assert str(excinfo.value) == "端口 9100 未配置为日志来源"


# ── 2.2 时间点解析 ───────────────────────────────────────────


def test_parse_log_at_full_stamp() -> None:
    moment = _parse_log_at("2026-09-28 13:05:37.500")
    assert moment.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] == "2026-09-28 13:05:37.500"
    assert moment.utcoffset() == timedelta(hours=8)


def test_parse_log_at_time_only_uses_today() -> None:
    moment = _parse_log_at("13:05:37.500")
    today = datetime.now(BEIJING_TZ).date()
    assert moment.date() == today
    assert moment.hour == 13 and moment.minute == 5


def test_parse_log_at_rejects_garbage() -> None:
    with pytest.raises(ValueError) as excinfo:
        _parse_log_at("昨天下午")
    assert "YYYY-MM-DD HH:MM:SS.mmm" in str(excinfo.value)


# ── 2.3 跨度语义与钳制 ───────────────────────────────────────


def test_span_default_and_cap() -> None:
    assert _clamp_log_span(0) == LOG_SPAN_DEFAULT_SECONDS
    assert _clamp_log_span(60) == 60
    assert _clamp_log_span(99999) == LOG_SPAN_MAX_SECONDS


def test_at_returns_window_after_the_moment(bus) -> None:
    """B 口径：给 at 时返回「该时刻之后」一个跨度，之前的行不算。"""
    bus.feed("before-moment", port=7005, channel=SKU_CHANNEL)
    time.sleep(0.02)  # 让时钟走一格，避免毫秒截断把「之前」并进来
    moment = now_stamp()
    bus.feed("after-moment", port=7005, channel=SKU_CHANNEL)

    payload = _payload(read_device_log(at=moment, seconds=30, port=7005))
    texts = [line["text"] for line in payload["lines"]]
    assert texts == ["after-moment"]
    assert payload["query"]["from"] == moment
    assert payload["conclusion"] == "ok"


def test_without_at_returns_recent_span(bus) -> None:
    """不给 at → 最近一个跨度。"""
    bus.feed("recent-line", port=7005, channel=SKU_CHANNEL)
    payload = _payload(read_device_log(seconds=30, port=7005))
    assert [line["text"] for line in payload["lines"]] == ["recent-line"]


# ── 2.4 关键词过滤与功能点还原 ───────────────────────────────


def test_keyword_filter_restores_feature(bus) -> None:
    """按关键词过滤（忽略大小写）并还原功能点编号。"""
    bus.feed("[light_switch][I]: switch_off", port=7005, channel=SKU_CHANNEL)
    bus.feed("ram free heap size: 1", port=7005, channel=SKU_CHANNEL)
    payload = _payload(read_device_log(seconds=30, port=7005, keyword="SWITCH_OFF"))
    assert [line["text"] for line in payload["lines"]] == ["[light_switch][I]: switch_off"]
    assert payload["keyword_hits"][0]["keyword"] == "switch_off"
    assert {item["id"] for item in payload["keyword_hits"][0]["features"]} == {1}


# ── 2.5 三种失败口径 ─────────────────────────────────────────


def test_unregistered_port_returns_readable_conclusion(bus) -> None:
    """未配置端口不报错：返回「端口 X 未配置为日志来源」，结论字段可区分。"""
    payload = _payload(read_device_log(seconds=30, port=9999))
    assert payload["conclusion"] == "port_not_configured"
    assert payload["note"] == "端口 9999 未配置为日志来源"
    assert payload["line_count"] == 0
    assert payload["lines"] == []
    assert payload["query"]["port"] == 9999


@pytest.mark.parametrize("port", [7004, 7003])
def test_unregistered_port_message_carries_the_requested_port(bus, port: int) -> None:
    """提示里的端口号是调用方传的那个（7004/7003 各自成句）。"""
    payload = _payload(read_device_log(seconds=10, port=port))
    assert payload["note"] == f"端口 {port} 未配置为日志来源"


def test_empty_range_says_no_log(bus) -> None:
    payload = _payload(read_device_log(at="2000-01-01 00:00:00.000", seconds=10, port=7005))
    assert payload["line_count"] == 0
    assert payload["conclusion"] == "no_log"
    assert "无日志" in payload["note"]


def test_keyword_without_hit_says_so(bus) -> None:
    bus.feed("ram free heap size: 1", port=7005, channel=SKU_CHANNEL)
    payload = _payload(read_device_log(seconds=30, port=7005, keyword="switch_on"))
    assert payload["line_count"] == 0
    assert payload["conclusion"] == "no_keyword_hit"
    assert "switch_on" in payload["note"]


# ── 同一时刻合并（需求方口径：相同时间点合在一起，保留换行）─────────

SAME_MS = "2026-09-28 15:47:41.466"
SAME_MS_TEXTS = (
    "[system] D name light_switch event is 0",
    "[system] D name light_switch start",
    "[light_switch][I]: switch_off",
)


def _same_ms_lines(source: str = "tcp"):
    from engines.device.logbus import LogLine, parse_stamp

    moment = parse_stamp(SAME_MS)
    assert moment is not None
    return [
        LogLine(
            channel=SKU_CHANNEL,
            timestamp=SAME_MS,
            epoch=moment.timestamp(),
            source=source,
            text=text,
            port=7005,
        )
        for text in SAME_MS_TEXTS
    ]


def test_merge_same_timestamp_keeps_newlines() -> None:
    """同一时间戳 + 同一来源 → 合并成一条，text 内保留换行。"""
    from engines.device.logbus import merge_lines_by_timestamp

    merged = merge_lines_by_timestamp(_same_ms_lines())
    assert len(merged) == 1
    assert merged[0]["timestamp"] == SAME_MS
    assert merged[0]["source"] == "tcp"
    assert merged[0]["text"] == "\n".join(SAME_MS_TEXTS)


def test_merge_keeps_different_timestamps_apart() -> None:
    """时间戳不同不合并，且**最新时间排在最上面**。"""
    from engines.device.logbus import LogLine, merge_lines_by_timestamp, parse_stamp

    merged = merge_lines_by_timestamp(
        [
            _same_ms_lines()[0],
            LogLine(
                channel=SKU_CHANNEL,
                timestamp="2026-09-28 15:47:41.467",
                epoch=parse_stamp("2026-09-28 15:47:41.467").timestamp(),  # type: ignore[union-attr]
                source="tcp",
                text="later",
                port=7005,
            ),
        ]
    )
    # 倒序：晚的在前
    assert [item["text"] for item in merged] == ["later", SAME_MS_TEXTS[0]]


def test_lines_sorted_newest_first() -> None:
    """三行不同时刻 → 返回顺序为最新在上（与查询范围无关，始终倒序）。"""
    from engines.device.logbus import LogLine, merge_lines_by_timestamp, parse_stamp

    stamps = ["2026-09-28 15:47:41.100", "2026-09-28 15:47:43.100", "2026-09-28 15:47:42.100"]
    lines = [
        LogLine(
            channel=SKU_CHANNEL,
            timestamp=stamp,
            epoch=parse_stamp(stamp).timestamp(),  # type: ignore[union-attr]
            source="tcp",
            text=f"line-{stamp[-8:]}",
            port=7005,
        )
        for stamp in stamps
    ]
    merged = merge_lines_by_timestamp(lines)
    assert [item["timestamp"] for item in merged] == sorted(stamps, reverse=True)


def test_merged_entry_keeps_inner_order() -> None:
    """同一条内部仍按原始先后（那一刻的经过不能倒着读）。"""
    from engines.device.logbus import merge_lines_by_timestamp

    merged = merge_lines_by_timestamp(_same_ms_lines())
    assert merged[0]["text"].split("\n") == list(SAME_MS_TEXTS)


def test_merge_keeps_different_sources_apart() -> None:
    """同一时间戳但来源不同不合并（避免混淆 tcp / serial）。"""
    from engines.device.logbus import merge_lines_by_timestamp

    merged = merge_lines_by_timestamp(_same_ms_lines("tcp") + _same_ms_lines("serial"))
    assert {(item["timestamp"], item["source"]) for item in merged} == {
        (SAME_MS, "tcp"),
        (SAME_MS, "serial"),
    }


def test_tool_output_merges_same_timestamp(bus, monkeypatch) -> None:
    """工具返回：同毫秒的三行合成一条，并同时给出原始行数。"""
    lines = _same_ms_lines()
    monkeypatch.setattr(
        bus, "read_range", lambda **_kwargs: {"channel": SKU_CHANNEL, "port": 7005, "lines": lines}
    )
    payload = _payload(read_device_log(seconds=30, port=7005))
    assert payload["line_count"] == 1
    assert payload["raw_line_count"] == 3
    assert payload["lines"][0]["text"] == "\n".join(SAME_MS_TEXTS)


def test_evidence_merges_same_timestamp() -> None:
    """验收证据里的窗口日志同样合并（同一时刻一条，text 内保留换行）。"""
    from engines.device.logbus import KeywordIndex, build_evidence

    evidence = build_evidence(
        channel=SKU_CHANNEL,
        window_id="w1",
        window_opened_at="2026-09-28 15:47:41.000",
        lines=_same_ms_lines(),
        keywords=KeywordIndex(
            {"switch_off": [{"id": 1, "module": "设备开关", "feature": "关闭设备成功"}]}
        ),
        action_time="2026-09-28 15:47:41.400",
        threshold_seconds=5.0,
        baseline_seconds=30.0,
    )
    assert evidence["window_line_count"] == 3  # 原始行数不变
    assert len(evidence["lines"]) == 1  # 展示按同刻合并
    assert evidence["lines"][0]["text"] == "\n".join(SAME_MS_TEXTS)
    assert evidence["hits"][0]["keyword"] == "switch_off"


# ── 3.1 工具箱登记 ───────────────────────────────────────────


def test_tool_is_registered_in_toolbox() -> None:
    """工具箱里可见、分类为「设备日志」、标记只读，且摘要写清用途。"""
    rows = {row["name"]: row for row in list_tool_schemas()}
    assert TOOL_NAME in rows
    row = rows[TOOL_NAME]
    assert row["category"] == "设备日志"
    assert row["read_only"] is True
    assert row["module"] == "log" and row["action"] == "read"
    assert "日志" in row["summary"]


# ── 3.2 执行模型装配（验收模型改用按规则检查的工具）──────────


def test_tool_is_mounted_for_executor_only() -> None:
    """通用查询工具只给执行模型；验收模型用的是按关键词规则检查的工具。"""
    assert TOOL_NAME in VISION_TOOLS
    assert TOOL_NAME not in VERIFIER_TOOLS
    assert VERIFIER_TOOLS == ["screenshot_page", "check_device_log"]


# ── 只读性：不触碰设备与数据库 ───────────────────────────────
def test_tool_reads_disk_history_when_buffer_misses(tmp_path, settings) -> None:
    """缓冲里没有的时段（例如十几分钟前）：工具从已落盘的日志文件回溯取到，并标出取数来源。"""
    settings.DEVICE_LOG_SOURCES = ""
    start_log_bus(
        LogBusConfig(
            enabled=True,
            tcp_port=0,
            channel=SKU_CHANNEL,
            source_channels={7005: SKU_CHANNEL},
            keyword_file=str(KEYWORD_FILE),
            log_dir=str(tmp_path),
        )
    )
    try:
        (tmp_path / f"{SKU_CHANNEL}_7005.log").write_text(
            "2026-09-29 11:47:04.687 [tcp] [light_switch][I]: switch_on\n", encoding="utf-8"
        )
        payload = _payload(read_device_log(at="2026-09-29 11:47:04.000", seconds=5, port=7005))
    finally:
        stop_log_bus()

    assert payload["conclusion"] == "ok"
    assert payload["sources"] == {"buffer_lines": 0, "file_lines": 1}
    assert "switch_on" in payload["lines"][0]["text"]


def test_tool_no_log_note_no_longer_blames_buffer(tmp_path, settings) -> None:
    """确实没有日志时，结论不再暗示「可能超出缓冲保留时长」（已回溯落盘文件）。"""
    settings.DEVICE_LOG_SOURCES = ""
    start_log_bus(
        LogBusConfig(
            enabled=True,
            tcp_port=0,
            channel=SKU_CHANNEL,
            source_channels={7005: SKU_CHANNEL},
            keyword_file=str(KEYWORD_FILE),
            log_dir=str(tmp_path),
        )
    )
    try:
        payload = _payload(read_device_log(at="2026-09-29 11:47:04.000", seconds=5, port=7005))
    finally:
        stop_log_bus()

    assert payload["conclusion"] == "no_log"
    assert "缓冲保留时长" not in payload["note"]


def test_tool_source_has_no_write_or_device_calls() -> None:
    """工具实现不调设备引擎、不写库、不建连接（源码级只读契约）。"""
    import inspect

    from apps.ai_assistant import tools as tools_module

    source = inspect.getsource(tools_module.read_device_log)
    for forbidden in ("open_engine", "use_device", ".save(", "objects.create", "socket."):
        assert forbidden not in source, f"只读工具里不应出现 {forbidden}"


def test_disabled_collection_raises_readable_error() -> None:
    """采集关闭时给可读错误，而不是空结果。"""
    stop_log_bus()
    with override_settings(DEVICE_LOG_ENABLED=False):
        with pytest.raises(ValueError) as excinfo:
            read_device_log(at="13:05:37.500", seconds=10)
    assert "日志采集未启动" in str(excinfo.value)
    # 时区常量仍可用（供时间解析）
    assert datetime.now(timezone.utc).year >= 2026


# ── 监听开关关闭态（变更 add-device-log-port-console）─────────


def test_disabled_port_returns_readable_conclusion(bus) -> None:
    """已登记但开关关闭 → 可读结论「端口 X 已关闭监听」，行数 0、不报错。"""
    from apps.ai_assistant import api

    api.set_log_port_enabled(7005, False)
    payload = _payload(read_device_log(seconds=30, port=7005))
    assert payload["conclusion"] == "port_disabled"
    assert payload["note"] == "端口 7005 已关闭监听"
    assert payload["line_count"] == 0 and payload["lines"] == []


def test_disabled_default_port_is_also_reported(bus) -> None:
    """不传端口（走平台默认端口）时同样拿到关闭态结论。"""
    from apps.ai_assistant import api

    api.set_log_port_enabled(7005, False)
    payload = _payload(read_device_log(seconds=30))
    assert payload["conclusion"] == "port_disabled"
    assert "已关闭监听" in payload["note"]


def test_query_does_not_start_collection(bus) -> None:
    """查询本身 MUST NOT 打开被关掉的端口（只读契约）。"""
    from apps.ai_assistant import api

    api.set_log_port_enabled(7005, False)
    read_device_log(seconds=10, port=7005)
    read_device_log(seconds=10)
    assert bus.running_ports() == []
    assert api.is_log_port_enabled(7005) is False


def test_reopened_port_returns_logs_again(bus) -> None:
    """开关重新打开后恢复返回日志，不再给关闭态结论。"""
    from apps.ai_assistant import api

    api.set_log_port_enabled(7005, False)
    assert _payload(read_device_log(seconds=30, port=7005))["conclusion"] == "port_disabled"

    api.set_log_port_enabled(7005, True)
    bus.feed("after-reopen", port=7005, channel=SKU_CHANNEL)
    payload = _payload(read_device_log(seconds=30, port=7005))
    assert payload["conclusion"] == "ok"
    assert [line["text"] for line in payload["lines"]] == ["after-reopen"]
