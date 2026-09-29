"""灰盒·单元测试 — 按关键词规则检查日志的工具（变更 verifier-log-check-tool）。

零设备、零真实端口（用 tcp_port=0 的假总线 + 直接 feed / 写日志文件）：
覆盖五条口径 ——
1. 检测到：给出时间戳、功能点与取数来源；
2. 未检测到 ≠ 出错：有日志但没该关键词 → no_hit；窗口内没日志 → no_log；
3. 关键词不在关键词表内时照常检查并如实标注；
4. 关键词缺省 / 端口未监听 / 端口未配置时给可读结论，不抛错、不开端口；
5. 缓冲没有时从已落盘的日志文件里检查（不受缓冲保留时长限制）。
"""

from __future__ import annotations

import json

from pathlib import Path

import pytest

from apps.ai_assistant.tools import check_device_log, list_tool_schemas
from engines.device.logbus import LogBusConfig, start_log_bus, stop_log_bus

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

SKU_CHANNEL = "H6810"
TOOL_NAME = "check_device_log"
REPO_ROOT = Path(__file__).resolve().parents[3]
KEYWORD_FILE = REPO_ROOT / "config" / "device_log_keywords.json"
SWITCH_ON = "2026-09-29 11:47:04.687"


def _payload(result: str) -> dict:
    return json.loads(result)


@pytest.fixture
def bus(tmp_path: Path):
    """真实但不起采集线程的总线：带日志目录（可从文件回溯），关键词表用平台表。"""
    instance = start_log_bus(
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
        yield instance
    finally:
        stop_log_bus()


def test_tool_is_registered_as_read_only() -> None:
    rows = {row["name"]: row for row in list_tool_schemas()}
    assert TOOL_NAME in rows
    row = rows[TOOL_NAME]
    assert row["category"] == "设备日志"
    assert row["read_only"] is True
    assert row["module"] == "log" and row["action"] == "check"
    assert "关键词" in row["summary"]


def test_detects_keyword_from_log_file(bus, tmp_path: Path) -> None:
    """缓冲里没有（重启后 / 十几分钟前）：从已落盘文件按窗口检查到，并给出功能点。"""
    (tmp_path / f"{SKU_CHANNEL}_7005.log").write_text(
        f"{SWITCH_ON} [tcp] [light_switch][I]: switch_on\n", encoding="utf-8"
    )

    payload = _payload(
        check_device_log(keyword="switch_on", at="2026-09-29 11:47:04.326", port=7005)
    )

    assert payload["detected"] is True
    assert payload["conclusion"] == "hit"
    assert payload["timestamps"] == [SWITCH_ON]
    assert payload["query"]["span_seconds"] == 5.0  # 默认取平台取证阈值
    assert payload["sources"] == {"buffer_lines": 0, "file_lines": 1}
    assert payload["keyword_known"] is True
    assert payload["features"][0]["feature"] == "打开设备成功"


def test_no_hit_is_not_an_error(bus, tmp_path: Path) -> None:
    (tmp_path / f"{SKU_CHANNEL}_7005.log").write_text(
        f"2026-09-29 11:47:04.687 [tcp] [light_switch][I]: switch_off\n", encoding="utf-8"
    )

    payload = _payload(
        check_device_log(keyword="switch_on", at="2026-09-29 11:47:04.326", port=7005)
    )

    assert payload["detected"] is False
    assert payload["conclusion"] == "no_hit"
    assert "没有出现" in payload["note"]


def test_no_log_in_window_is_reported_separately(bus) -> None:
    payload = _payload(
        check_device_log(keyword="switch_on", at="2026-09-29 09:00:00.000", port=7005)
    )

    assert payload["detected"] is False
    assert payload["conclusion"] == "no_log"
    assert "没有任何日志" in payload["note"]


def test_unknown_keyword_still_checked(bus, tmp_path: Path) -> None:
    (tmp_path / f"{SKU_CHANNEL}_7005.log").write_text(
        f"{SWITCH_ON} [tcp] [x]: totally_custom_token\n", encoding="utf-8"
    )

    payload = _payload(
        check_device_log(keyword="totally_custom_token", at="2026-09-29 11:47:04.326", port=7005)
    )

    assert payload["detected"] is True
    assert payload["keyword_known"] is False
    assert "不在平台关键词表内" in payload["note"]


def test_missing_keyword_is_readable(bus) -> None:
    payload = _payload(check_device_log(keyword="  ", at="2026-09-29 11:47:04.326", port=7005))
    assert payload["detected"] is False
    assert payload["conclusion"] == "keyword_missing"
    assert "关键词" in payload["note"]


def test_disabled_port_is_readable(bus, monkeypatch) -> None:
    """端口关着监听：给可读结论、不查日志、不打开端口。"""
    from apps.ai_assistant import api

    monkeypatch.setattr(api, "is_log_port_enabled", lambda port: False)

    payload = _payload(check_device_log(keyword="switch_on", port=7005))

    assert payload["conclusion"] == "port_disabled"
    assert payload["detected"] is False
    assert "已关闭监听" in payload["note"]


def test_unconfigured_port_is_readable(bus) -> None:
    payload = _payload(
        check_device_log(keyword="switch_on", at="2026-09-29 11:47:04.326", port=9100)
    )
    assert payload["conclusion"] == "port_not_configured"
    assert payload["detected"] is False
