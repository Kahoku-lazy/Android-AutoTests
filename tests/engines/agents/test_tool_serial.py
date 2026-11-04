"""
单文件调试指令：python -m pytest tests/engines/agents/test_tool_serial.py -vv --tb=short

本文件覆盖日志检查工具的解析缓存（纯单测，用临时文件，不连设备、不读真实日志）：

1. test_check_* —— 命中 / 未命中但已盖满窗口 / 窗口内没日志 / 盖不满 5 秒四条既有语义。
2. test_incremental_* —— 第二次检查只从上次的字节偏移继续解析，且结果与全量解析一致。
3. test_partial_line_* —— 结尾没有换行的半行留到下次，不参与本次判定。
4. test_truncated_* / test_rotated_* —— 文件变短或换掉文件身份时回退全量，不沿用旧行。
5. test_missing_file_* —— 文件不存在时返回空，不抛错。
"""

from __future__ import annotations

import pytest

from engines.agents.tools import tool_serial

pytestmark = pytest.mark.unit

_SKU = "H6810"
_PORT = 7005
_AT = "2026-11-04 12:25:15"


def _line(stamp: str, message: str, level: str = "INFO") -> str:
    """拼一行与采集器格式一致的日志。"""
    return f"{stamp} - root - {level} - {message}"


def _write(path, lines: list[str], *, trailing_newline: bool = True) -> None:
    """写日志文件；`trailing_newline=False` 用来模拟正在写入的半行。"""
    text = "\n".join(lines)
    if trailing_newline and text:
        text += "\n"
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def logfile(tmp_path, monkeypatch: pytest.MonkeyPatch):
    """把抓取文件路径指到临时目录，并清空解析缓存。"""
    path = tmp_path / "H6810_7005.log"
    monkeypatch.setattr(tool_serial, "capture_file_path", lambda _sku, _port: path)
    tool_serial._clear_cache()
    return path


def test_check_finds_keyword_inside_window(logfile) -> None:
    """命中窗口内的关键词时返回 PASS 与该行原文。"""
    _write(
        logfile,
        [
            _line("2026-11-04 12:25:14,900", "before_window"),
            _line("2026-11-04 12:25:16,120", "timer_configs_set_success"),
        ],
    )

    payload = tool_serial.check_device_log("timer_configs_set_success", at=_AT, sku=_SKU, port=_PORT)

    assert '"result": "PASS"' in payload
    assert "2026-11-04 12:25:16,120" in payload
    assert "timer_configs_set_success" in payload


def test_check_reports_fail_when_window_has_no_keyword(logfile) -> None:
    """窗口已盖满但没有关键词时返回 FAIL，不抛错。"""
    _write(
        logfile,
        [
            _line("2026-11-04 12:25:16,000", "other_event"),
            _line("2026-11-04 12:25:21,000", "later_event"),
        ],
    )

    payload = tool_serial.check_device_log("timer_configs_set_success", at=_AT, sku=_SKU, port=_PORT)

    assert tool_serial.LOG_KEYWORD_MISS in payload
    assert '"result": "FAIL"' in payload


def test_check_ignores_keyword_before_start(logfile) -> None:
    """起点之前的行属于上一个动作，不参与本次判定。"""
    _write(
        logfile,
        [
            _line("2026-11-04 12:25:11,000", "timer_configs_set_success"),
            _line("2026-11-04 12:25:16,000", "heartbeat"),
            _line("2026-11-04 12:25:20,000", "heartbeat2"),
        ],
    )

    payload = tool_serial.check_device_log("timer_configs_set_success", at=_AT, sku=_SKU, port=_PORT)

    assert tool_serial.LOG_KEYWORD_MISS in payload
    assert '"result": "FAIL"' in payload


def test_check_passes_when_capture_stalled_right_after_keyword(logfile) -> None:
    """抓取在命中行之后中断、窗口没盖满时，只要窗口内已命中就判通过。"""
    _write(logfile, [_line("2026-11-04 12:25:16,000", "timer_configs_set_success")])

    payload = tool_serial.check_device_log("timer_configs_set_success", at=_AT, sku=_SKU, port=_PORT)

    assert '"result": "PASS"' in payload
    assert '"offset_seconds": 1.0' in payload


def test_check_reports_positive_offset_inside_window(logfile) -> None:
    """窗口内命中时偏移为正，口径是「起点之后多少秒」。"""
    _write(
        logfile,
        [
            _line("2026-11-04 12:25:17,500", "timer_configs_set_success"),
            _line("2026-11-04 12:25:21,000", "heartbeat"),
        ],
    )

    payload = tool_serial.check_device_log("timer_configs_set_success", at=_AT, sku=_SKU, port=_PORT)

    assert '"result": "PASS"' in payload
    assert '"offset_seconds": 2.5' in payload


def test_check_raises_when_no_log_after_start(logfile) -> None:
    """起点之后没有任何行时中断本轮。"""
    _write(logfile, [_line("2026-11-04 12:25:10,000", "too_early")])

    with pytest.raises(ValueError) as excinfo:
        tool_serial.check_device_log("timer_configs_set_success", at=_AT, sku=_SKU, port=_PORT)

    assert str(excinfo.value) == tool_serial.LOG_EMPTY


