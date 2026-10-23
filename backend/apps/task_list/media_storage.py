"""
python -m 调试路径: backend.apps.task_list.media_storage

本模块的业务功能如下：
1. encode: 把截图 base64 压成长边 720 的 WebP 缩略图，并给出原图 sha256。
2. LocalMediaStorage: 任务截图的本地文件读写（保存、读取、存在性、按任务删除）。
3. get_media_storage: 进程内一份存储实现，便于将来替换成对象存储。
"""

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
    """原图字节的 sha256，作为去重键与 ETag。"""
    return hashlib.sha256(raw).hexdigest()


def _to_webp(raw: bytes) -> tuple[bytes, int, int] | None:
    """
    把图片字节压成长边 720 的 WebP。

    Args:
        raw: 原始图片字节。

    Returns:
        (WebP 字节, 宽, 高)；无法解码时返回 None。
    """
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
    """
    解码截图并压成 WebP 缩略图。

    Args:
        image_b64: 截图 base64，允许带 data URI 前缀。

    Returns:
        {sha256, data, width, height, media_type}；坏图返回 None。
    """
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
    """
    把已有缩略图字节重新压成 WebP，供存量迁移使用。

    Args:
        raw: 已有缩略图字节（历史为 JPEG）。

    Returns:
        (WebP 字节, 宽, 高)；无法解码时返回 None。
    """
    return _to_webp(raw)


class LocalMediaStorage:
    """任务截图的本地文件存储：`<root>/<task_id>/<sha256>.webp`。"""

    def __init__(self, root: Path) -> None:
        self._root = Path(root)

    @property
    def root(self) -> Path:
        """媒体文件根目录。"""
        return self._root

    def build_key(self, task_id: int, sha256: str) -> str:
        """
        生成任务内唯一的存储键。

        Args:
            task_id: 任务编号。
            sha256: 原图 sha256（64 位十六进制）。

        Returns:
            形如 `142/ab12….webp` 的相对路径。

        Raises:
            ValueError: sha256 不是 64 位十六进制。
        """
        digest = (sha256 or "").strip().lower()
        if len(digest) != _SHA_LEN or any(ch not in "0123456789abcdef" for ch in digest):
            raise ValueError("sha256 必须是 64 位十六进制")
        return f"{int(task_id)}/{digest}.webp"

    def save(self, task_id: int, sha256: str, data: bytes) -> str:
        """
        原子写入一张缩略图。

        Args:
            task_id: 任务编号。
            sha256: 原图 sha256。
            data: WebP 字节。

        Returns:
            存储键。
        """
        key = self.build_key(task_id, sha256)
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_name(f"{path.name}.tmp")
        temp.write_bytes(data)
        os.replace(temp, path)
        return key

    def open(self, key: str) -> bytes | None:
        """
        读取存储键对应的字节。

        Args:
            key: 存储键；空值或非法路径返回 None。

        Returns:
            文件字节；不存在或越界时返回 None。
        """
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
        """存储键对应的文件是否存在。"""
        if not (key or "").strip():
            return False
        try:
            return self._path(key).is_file()
        except ValueError:
            return False

    def keys_for_task(self, task_id: int) -> set[str]:
        """列出任务目录下现有的存储键；目录不存在时为空集。"""
        directory = self._root / str(int(task_id))
        if not directory.is_dir():
            return set()
        prefix = f"{int(task_id)}/"
        return {f"{prefix}{entry.name}" for entry in directory.iterdir() if entry.is_file()}

    def delete(self, key: str) -> bool:
        """删除一张缩略图；不存在或非法路径返回 False。"""
        try:
            self._path(key).unlink()
        except (OSError, ValueError):
            return False
        return True

    def delete_task(self, task_id: int) -> None:
        """删除一个任务的全部截图文件。"""
        shutil.rmtree(self._root / str(int(task_id)), ignore_errors=True)

    def _path(self, key: str) -> Path:
        """
        把存储键解析成本地路径，并阻止越出根目录。

        Args:
            key: 存储键。

        Returns:
            根目录内的绝对路径。

        Raises:
            ValueError: 键为空、是绝对路径或解析后越出根目录。
        """
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
    """进程内一份本地存储实现。"""
    global _STORAGE
    if _STORAGE is None:
        _STORAGE = LocalMediaStorage(settings.TASK_MEDIA_DIR)
    return _STORAGE


def reset_media_storage() -> None:
    """丢弃进程内实例，下次按当前 settings 重建（测试与配置变更后使用）。"""
    global _STORAGE
    _STORAGE = None
