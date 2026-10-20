"""读取当前抓取文件的尾部原文行。

旧的「时间戳 [来源] 原文」写入、解析和按范围读取已去掉。
"""

from __future__ import annotations

import os

from pathlib import Path

from utils.logs import serial_log

__all__ = ["tail_lines"]

READ_CHUNK_BYTES = 64 * 1024


def tail_lines(path: str | Path, limit: int) -> list[str]:
    """读文件尾部最多 limit 行，返回文件顺序（旧→新）。

    文件不存在或不是文件时返回空列表。
    """
    target = Path(path)
    wanted = max(0, int(limit))
    if wanted == 0 or not target.is_file():
        return []
    chunks: list[bytes] = []
    try:
        with target.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            position = handle.tell()
            while position > 0:
                size = min(READ_CHUNK_BYTES, position)
                position -= size
                handle.seek(position)
                chunks.insert(0, handle.read(size))
                if sum(chunk.count(b"\n") for chunk in chunks) > wanted:
                    break
    except OSError as exc:
        serial_log.error("device log file read failed (%s): %s", target, exc)
        return []
    lines = b"".join(chunks).split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()
    return [_strip_cr(chunk.decode("utf-8", errors="replace")) for chunk in lines[-wanted:]]


def _strip_cr(text: str) -> str:
    """去掉 CRLF 残留的回车。"""
    return text[:-1] if text.endswith("\r") else text