def test_check_raises_when_window_not_covered(logfile) -> None:
    """起点之后的行还没盖满 5 秒时中断本轮。"""
    _write(logfile, [_line("2026-11-04 12:25:16,000", "only_one_line")])

    with pytest.raises(ValueError) as excinfo:
        tool_serial.check_device_log("timer_configs_set_success", at=_AT, sku=_SKU, port=_PORT)

    assert str(excinfo.value) == tool_serial.LOG_SPAN_SHORT


def test_incremental_second_call_starts_at_previous_offset(
    logfile, monkeypatch: pytest.MonkeyPatch
) -> None:
    """第二次检查从上次解析到的字节位继续，不再从 0 开始。"""
    _write(logfile, [_line("2026-11-04 12:25:16,000", "first")])
    tool_serial._capture_rows(_SKU, _PORT)
    first_offset = logfile.stat().st_size

    offsets: list[int] = []
    original = tool_serial._parse_tail

    def spy(path, offset):
        offsets.append(offset)
        return original(path, offset)

    monkeypatch.setattr(tool_serial, "_parse_tail", spy)
    _write(
        logfile,
        [
            _line("2026-11-04 12:25:16,000", "first"),
            _line("2026-11-04 12:25:17,000", "second"),
        ],
    )

    rows = tool_serial._capture_rows(_SKU, _PORT)

    assert offsets == [first_offset]
    assert [message for _, _, message in rows] == ["first", "second"]


def test_incremental_result_matches_full_parse(logfile) -> None:
    """增量解析与「整份解析一次」逐行一致。"""
    _write(
        logfile,
        [
            _line("2026-11-04 12:25:16,000", "first"),
            _line("2026-11-04 12:25:17,000", "second"),
        ],
    )
    tool_serial._capture_rows(_SKU, _PORT)
    _write(
        logfile,
        [
            _line("2026-11-04 12:25:16,000", "first"),
            _line("2026-11-04 12:25:17,000", "second"),
            _line("2026-11-04 12:25:18,000", "third"),
        ],
    )

    incremental = tool_serial._capture_rows(_SKU, _PORT)
    full, _parsed = tool_serial._parse_tail(logfile, 0)

    assert incremental == full


def test_incremental_keeps_old_rows_queryable(logfile) -> None:
    """已解析过的行仍能被后续查询命中（窗口落在旧区间）。"""
    _write(logfile, [_line("2026-11-04 12:25:16,120", "timer_configs_set_success")])
    tool_serial.check_device_log("timer_configs_set_success", at=_AT, sku=_SKU, port=_PORT)
    _write(
        logfile,
        [
            _line("2026-11-04 12:25:16,120", "timer_configs_set_success"),
            _line("2026-11-04 12:25:20,000", "after"),
        ],
    )

    payload = tool_serial.check_device_log("timer_configs_set_success", at=_AT, sku=_SKU, port=_PORT)

    assert '"result": "PASS"' in payload


def test_partial_line_is_left_for_next_round(logfile) -> None:
    """结尾没有换行的半行不参与判定，补上换行后才被解析。"""
    _write(
        logfile,
        [
            _line("2026-11-04 12:25:16,000", "first"),
            _line("2026-11-04 12:25:16,500", "timer_configs_set_succ"),
        ],
        trailing_newline=False,
    )

    tool_serial._capture_rows(_SKU, _PORT)
    assert [message for _, _, message in tool_serial._capture_rows(_SKU, _PORT)] == ["first"]

    _write(
        logfile,
        [
            _line("2026-11-04 12:25:16,000", "first"),
            _line("2026-11-04 12:25:16,500", "timer_configs_set_success"),
        ],
    )

    messages = [message for _, _, message in tool_serial._capture_rows(_SKU, _PORT)]
    assert messages == ["first", "timer_configs_set_success"]


def test_truncated_file_falls_back_to_full_parse(logfile) -> None:
    """文件变短（被截断重写）时丢弃缓存，只按新内容判定。"""
    _write(
        logfile,
        [
            _line("2026-11-04 12:25:16,000", "old_row"),
            _line("2026-11-04 12:25:17,000", "old_row_2"),
        ],
    )
    tool_serial._capture_rows(_SKU, _PORT)
    _write(logfile, [_line("2026-11-04 12:25:18,000", "new_row")])

    rows = tool_serial._capture_rows(_SKU, _PORT)

    assert [message for _, _, message in rows] == ["new_row"]


def test_rotated_file_falls_back_to_full_parse(logfile) -> None:
    """文件身份变化（轮转）时丢弃缓存，不沿用旧行。"""
    _write(logfile, [_line("2026-11-04 12:25:16,000", "old_row")])
    tool_serial._capture_rows(_SKU, _PORT)
    stat = logfile.stat()
    tool_serial._cache[str(logfile)] = tool_serial._ParsedLog(
        size=int(stat.st_size),
        mtime_ns=int(stat.st_mtime_ns),
        inode=123456789,
        parsed_bytes=int(stat.st_size),
        rows=((1.0, "2020-01-01 00:00:00,000", "stale_row"),),
    )

    rows = tool_serial._capture_rows(_SKU, _PORT)

    assert [message for _, _, message in rows] == ["old_row"]


def test_missing_file_returns_empty(logfile) -> None:
    """文件不存在时返回空列表，不抛错。"""
    assert tool_serial._capture_rows(_SKU, _PORT) == []
