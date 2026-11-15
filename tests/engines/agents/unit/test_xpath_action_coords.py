"""
单文件调试指令：python -m pytest tests/engines/agents/test_xpath_action_coords.py -vv --tb=short

本文件是 xpath_action 的契约测试（纯单测，不连设备）：

1. test_single_hit_* —— 命中 1 条：回标记图、序号 1、帧标识，且只读不点击。
2. test_multiple_hits_* —— 命中多条：全部标在同一张图上，序号按纵坐标升序。
3. test_marked_image_* —— 每个命中点在图上都有一个红点。
4. test_no_hit_* / test_missing_center_* —— 未命中不出图不截图；缺中心坐标按 0 兜底。
5. test_confirm_off_* —— confirm=False 时只回坐标，不出图也不签发 token。
6. test_connection_failure_* / test_xpath_action_is_read_only —— 失败路径与只读标记。
"""

from __future__ import annotations

import base64
import io
import json

import pytest

from PIL import Image

from engines.agents.tools import tool_device as agent_tools

pytestmark = pytest.mark.unit

def _shot_bytes(size: tuple[int, int] = (120, 120)) -> bytes:
    """造一张纯色截图，供标记点断言使用。"""
    buf = io.BytesIO()
    Image.new("RGB", size, (10, 120, 200)).save(buf, "PNG")
    return buf.getvalue()


PNG_1PX = _shot_bytes()


class _Conn:
    """连接对象替身。"""

    def disconnect(self) -> None:
        return None


class _Info:
    """设备信息替身：只读查询不应该去读前台应用。"""

    def current_app(self) -> dict:
        raise AssertionError("只读查询不应该读取前台应用")


def _install(monkeypatch: pytest.MonkeyPatch, found: list[dict] | None):
    """装一个假设备：记录截图与手势次数。"""
    calls: list[str] = []

    class _Control:
        screenshot_media_type = "image/png"

        def find_xpath(self, xpath: str) -> list[dict] | None:
            del xpath
            return found

        def screenshot_bytes(self) -> bytes:
            calls.append("screenshot")
            return PNG_1PX

        def click_coord(self, *_args) -> None:
            calls.append("click")

        def long_click_coord(self, *_args) -> None:
            calls.append("long_click")

    def open_device(*_args, **_kwargs):
        return _Conn(), _Info(), _Control()

    monkeypatch.setattr(agent_tools, "open_device", open_device)
    return calls


def _load(serial: str, *args, **kwargs) -> dict:
    """调用并统一成 dict：带图结果原样返回，文本结果按 JSON 解析。"""
    result = agent_tools.xpath_action(serial, *args, **kwargs)
    return result if isinstance(result, dict) else json.loads(result)


def test_single_hit_returns_marked_image_and_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """命中 1 条：回标记图、序号 1 的条目与帧标识，且不产生点击。"""
    calls = _install(monkeypatch, [{"text": "H6110", "x": 120, "y": 340}])

    payload = _load("serial-1", "//node")
    summary = payload["summary"]

    assert summary["count"] == 1
    assert summary["items"] == [{"index": 1, "text": "H6110", "x": 120, "y": 340}]
    assert summary["token"]
    assert payload["image"]["media_type"] == "image/png"
    assert "click" not in calls and "long_click" not in calls


def test_multiple_hits_are_numbered_by_position(monkeypatch: pytest.MonkeyPatch) -> None:
    """命中多条：序号按（纵坐标, 横坐标）升序，全部画在同一张图上。"""
    _install(
        monkeypatch,
        [
            {"text": "定时", "x": 230, "y": 1684},
            {"text": "定时", "x": 142, "y": 774},
        ],
    )

    summary = _load("serial-1", "//*[@text='定时']")["summary"]

    assert [item["index"] for item in summary["items"]] == [1, 2]
    assert [(item["x"], item["y"]) for item in summary["items"]] == [(142, 774), (230, 1684)]


def test_marked_image_has_one_dot_per_hit(monkeypatch: pytest.MonkeyPatch) -> None:
    """两个命中点在图上各有一个红点。"""
    _install(
        monkeypatch,
        [
            {"text": "定时", "x": 20, "y": 20},
            {"text": "定时", "x": 80, "y": 60},
        ],
    )

    payload = _load("serial-1", "//*[@text='定时']")
    image = Image.open(io.BytesIO(base64.b64decode(payload["image"]["base64"])))
    image.load()

    assert image.getpixel((20, 20))[:3] == (255, 0, 0)
    assert image.getpixel((80, 60))[:3] == (255, 0, 0)


def test_no_hit_reports_zero_without_screenshot(monkeypatch: pytest.MonkeyPatch) -> None:
    """未命中：count=0、不出图、不截图。"""
    calls = _install(monkeypatch, [])

    payload = _load("serial-1", "//missing")

    assert payload["count"] == 0
    assert payload["items"] == []
    assert "image" not in payload
    assert "screenshot" not in calls


def test_missing_center_defaults_to_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    """元素没有中心坐标时按 0 兜底，不抛异常。"""
    _install(monkeypatch, [{"text": "no-center"}])

    summary = _load("serial-1", "//node")["summary"]

    assert (summary["items"][0]["x"], summary["items"][0]["y"]) == (0, 0)


def test_confirm_off_returns_coordinates_only(monkeypatch: pytest.MonkeyPatch) -> None:
    """confirm=False：只回坐标，不出图、不签发 token。"""
    calls = _install(monkeypatch, [{"text": "H6110", "x": 120, "y": 340}])

    payload = _load("serial-1", "//node", confirm=False)

    assert payload["count"] == 1
    assert "token" not in payload
    assert "image" not in payload
    assert "screenshot" not in calls


def test_connection_failure_returns_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """连不上设备时返回可读 error。"""

    def open_device(*_args, **_kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(agent_tools, "open_device", open_device)
    payload = _load("serial-1", "//node")

    assert "error" in payload
    assert "offline" in payload["error"]


def test_xpath_action_is_read_only() -> None:
    """xpath 查询标记为只读工具。"""
    specs = {spec.name: spec for spec in agent_tools.device_tool_specs()}
    assert specs["xpath_action"].read_only is True
