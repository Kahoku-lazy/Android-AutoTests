"""Step 0 基线 — OCR 现状行为锚定（L1a 算法下沉前置）。

cnocr 引擎全部 mock，不加载真实模型。
"""

import base64

import pytest

from PIL import Image

from algorithms.vision import ocr as ocr_module

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


class TestPilToB64:
    def test_output_is_jpeg_base64(self):
        img = Image.new("RGB", (8, 8), "red")
        encoded = ocr_module._pil_to_b64(img)
        raw = base64.b64decode(encoded)
        assert raw[:2] == b"\xff\xd8"  # JPEG SOI 魔数


class _FakeEngine:
    def __init__(self, results):
        self._results = results

    def ocr(self, path):
        return self._results


@pytest.fixture
def fake_screenshot(tmp_path):
    img = Image.new("RGB", (80, 60), "white")
    path = tmp_path / "shot.png"
    img.save(str(path))
    return str(path)


class TestRecognize:
    def test_maps_cnocr_output(self, fake_screenshot, monkeypatch):
        monkeypatch.setattr(
            ocr_module,
            "_get_engine",
            lambda: _FakeEngine(
                [
                    {
                        "text": "登录",
                        "score": 0.9876,
                        "position": [(10, 10), (50, 10), (50, 30), (10, 30)],
                    },
                ]
            ),
        )

        texts = ocr_module.recognize(fake_screenshot)

        assert len(texts) == 1
        t = texts[0]
        assert t["text"] == "登录"
        assert t["confidence"] == 0.9876
        assert (t["x"], t["y"], t["width"], t["height"]) == (10, 10, 40, 20)
        assert t["bounds"] == "[10,10][50,30]"
        assert t["thumbnail_format"] == "jpeg"
        assert base64.b64decode(t["thumbnail"])[:2] == b"\xff\xd8"

    def test_skips_empty_and_zero_size_positions(self, fake_screenshot, monkeypatch):
        monkeypatch.setattr(
            ocr_module,
            "_get_engine",
            lambda: _FakeEngine(
                [
                    {"text": "无位置", "score": 0.5, "position": None},
                    {"text": "空位置", "score": 0.5, "position": []},
                    {"text": "零尺寸", "score": 0.5, "position": [(0, 0), (0, 0)]},
                    {"text": "有效", "score": 0.9, "position": [(0, 0), (4, 0), (4, 4), (0, 4)]},
                ]
            ),
        )

        texts = ocr_module.recognize(fake_screenshot)

        assert [t["text"] for t in texts] == ["有效"]
