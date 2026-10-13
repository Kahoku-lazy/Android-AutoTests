"""灰盒·单元测试 — 按型号日志文件检查关键词。

零设备、零真实端口（临时目录里写日志文件）：
1. H6810 只读 `H6810_*.log`，H7011 只读 `H7011_*.log`；
2. 从起点向后 5 秒内找到关键词 → result 为 PASS，并带回那一行；
3. 这 5 秒内有日志但没有关键词 → result 为 FAIL；
4. 这 5 秒内没有任何日志 → 抛出「日志为空，请检查断后是否正确连接，此轮执行终止」。
"""

from __future__ import annotations

import json

from pathlib import Path

import pytest

from apps.ai_assistant.tools import list_tool_schemas
from engines.agents.tools.tool_serial import LOG_EMPTY, check_device_log
from engines.agents.tools_config import VERIFIER_BASIC_TOOL_NAMES, build_verifier_toolkit

pytestmark = [pytest.mark.unit, pytest.mark.django_db]

TOOL_NAME = "check_device_log"
CLICK_AT = "2026-10-12 11:40:10.865"
HIT_STAMP = "2026-10-12 11:40:11.491"
HIT_LINE = f"{HIT_STAMP} [tcp] [light_switch][I]: switch_off"


def _payload(result: str) -> dict:
    return json.loads(result)


def _use_dir(monkeypatch, directory: Path) -> None:
    monkeypatch.setattr("engines.agents.tools.tool_serial._log_dir", lambda: directory)


def test_tool_is_registered_as_read_only() -> None:
    rows = {row["name"]: row for row in list_tool_schemas()}
    assert TOOL_NAME in rows
    row = rows[TOOL_NAME]
    assert row["category"] == "设备日志"
    assert row["read_only"] is True
    assert row["module"] == "log" and row["action"] == "check"
    assert "关键词" in row["summary"]


def test_verifier_toolkit_keeps_screenshot_and_log_check_only() -> None:
    toolkit = build_verifier_toolkit()
    names = {tool.name for group in toolkit.tool_groups for tool in group.tools}
    assert VERIFIER_BASIC_TOOL_NAMES == ("screenshot_page", "check_device_log")
    assert names == {"screenshot_page", "check_device_log"}


def test_finds_keyword_in_the_next_five_seconds(tmp_path: Path, monkeypatch) -> None:
    """点击后一秒出现的 switch_off 落在 5 秒窗口内，返回该行原文。"""
    _use_dir(monkeypatch, tmp_path)
    (tmp_path / "H6810_7005.log").write_text(HIT_LINE + "\n", encoding="utf-8")

    payload = _payload(check_device_log(keyword="switch_off", at=CLICK_AT, sku="H6810"))

    assert payload == {"timestamp": HIT_STAMP, "msg": HIT_LINE, "result": "PASS"}


def test_sku_selects_its_own_log_file(tmp_path: Path, monkeypatch) -> None:
    """H6810 不读 H7011 的文件；H7011 能读到自己的命中行。"""
    _use_dir(monkeypatch, tmp_path)
    (tmp_path / "H7011_7006.log").write_text(HIT_LINE + "\n", encoding="utf-8")

    with pytest.raises(ValueError, match=LOG_EMPTY):
        check_device_log(keyword="switch_off", at=CLICK_AT, sku="H6810")

    payload = _payload(check_device_log(keyword="switch_off", at=CLICK_AT, sku="H7011"))
    assert payload["result"] == "PASS"
    assert payload["msg"] == HIT_LINE


def test_keyword_miss_is_fail(tmp_path: Path, monkeypatch) -> None:
    """窗口内有日志，但没有要查的关键词：返回 FAIL，不中断。"""
    _use_dir(monkeypatch, tmp_path)
    (tmp_path / "H6810_7005.log").write_text(HIT_LINE + "\n", encoding="utf-8")

    payload = _payload(check_device_log(keyword="switch_on", at=CLICK_AT, sku="H6810"))

    assert payload == {"timestamp": "", "msg": "", "result": "FAIL"}


