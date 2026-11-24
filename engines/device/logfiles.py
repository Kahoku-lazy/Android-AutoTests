from __future__ import annotations

import os

from pathlib import Path

from utils.logs import serial_log

__all__ = ["tail_lines"]

READ_CHUNK_BYTES = 64 * 1024


def tail_lines(path: str | Path, limit: int) -> list[str]:
    target = Path(path)
    wanted = max(0, int(limit))
    if wanted == 0 or not target.is_file():
        return []
    chunks: list[bytes] = []
    newlines = 0
    try:
        with target.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            position = handle.tell()
            while position > 0:
                size = min(READ_CHUNK_BYTES, position)
                position -= size
                handle.seek(position)
                chunk = handle.read(size)
                chunks.append(chunk)
                newlines += chunk.count(b"\n")
                if newlines > wanted:
                    break
    except OSError as exc:
        serial_log.error("device log file read failed (%s): %s", target, exc)
        return []
    chunks.reverse()
    lines = b"".join(chunks).split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return [_strip_cr(chunk.decode("utf-8", errors="replace")) for chunk in lines[-wanted:]]


def _strip_cr(text: str) -> str:
    return text[:-1] if text.endswith("\r") else text
