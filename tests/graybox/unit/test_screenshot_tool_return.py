"""截图工具：只做截图（不查前台应用 / 屏幕尺寸），返回模型图与本地路径。"""

from __future__ import annotations

import io
import re

import pytest

from PIL import Image

from engines.ai.tools import tool_device


class _Info:
    """设备信息桩：记录是否被截图工具查询过（不该被查）。"""

    def __init__(self) -> None:
        self.calls: list[str] = []

    def current_app(self) -> dict:
        self.calls.append("current_app")
        return {"package": "com.demo", "activity": ".MainActivity"}

    def screen_size(self) -> tuple[int, int]:
        self.calls.append("screen_size")
        return (1080, 2340)


class _Control:
    def screenshot_raw(self) -> bytes:
        image = Image.new("RGB", (1080, 2340), (1, 2, 3))
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()


class _Connection:
    def __init__(self) -> None:
        self.disconnected = False

    def disconnect(self) -> None:
        self.disconnected = True


def _patch(monkeypatch, info: _Info, connection: _Connection) -> None:
    monkeypatch.setattr(
        tool_device, "open_device", lambda system, serial: (connection, info, _Control())
    )


@pytest.mark.unit
def test_screenshot_tool_returns_only_image_and_local_path(tmp_path, monkeypatch):
    info, connection = _Info(), _Connection()
    _patch(monkeypatch, info, connection)
    tools = tool_device.build_device_tools(str(tmp_path))

    result = tools["screenshot_page"]("S1", keep_local=True)

    assert set(result["summary"]) == {"screenshot_path", "screenshot_name"}
    assert info.calls == [], "截图工具 MUST NOT 额外查询前台应用或屏幕尺寸"
    assert connection.disconnected, "用完必须断开连接"
    assert re.fullmatch(
        r"inspector/shots/capture_\d{8}_\d{6}_\d{3}\.jpg", result["summary"]["screenshot_path"]
    )
    assert result["image"]["base64"], "必须把图片给模型"
    assert (tmp_path / result["summary"]["screenshot_path"]).is_file()


@pytest.mark.unit
def test_screenshot_tool_keep_local_false_still_gives_image(tmp_path, monkeypatch):
    info, connection = _Info(), _Connection()
    _patch(monkeypatch, info, connection)
    tools = tool_device.build_device_tools(str(tmp_path))

    result = tools["screenshot_page"]("S1", keep_local=False)

    assert result["summary"] == {"screenshot_path": "", "screenshot_name": ""}
    assert result["image"]["base64"], "不落盘时仍要把图片给模型"
    assert not (tmp_path / "inspector").exists()
