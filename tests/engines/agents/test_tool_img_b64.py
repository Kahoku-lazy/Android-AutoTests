"""
单文件调试指令：python -m pytest tests/engines/agents/test_tool_img_b64.py -vv --tb=short

本文件是 tool_img_b64 的工具契约测试（纯单测，不连设备、不落盘）：

1. test_spec_* / test_assigned_* —— 工具规格只有一个 mark_dot，只读，且进入执行角色常驻组。
2. test_mark_dot_* —— 归一化/像素坐标都画到目标点，返回图片信封（base64 + media_type）。
3. test_keeps_* —— 输入格式沿用：PNG 进 PNG 出，JPEG 进 JPEG 出。
4. test_bad_* —— 截屏失败、非法 base64、坐标越界都转成可读 error，不抛到框架外。
5. test_pure_* —— 纯函数 base64 进 base64 出，越界抛 ValueError。
"""

from __future__ import annotations

import base64
import io

import pytest

from PIL import Image

from engines.agents import tools_config
from engines.agents.tools import tool_img_b64

pytestmark = pytest.mark.unit

_SIZE = (200, 100)


def _image_b64(fmt: str = "PNG", size: tuple[int, int] = _SIZE) -> str:
    """纯色测试图 → base64。"""
    buf = io.BytesIO()
    Image.new("RGB", size, (10, 120, 200)).save(buf, fmt)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def _open(b64: str) -> Image.Image:
    """base64 → 已加载的 PIL 图片。"""
    image = Image.open(io.BytesIO(base64.b64decode(b64)))
    image.load()
    return image


def _patch_shot(monkeypatch: pytest.MonkeyPatch, shot_b64: str) -> None:
    """用固定 base64 顶替设备截屏。"""
    monkeypatch.setattr(tool_img_b64, "_screenshot_b64", lambda _serial: shot_b64)


def test_spec_is_single_read_only_tool():
    """工具表只有一个 mark_dot，且只读、自动放行。"""
    specs = tool_img_b64.img_b64_tool_specs()
    assert [spec.name for spec in specs] == ["mark_dot"]
    assert specs[0].read_only is True
    assert specs[0].auto_allow is True
    assert tools_config.select_tools(("mark_dot",))[0].handler is tool_img_b64.mark_dot


def test_assigned_to_executor_basic_only():
    """mark_dot 进入执行角色常驻组，验收角色看不到它。"""
    assert "mark_dot" in tools_config.EXECUTOR_BASIC_TOOL_NAMES
    assert "mark_dot" not in tools_config.VERIFIER_BASIC_TOOL_NAMES
    group_names = {name for group in tools_config.EXECUTOR_TOOL_GROUPS for name in group.tool_names}
    assert "mark_dot" not in group_names


def test_mark_dot_normalized_draws_at_center(monkeypatch: pytest.MonkeyPatch):
    """归一化 (0.5, 0.5) 画到 200x100 图的 (100, 50)，其余像素不变。"""
    source = _image_b64()
    _patch_shot(monkeypatch, source)

    result = tool_img_b64.mark_dot("serial-1", 0.5, 0.5)

    assert set(result) == {"image"}
    assert result["image"]["media_type"] == "image/png"
    marked = _open(result["image"]["base64"])
    assert marked.size == _SIZE
    assert marked.format == "PNG"
    assert marked.getpixel((100, 50))[:3] == (255, 0, 0)
    assert marked.getpixel((0, 0))[:3] == (10, 120, 200)
    assert marked.getpixel((199, 99))[:3] == (10, 120, 200)
    # 原始截图未被改动
    assert _open(source).getpixel((100, 50))[:3] == (10, 120, 200)


def test_mark_dot_pixel_coordinates_match_normalized(monkeypatch: pytest.MonkeyPatch):
    """像素坐标与归一化坐标画在同一点；边界 1.0 夹到右下角。"""
    source = _image_b64()
    _patch_shot(monkeypatch, source)

    by_pixel = tool_img_b64.mark_dot("serial-1", 100, 50, normalized=False)
    by_ratio = tool_img_b64.mark_dot("serial-1", 0.5, 0.5)
    assert _open(by_pixel["image"]["base64"]).getpixel((100, 50)) == _open(
        by_ratio["image"]["base64"]
    ).getpixel((100, 50))

    edge = tool_img_b64.mark_dot("serial-1", 1.0, 1.0)
    assert _open(edge["image"]["base64"]).getpixel((199, 99))[:3] == (255, 0, 0)


def test_keeps_jpeg_format(monkeypatch: pytest.MonkeyPatch):
    """JPEG 截图标记后仍是 JPEG，media_type 同步为 image/jpeg。"""
    _patch_shot(monkeypatch, _image_b64("JPEG"))

    result = tool_img_b64.mark_dot("serial-1", 0.25, 0.25)

    assert result["image"]["media_type"] == "image/jpeg"
    assert _open(result["image"]["base64"]).format == "JPEG"


def test_bad_capture_returns_error(monkeypatch: pytest.MonkeyPatch):
    """截屏失败不抛到框架外，返回可读 error。"""

    def _boom(_serial: str) -> str:
        raise RuntimeError("adb 断开")

    monkeypatch.setattr(tool_img_b64, "_screenshot_b64", _boom)
    result = tool_img_b64.mark_dot("serial-1", 0.5, 0.5)

    assert "error" in result
    assert "adb 断开" in result["error"]


def test_bad_base64_returns_error(monkeypatch: pytest.MonkeyPatch):
    """截屏返回的不是图片时返回 error。"""
    _patch_shot(monkeypatch, "not-base64!!!")

    result = tool_img_b64.mark_dot("serial-1", 0.5, 0.5)

    assert "error" in result
    assert "标记失败" in result["error"]


def test_bad_pixel_coordinate_returns_error(monkeypatch: pytest.MonkeyPatch):
    """像素坐标越界返回 error，不画到图片外。"""
    _patch_shot(monkeypatch, _image_b64())

    result = tool_img_b64.mark_dot("serial-1", 500, 500, normalized=False)

    assert "error" in result
    assert "坐标越界" in result["error"]


def test_pure_function_returns_base64_and_raises():
    """纯函数返回 str；空串、越界抛 ValueError，支持 data URI 前缀。"""
    source = _image_b64()
    marked = tool_img_b64.mark_dot_b64(source, 0.5, 0.5)
    assert isinstance(marked, str)
    assert _open(marked).getpixel((100, 50))[:3] == (255, 0, 0)

    prefixed = tool_img_b64.mark_dot_b64(f"data:image/png;base64,{source}", 0.5, 0.5)
    assert prefixed == marked

    with pytest.raises(ValueError):
        tool_img_b64.mark_dot_b64("", 0.5, 0.5)
    with pytest.raises(ValueError):
        tool_img_b64.mark_dot_b64(source, 500, 500, normalized=False)
