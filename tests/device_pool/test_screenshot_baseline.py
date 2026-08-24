"""Step 0 基线（Step 4 显式更新）— screenshot_b64 输出格式锚定（经 FakeEngine 真实字节）。"""

import base64

from io import BytesIO

import pytest

from PIL import Image

from apps.device_pool.pool import DevicePool
from tests.device_pool.fakes import clear_sessions, install_fake_engine

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


@pytest.fixture
def pool(monkeypatch):
    clear_sessions()
    p = DevicePool()
    p.current_serial = "S"
    return p


class TestScreenshotB64:
    def test_output_is_jpeg_base64(self, pool, monkeypatch):
        install_fake_engine(monkeypatch)
        encoded = pool.screenshot_b64(quality=55)
        raw = base64.b64decode(encoded)
        assert raw[:2] == b"\xff\xd8"  # JPEG SOI

    def test_max_width_scales_down(self, pool, monkeypatch):
        install_fake_engine(monkeypatch)
        encoded = pool.screenshot_b64(quality=55, max_width=5)
        raw = base64.b64decode(encoded)
        img = Image.open(BytesIO(raw))
        assert img.width == 5
        assert img.height == 10  # 等比缩放（20x10 → 5x10）

    def test_no_max_width_keeps_original(self, pool, monkeypatch):
        install_fake_engine(monkeypatch)
        encoded = pool.screenshot_b64()
        img = Image.open(BytesIO(base64.b64decode(encoded)))
        assert (img.width, img.height) == (10, 20)

    def test_screenshot_file_saves_png(self, pool, monkeypatch, tmp_path):
        install_fake_engine(monkeypatch)
        path = tmp_path / "out.png"

        pool.screenshot_file(str(path))

        assert path.exists()
        assert path.read_bytes()[:8] == b"\x89PNG\r\n\x1a\n"  # PNG 魔数
