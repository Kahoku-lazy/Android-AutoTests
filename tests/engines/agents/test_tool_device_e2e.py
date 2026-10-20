"""
单文件调试指令：python -m pytest tests/engines/agents/test_tool_device_e2e.py -vv -s --tb=short

本文件用真机验证工具链路，参数取自 test_agents_workflow.yml 的 TestToolDevice 段
（serial 必填、package 可选，缺省 com.android.settings）。约 15 秒。

1. test_screenshot_page_returns_png_without_path —— 截图 base64 解出以 \\x89PNG 开头，路径为空串。
2. test_click_ratio_returns_pixel_and_time —— 归一化点击回实际像素坐标与动作时间。
3. test_tap_screen_returns_pixel_and_time —— 像素点击的坐标与入参一致。
4. test_swipe_screen_returns_only_time / test_press_key_returns_only_time —— 返回体只有 action_time。
5. test_app_control_stop_then_start_reports_both_foregrounds —— 先停后起，两次都给出动作前后的前台应用。

标 e2e（真实设备链路）：`-m "unit or integration"` 不会带上它，免得没有设备的环境变红；
serial 未配置时整文件跳过。注意这些用例真的会点屏、滑动、按返回键、启停 App。
"""

from __future__ import annotations

import base64
import json
import re

from pathlib import Path

import pytest
import yaml

from engines.agents.tools import tool_device

_FIXTURE = Path(__file__).with_name("test_agents_workflow.yml")
# 与 utils.logs.logging_now_stamp 的格式一致：YYYY-MM-DD HH:MM:SS,mmm
_STAMP = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3}$")
_DEFAULT_PACKAGE = "com.android.settings"


def _device_params() -> dict:
    """读用例 YAML 的 `TestToolDevice` 段（真机参数）。"""
    data = yaml.safe_load(_FIXTURE.read_text(encoding="utf-8")) or {}
    section = data.get("TestToolDevice") if isinstance(data, dict) else None
    return dict(section or {})


_PARAMS = _device_params()
_SERIAL = str(_PARAMS.get("serial") or "").strip()
_PACKAGE = str(_PARAMS.get("package") or _DEFAULT_PACKAGE).strip()

pytestmark = [
    pytest.mark.e2e,
    pytest.mark.skipif(
        not _SERIAL,
        reason="test_agents_workflow.yml 的 TestToolDevice.serial 未配置",
    ),
]


def _run(name: str, *args, **kwargs) -> dict:
    """调用工具并解析返回的 JSON。"""
    return json.loads(getattr(tool_device, name)(_SERIAL, *args, **kwargs))


def _assert_stamp(payload: dict) -> None:
    """返回体里的 action_time 必须是本地时间戳格式。"""
    assert "action_time" in payload, payload
    assert _STAMP.match(payload["action_time"]), payload["action_time"]


def _show(label: str, expected: str, actual) -> None:
    """打印预期与实际，让 PASS 也能看到比对结果（-vv 只给 PASSED，要配 -s）。"""
    if isinstance(actual, dict):
        actual = json.dumps(actual, ensure_ascii=False)
    print(f"\n[预期] {label} → {expected}")
    print(f"[实际] {actual}")


# ══════════════════════════════════════════════════════════════════
# 非动作工具
# ══════════════════════════════════════════════════════════════════


def test_screenshot_page_returns_png_without_path() -> None:
    """截图回传的是可解码的 PNG，且不落盘（路径恒为空串）。"""
    payload = tool_device.build_device_tools()["screenshot_page"](_SERIAL)
    raw = base64.b64decode(payload["image"]["base64"])
    _show(
        "screenshot_page",
        '{"image": {base64: 可解码为 PNG（\\x89PNG 开头）, media_type: image/png}}，只有这一个键',
        {
            "png头": repr(raw[:4]),
            "像素字节": len(raw),
            "media_type": payload["image"]["media_type"],
            "顶层键": sorted(payload),
        },
    )

    assert "error" not in payload, payload
    assert raw.startswith(b"\x89PNG")
    assert payload["image"]["media_type"] == "image/png"
    assert set(payload) == {"image"}


# ══════════════════════════════════════════════════════════════════
# 点击类：回传像素坐标 + 动作时间
# ══════════════════════════════════════════════════════════════════


def test_click_ratio_returns_pixel_and_time() -> None:
    """归一化点击回传实际像素坐标（屏幕中央）与时间。"""
    payload = _run("click_ratio", nx=0.5, ny=0.5)
    _show(
        "click_ratio(nx=0.5, ny=0.5)",
        "{x: 实际像素, y: 实际像素, action_time: YYYY-MM-DD HH:MM:SS,mmm}，恰好这三个键",
        payload,
    )

    assert "error" not in payload, payload
    assert set(payload) == {"x", "y", "action_time"}
    _assert_stamp(payload)
    assert payload["x"] > 0 and payload["y"] > 0


def test_tap_screen_returns_pixel_and_time() -> None:
    """像素点击回传的坐标与入参一致。"""
    payload = _run("tap_screen", mode="click", x=100, y=200)
    _show(
        "tap_screen(mode=click, x=100, y=200)",
        "{x: 100, y: 200, action_time: YYYY-MM-DD HH:MM:SS,mmm}",
        payload,
    )

    assert "error" not in payload, payload
    assert (payload["x"], payload["y"]) == (100, 200)
    _assert_stamp(payload)


# ══════════════════════════════════════════════════════════════════
# 只回动作时间的动作
# ══════════════════════════════════════════════════════════════════


def test_swipe_screen_returns_only_time() -> None:
    """滑动只回动作时间。"""
    payload = _run("swipe_screen", direction="up", distance=300)
    _show(
        "swipe_screen(direction=up, distance=300)",
        "{action_time: YYYY-MM-DD HH:MM:SS,mmm}，只有这一个键",
        payload,
    )

    assert "error" not in payload, payload
    assert set(payload) == {"action_time"}
    _assert_stamp(payload)


def test_press_key_returns_only_time() -> None:
    """返回键只回动作时间。"""
    payload = _run("press_key")
    _show("press_key", "{action_time: YYYY-MM-DD HH:MM:SS,mmm}，只有这一个键", payload)

    assert "error" not in payload, payload
    assert set(payload) == {"action_time"}
    _assert_stamp(payload)


# ══════════════════════════════════════════════════════════════════
# 启停 App：时间点 + 包名 + 前后台
# ══════════════════════════════════════════════════════════════════


def test_app_control_stop_then_start_reports_both_foregrounds() -> None:
    """先停后起：两次都要给出动作前后的前台应用。"""
    stopped = _run("app_control", action="stop_app", package=_PACKAGE)
    _show(
        f"app_control(stop_app, {_PACKAGE})",
        "after_app.package 不等于目标包；action=stop_app；带 action_time",
        stopped,
    )
    assert "error" not in stopped, stopped
    _assert_stamp(stopped)
    assert stopped["action"] == "stop_app"
    assert stopped["package"] == _PACKAGE
    assert (
        stopped["before_app"]["package"] == _PACKAGE or stopped["after_app"]["package"] != _PACKAGE
    )

    started = _run("app_control", action="start_app", package=_PACKAGE)
    _show(
        f"app_control(start_app, {_PACKAGE})",
        "after_app.package 等于目标包；action=start_app；带 action_time",
        started,
    )
    assert "error" not in started, started
    _assert_stamp(started)
    assert started["action"] == "start_app"
    assert started["after_app"]["package"] == _PACKAGE, started["after_app"]
