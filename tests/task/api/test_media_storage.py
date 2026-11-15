"""本地截图存储：WebP 编码、读写回环、路径越界保护。"""

from __future__ import annotations

import base64
import hashlib
import io

import pytest

from PIL import Image

from backend.apps.task_list import media_storage

pytestmark = [pytest.mark.unit]


def _png_bytes(width: int = 1080, height: int = 2400) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), (20, 40, 60)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_encode_produces_webp_and_original_sha():
    raw = _png_bytes()
    packed = media_storage.encode(base64.b64encode(raw).decode("ascii"))

    assert packed is not None
    assert packed["media_type"] == "image/webp"
    assert packed["sha256"] == hashlib.sha256(raw).hexdigest()
    image = Image.open(io.BytesIO(packed["data"]))
    assert image.format == "WEBP"
    assert max(image.size) == 720


def test_encode_returns_none_for_bad_image():
    assert media_storage.encode("not-an-image") is None


def test_save_open_and_delete_task(tmp_path):
    storage = media_storage.LocalMediaStorage(tmp_path)
    key = storage.save(142, "a" * 64, b"webp-bytes")

    assert key == f"142/{'a' * 64}.webp"
    assert storage.open(key) == b"webp-bytes"
    assert storage.exists(key)
    assert storage.keys_for_task(142) == {key}

    storage.delete_task(142)
    assert storage.open(key) is None
    assert storage.keys_for_task(142) == set()


def test_path_traversal_is_rejected(tmp_path):
    storage = media_storage.LocalMediaStorage(tmp_path)

    assert storage.open("../outside.webp") is None
    with pytest.raises(ValueError):
        storage.build_key(1, "../bad")
