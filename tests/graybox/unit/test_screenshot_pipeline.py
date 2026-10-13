"""截图链路：原始帧 → 只编一次（给模型的 base64）+ 落盘一张本地图（毫秒时间戳命名）。"""

from __future__ import annotations

import base64
import io
import re

import pytest

from PIL import Image

from engines.device.action import MODEL_MEDIA_TYPE, Screenshot, millisecond_stamp


class _FakeControl:
    """最小控制桩：截图动作只需要 `screenshot_raw`。"""

    def __init__(self, size: tuple[int, int] = (1080, 2340)) -> None:
        self.calls = 0
        self._size = size

    def screenshot_raw(self) -> bytes:
        self.calls += 1
        image = Image.new("RGB", self._size, (10, 20, 30))
        buf = io.BytesIO()
        image.save(buf, format="PNG")
        return buf.getvalue()


@pytest.mark.unit
def test_save_takes_one_raw_frame_and_writes_ms_named_local_file(tmp_path):
    control = _FakeControl()

    shot = Screenshot(control).save(str(tmp_path), keep_local=True)

    assert control.calls == 1, "只取一次原始帧（不再有中间压缩）"
    assert re.fullmatch(r"capture_\d{8}_\d{6}_\d{3}\.jpg", shot["screenshot_name"])
    assert shot["screenshot_path"] == f"inspector/shots/{shot['screenshot_name']}"

    local = tmp_path / "inspector" / "shots" / shot["screenshot_name"]
    assert local.is_file(), "本地图必须落盘"
    with Image.open(local) as image:
        assert image.format == "JPEG"
        assert image.size == (1080, 2340), "本地图是全分辨率"


@pytest.mark.unit
def test_model_payload_is_lossless_png_at_full_size(tmp_path):
    """给模型的图必须无损、原尺寸（不缩放、不有损压缩）。"""
    shot = Screenshot(_FakeControl()).save(str(tmp_path), keep_local=True)

    assert shot["media_type"] == MODEL_MEDIA_TYPE
    raw = base64.b64decode(shot["image_base64"])
    assert raw[:8] == b"\x89PNG\r\n\x1a\n", "给模型的必须是 PNG（无损）"
    with Image.open(io.BytesIO(raw)) as image:
        assert image.size == (1080, 2340), "给模型的图不得缩放"
        assert image.format == "PNG"


@pytest.mark.unit
def test_keep_local_false_returns_base64_without_local_file(tmp_path):
    shot = Screenshot(_FakeControl()).save(str(tmp_path), keep_local=False)

    assert shot["screenshot_path"] == "" and shot["screenshot_name"] == ""
    assert shot["image_base64"], "不给本地图时仍要把图给模型"
    assert not (tmp_path / "inspector").exists()


@pytest.mark.unit
def test_millisecond_stamp_format():
    assert re.fullmatch(r"\d{8}_\d{6}_\d{3}", millisecond_stamp())
