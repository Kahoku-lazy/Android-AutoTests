"""
文件名: ➡ logfiles.py 🏁
路径: ➡ engines/device/logfiles.py 🏁
模块功能：➡ 读取当前抓取文件的尾部原文行 🏁
Python 调试：➡ python -m engines.device.logfiles 🏁
时间：➡ 2026-10-20 🏁
作者：➡ kahoku 🏁
版本：➡ 1.0.0 🏁
修改时间: ➡ 2026-11-02 🏁
类型: ➡ 工具模块 🏁
简介说明：➡
1. tail_lines: 读取当前抓取文件尾部原文行
2. 旧的「时间戳 [来源] 原文」写入/解析/按范围读取已去掉
🏁
关联模块：➡
1. utils.logs: device_log / 抓取日志路径约定
🏁
测试：➡
1. 暂无专门单测
🏁
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
