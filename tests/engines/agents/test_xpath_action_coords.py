"""xpath_action 只返回文本与中心坐标，不点击。"""

import json

import pytest

from engines.agents.tools import tool_device as agent_tools


class _Conn:
    def disconnect(self) -> None:
        return None


class _Info:
    def current_app(self) -> dict:
        raise AssertionError("只读查询不应读取前台应用")


def _install(monkeypatch: pytest.MonkeyPatch, found: list[dict] | None):
    clicks: list[str] = []

    class _Control:
        def find_xpath(self, xpath: str) -> list[dict] | None:
            del xpath
            return found

        def click_element(self, *_args, **_kwargs) -> bool:
            clicks.append("click")
            return True

        def long_click_element(self, *_args, **_kwargs) -> bool:
            clicks.append("long_click")
            return True

    def open_device(*_args, **_kwargs):
        return _Conn(), _Info(), _Control()

    monkeypatch.setattr(agent_tools, "open_device", open_device)
    return clicks


def _load(serial: str, xpath: str) -> dict:
    return json.loads(agent_tools.xpath_action(serial, xpath))


def test_single_hit_has_no_index(monkeypatch: pytest.MonkeyPatch) -> None:
    clicks = _install(
        monkeypatch,
        [
            {
                "text": "H6110",
                "x": 120,
                "y": 340,
                "bounds": "[80,300][160,380]",
                "resource_id": "rid",
                "class_name": "TextView",
                "content_desc": "desc",
            }
        ],
    )
    payload = _load("serial-1", "//node")
    assert payload == {
        "count": 1,
        "text": "H6110",
        "x": 120,
        "y": 340,
    }
    assert "index" not in payload
    assert "items" not in payload
    assert "action_time" not in payload
    assert "bounds" not in payload
    assert clicks == []


def test_multiple_hits_are_indexed(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(
        monkeypatch,
        [
            {"text": "A", "x": 1, "y": 2, "bounds": "[0,0][2,4]"},
            {"text": "B", "x": 3, "y": 4, "bounds": "[2,0][4,4]"},
            {"text": "C", "x": 5, "y": 6, "bounds": "[4,0][6,4]"},
        ],
    )
    payload = _load("serial-1", "//node")
    assert payload["count"] == 3
    assert [item["index"] for item in payload["items"]] == [0, 1, 2]
    assert payload["items"][2]["text"] == "C"
    assert payload["items"][2]["x"] == 5
    assert payload["items"][2]["y"] == 6


def test_no_hit(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, [])
    payload = _load("serial-1", "//missing")
    assert payload == {"count": 0, "items": []}
    assert "text" not in payload
    assert "x" not in payload
    assert "y" not in payload


def test_missing_center_defaults_to_zero(monkeypatch: pytest.MonkeyPatch) -> None:
    _install(monkeypatch, [{"text": "ON"}])
    payload = _load("serial-1", "//node")
    assert (payload["x"], payload["y"]) == (0, 0)


def test_connection_failure_returns_error(monkeypatch: pytest.MonkeyPatch) -> None:
    def open_device(*_args, **_kwargs):
        raise RuntimeError("offline")

    monkeypatch.setattr(agent_tools, "open_device", open_device)
    payload = _load("serial-1", "//node")
    assert "error" in payload
    assert "offline" in payload["error"]


def test_xpath_action_is_read_only() -> None:
    specs = {spec.name: spec for spec in agent_tools.device_tool_specs()}
    assert specs["xpath_action"].read_only is True