def test_empty_window_interrupts(tmp_path: Path, monkeypatch) -> None:
    """命中行在起点 6 秒之后：这 5 秒内没有日志，中断本轮。"""
    _use_dir(monkeypatch, tmp_path)
    late = "2026-10-12 11:40:16.865 [tcp] [light_switch][I]: switch_off\n"
    (tmp_path / "H6810_7005.log").write_text(late, encoding="utf-8")

    with pytest.raises(ValueError, match=LOG_EMPTY) as caught:
        check_device_log(keyword="switch_off", at=CLICK_AT, sku="H6810")

    assert str(caught.value) == LOG_EMPTY


def test_line_before_start_is_outside_the_window(tmp_path: Path, monkeypatch) -> None:
    """起点之前的日志不算这 5 秒内。"""
    _use_dir(monkeypatch, tmp_path)
    early = "2026-10-12 11:40:10.864 [tcp] [light_switch][I]: switch_off\n"
    (tmp_path / "H6810_7005.log").write_text(early, encoding="utf-8")

    with pytest.raises(ValueError, match=LOG_EMPTY):
        check_device_log(keyword="switch_off", at=CLICK_AT, sku="H6810")


def test_returns_the_earliest_hit(tmp_path: Path, monkeypatch) -> None:
    """窗口内多次出现时，返回时间最早的那一行。"""
    _use_dir(monkeypatch, tmp_path)
    first = "2026-10-12 11:40:12.100 [tcp] [light_switch][I]: switch_off"
    second = "2026-10-12 11:40:14.200 [tcp] [light_switch][I]: switch_off"
    (tmp_path / "H6810_7005.log").write_text(f"{second}\n{first}\n", encoding="utf-8")

    payload = _payload(check_device_log(keyword="SWITCH_OFF", at=CLICK_AT, sku="H6810"))

    assert payload["result"] == "PASS"
    assert payload["timestamp"] == "2026-10-12 11:40:12.100"
    assert payload["msg"] == first


def test_feature_name_is_searched_as_written(tmp_path: Path, monkeypatch) -> None:
    """功能点中文按原文查找。日志里只有 switch_off 时，这条中文返回 FAIL。"""
    _use_dir(monkeypatch, tmp_path)
    (tmp_path / "H6810_7005.log").write_text(HIT_LINE + "\n", encoding="utf-8")

    payload = _payload(check_device_log(keyword="关闭设备成功", at=CLICK_AT, sku="H6810"))

    assert payload == {"timestamp": "", "msg": "", "result": "FAIL"}


def test_second_precision_start_still_hits(tmp_path: Path, monkeypatch) -> None:
    """起点只写到秒时，按该秒的 .000 向后 5 秒查找。"""
    _use_dir(monkeypatch, tmp_path)
    (tmp_path / "H6810_7005.log").write_text(HIT_LINE + "\n", encoding="utf-8")

    payload = _payload(
        check_device_log(keyword="switch_off", at="2026-10-12 11:40:10", sku="H6810")
    )

    assert payload["result"] == "PASS"
    assert payload["timestamp"] == HIT_STAMP


def test_verifier_prompt_carries_keyword_catalog() -> None:
    """验收系统提示词附上关键词表，并写明 UI 断言不要查日志。"""
    from engines.agents.prompts.verifier_prompt import verifier_system_prompt

    prompt = verifier_system_prompt()
    assert "switch_off" in prompt
    assert "关闭设备成功" in prompt
    assert "原样写入 check_device_log 的 keyword" in prompt
    assert "UI 断言不要查日志" in prompt
    assert "不要调用 check_device_log" in prompt


def test_missing_inputs_are_fail(tmp_path: Path, monkeypatch) -> None:
    """缺关键词、时间点或型号时返回 FAIL，不中断。"""
    _use_dir(monkeypatch, tmp_path)
    (tmp_path / "H6810_7005.log").write_text(HIT_LINE + "\n", encoding="utf-8")

    assert _payload(check_device_log(keyword="  ", at=CLICK_AT, sku="H6810"))["result"] == "FAIL"
    assert _payload(check_device_log(keyword="switch_off", at="", sku="H6810"))["result"] == "FAIL"
    assert _payload(check_device_log(keyword="switch_off", at=CLICK_AT, sku=""))["result"] == "FAIL"
