from __future__ import annotations

import base64
import hashlib
import io
import os
import shutil

from pathlib import Path

from django.conf import settings
from PIL import Image

THUMBNAIL_EDGE = 720
WEBP_QUALITY = 75
MEDIA_TYPE = "image/webp"
_SHA_LEN = 64


def _sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _to_webp(raw: bytes) -> tuple[bytes, int, int] | None:
    if not raw:
        return None
    try:
        image = Image.open(io.BytesIO(raw)).convert("RGB")
        image.thumbnail((THUMBNAIL_EDGE, THUMBNAIL_EDGE))
        buffer = io.BytesIO()
        image.save(buffer, format="WEBP", quality=WEBP_QUALITY)
    except Exception:
        return None
    return buffer.getvalue(), image.size[0], image.size[1]


def encode(image_b64: str) -> dict | None:
    try:
        raw = base64.b64decode(image_b64, validate=False)
    except Exception:
        return None
    packed = _to_webp(raw)
    if packed is None:
        return None
    data, width, height = packed
    return {
        "sha256": _sha256(raw),
        "data": data,
        "width": width,
        "height": height,
        "media_type": MEDIA_TYPE,
    }


def reencode(raw: bytes) -> tuple[bytes, int, int] | None:
    return _to_webp(raw)


class LocalMediaStorage:
    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        return self._root

    def build_key(self, task_id: int, sha256: str) -> str:
        digest = (sha256 or "").strip().lower()
        if len(digest) != _SHA_LEN or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("sha256 必须是 64 位十六进制")
        return f"{int(task_id)}/{digest}.webp"

    def save(self, task_id: int, sha256: str, data: bytes) -> str:
        key = self.build_key(task_id, sha256)
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(f"{path.name}.tmp")
        temp.write_bytes(data)
        os.replace(temp, path)
        return key

    def open(self, key: str) -> bytes | None:
        if not (key or "").strip():
            return None
        try:
            path = self._path(key)
        except ValueError:
            return None
        try:
            return path.read_bytes()
        except OSError:
            return None

    def exists(self, key: str) -> bool:
        if not (key or "").strip():
            return False
        try:
            return self._path(key).is_file()
        except ValueError:
            return False

    def keys_for_task(self, task_id: int) -> set[str]:
        directory = self._root / str(int(task_id))
        if not directory.is_dir():
            return set()
        prefix = f"{int(task_id)}/"
        return {f"{prefix}{entry.name}" for entry in directory.iterdir() if entry.is_file()}

    def delete(self, key: str) -> bool:
        try:
            self._path(key).unlink()
        except (OSError, ValueError):
            return False
        return True

    def delete_task(self, task_id: int) -> None:
        shutil.rmtree(self._root / str(int(task_id)), ignore_errors=True)

    def _path(self, key: str) -> Path:
        text = (key or "").strip().replace("\\", "/")
        if not text:
            raise ValueError("存储键不能为空")
        candidate = (self._root / text).resolve()
        root = self._root.resolve()
        if candidate != root and root not in candidate.parents:
            raise ValueError("存储键越出媒体目录")
        return candidate


_STORAGE: LocalMediaStorage | None = None


def get_media_storage() -> LocalMediaStorage:
    global _STORAGE
    if _STORAGE is None:
        _STORAGE = LocalMediaStorage(settings.TASK_MEDIA_DIR)
    return _STORAGE


def reset_media_storage() -> None:
    global _STORAGE
    _STORAGE = None
