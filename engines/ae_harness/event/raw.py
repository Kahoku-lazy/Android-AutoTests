from __future__ import annotations

import base64
import binascii
import hashlib
import json
import time

from dataclasses import asdict, is_dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

__all__ = ["RawEventDump", "save_media"]

_MEDIA_MIN_CHARS = 256
_SUFFIXES = {
    "image/png": "png",
    "image/jpeg": "jpg",
    "image/webp": "webp",
    "image/gif": "gif",
}


def _stamp() -> str:
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S.%f")[:-3]


def _plain(value: Any) -> Any:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, Enum):
        return _plain(value.value)
    if isinstance(value, dict):
        return {str(key): _plain(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set, frozenset)):
        return [_plain(item) for item in value]
    if isinstance(value, (bytes, bytearray)):
        return {"bytes": len(value)}
    if isinstance(value, Path):
        return value.as_posix()
    if is_dataclass(value) and not isinstance(value, type):
        return _plain(asdict(value))
    return repr(value)


def save_media(fields: dict, media_dir: Path, *, as_url: bool = False) -> dict:
    data = fields.get("data")
    if not isinstance(data, str) or len(data) < _MEDIA_MIN_CHARS:
        return _save_source(fields, media_dir, as_url)
    media_type = str(fields.get("media_type") or "application/octet-stream")
    suffix = _SUFFIXES.get(media_type, "bin")
    try:
        payload = base64.b64decode(data, validate=False)
    except (binascii.Error, ValueError):
        payload = data.encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    name = f"{fields.get('block_id') or 'media'}_{digest[:8]}.{suffix}"
    media_dir.mkdir(parents=True, exist_ok=True)
    target = media_dir / name
    target.write_bytes(payload)
    fields = dict(fields)
    if as_url:
        fields["data"] = None
        fields["url"] = target.resolve().as_uri()
        return fields
    fields["data"] = {
        "saved_to": name,
        "chars": len(data),
        "bytes": len(payload),
        "sha256": digest,
    }
    return fields


def _save_source(fields: dict, media_dir: Path, as_url: bool) -> dict:
    source = fields.get("source")
    if not as_url or not isinstance(source, dict):
        return fields
    data = source.get("data")
    if not isinstance(data, str) or len(data) < _MEDIA_MIN_CHARS:
        return fields
    media_type = str(source.get("media_type") or "application/octet-stream")
    suffix = _SUFFIXES.get(media_type, "bin")
    try:
        payload = base64.b64decode(data, validate=False)
    except (binascii.Error, ValueError):
        payload = data.encode("utf-8")
    digest = hashlib.sha256(payload).hexdigest()
    name = f"{fields.get('block_id') or 'media'}_{digest[:8]}.{suffix}"
    media_dir.mkdir(parents=True, exist_ok=True)
    target = media_dir / name
    target.write_bytes(payload)
    fields = dict(fields)
    fields["source"] = {
        "type": "url",
        "url": target.resolve().as_uri(),
        "media_type": media_type,
    }
    return fields


class RawEventDump:
    def __init__(
        self,
        path: Path,
        *,
        media_dir: Path | None = None,
        inline_media: bool = False,
    ) -> None:
        self.path = path
        self.media_dir = media_dir if media_dir is not None else path.parent / f"{path.stem}.media"
        self.inline_media = bool(inline_media)
        self._handle = None
        self._seq = 0
        self._begin = 0.0

    def begin(self, meta: dict | None = None) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("w", encoding="utf-8")
        self._begin = time.perf_counter()
        self._write("dump_begin", _plain(dict(meta or {})))

    def feed(self, event: object) -> None:
        self._write(
            type(event).__name__,
            self._fields(event),
            created_at=str(getattr(event, "created_at", "") or ""),
        )

    def end(self, payload: dict | None = None) -> None:
        self._write("dump_end", _plain(dict(payload or {})))

    def emit(self, kind: str, fields: Any) -> None:
        self._write(kind, _plain(fields))

    def close(self) -> None:
        if self._handle is not None:
            self._handle.close()
            self._handle = None

    def _fields(self, event: object) -> Any:
        dump = getattr(event, "model_dump", None)
        if callable(dump):
            try:
                raw = dump(mode="python")
            except TypeError:
                raw = dump()
        elif is_dataclass(event) and not isinstance(event, type):
            raw = asdict(event)
        else:
            raw = dict(vars(event))
        fields = _plain(raw)
        if isinstance(fields, dict):
            return self._split_media(fields)
        return fields

    def _split_media(self, fields: dict) -> dict:
        if self.inline_media:
            return fields
        return save_media(fields, self.media_dir)

    def _write(self, kind: str, fields: Any, *, created_at: str = "") -> None:
        if self._handle is None:
            return
        self._seq += 1
        row = {
            "seq": self._seq,
            "at": created_at or _stamp(),
            "recv_ms": round((time.perf_counter() - self._begin) * 1000, 3),
            "type": kind,
            "fields": fields,
        }
        self._handle.write(json.dumps(row, ensure_ascii=False, default=repr) + "\n")
        self._handle.flush()
