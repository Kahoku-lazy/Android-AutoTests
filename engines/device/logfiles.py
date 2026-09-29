"""设备日志本地文件归档 —— `{SKU}_{端口}.log` 追加写入 + 定长轮转 + 尾部/范围读取。

定位（引擎层，零 `django` / 零 `apps` 依赖）：只认「目录 / 单文件上限 / SKU / 端口」几个参数，
文件句柄不出本模块；上层（`apps`）只经公开函数拿到行文本或行对象。

约定：

1. 当前文件固定叫 `{SKU}_{端口}.log`；写满单文件上限（默认 50MB）时，在写下一行之前改名存档为
   `{SKU}_{端口}_{YYYYMMDD}.log`；同一自然日内多次轮转追加 `_2`/`_3`…，**绝不覆盖**（宁可多留文件，不丢行）。
2. 查看只读当前文件；存档文件只归档，平台既不读取也不删除。
3. 一行一条：`北京时间毫秒 [来源] 原文`，UTF-8，写完即 flush（页面能立刻看到新行）。
4. 写文件失败（磁盘满 / 权限）只记录错误并冷却重试，MUST NOT 反过来影响采集与内存缓冲。

时间戳口径（`BEIJING_TZ` / `STAMP_FORMAT` / `line_epoch`）以本模块为真相源，`logbus` 从本模块导入，
使「内存缓冲」与「落盘文件」两条读取路径用同一套时间解析。
"""

from __future__ import annotations

import logging
import os
import re
import threading
import time

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

BEIJING_TZ = timezone(timedelta(hours=8))
STAMP_FORMAT = "%Y-%m-%d %H:%M:%S.%f"

logger = logging.getLogger(__name__)

__all__ = [
    "BEIJING_TZ",
    "DEFAULT_FILE_MAX_BYTES",
    "FileLine",
    "LogFileSink",
    "STAMP_FORMAT",
    "archive_file_name",
    "current_file_name",
    "line_epoch",
    "log_file_path",
    "parse_log_line",
    "range_lines",
    "tail_lines",
]

DEFAULT_FILE_MAX_BYTES = 50 * 1024 * 1024  # 50MB
READ_CHUNK_BYTES = 64 * 1024  # 尾部倒读块大小
MAX_ROTATE_INDEX = 9999  # 同日轮转的序号上限（超过视为异常，宁可报错也不覆盖）
RETRY_COOLDOWN_SECONDS = 30.0  # 写失败后的重试冷却，避免刷日志

_LINE_PATTERN = re.compile(
    r"^(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3})"
    r"\s+\[(?P<source>[^\]]*)\]\s?(?P<text>.*)$"
)


# ── 命名 ──────────────────────────────────────────────────────


def current_file_name(sku: str, port: int) -> str:
    """当前日志文件名：`{SKU}_{端口}.log`。"""
    return f"{_safe_segment(sku)}_{int(port)}.log"


def archive_file_name(sku: str, port: int, day: str, index: int = 1) -> str:
    """存档文件名：`{SKU}_{端口}_{日期}.log`；index > 1 时追加 `_2`/`_3`…（绝不覆盖）。"""
    suffix = "" if index <= 1 else f"_{int(index)}"
    return f"{_safe_segment(sku)}_{int(port)}_{day}{suffix}.log"


def log_file_path(directory: str | Path, sku: str, port: int) -> Path:
    """当前日志文件的完整路径。"""
    return Path(directory) / current_file_name(sku, port)


def _safe_segment(value: str) -> str:
    """文件名片段去危险字符（SKU 来自配置，不做路径拼接风险）。"""
    text = str(value or "").strip() or "unknown"
    return re.sub(r"[^0-9A-Za-z_.-]", "_", text)


def _day_of(line: Any) -> str:
    """轮转日期：优先取日志行时间戳的日期部分（北京时间），否则用本机当天。"""
    stamp = str(getattr(line, "timestamp", "") or "")
    if len(stamp) >= 10 and stamp[4] == "-" and stamp[7] == "-":
        return stamp[:10].replace("-", "")
    return datetime.now().strftime("%Y%m%d")


# ── 行格式 ────────────────────────────────────────────────────


def format_log_line(line: Any) -> str:
    """日志行 → 文件内容行：`时间戳 [来源] 原文`（含换行）。"""
    return f"{line.timestamp} [{line.source}] {line.text}\n"


@dataclass
class FileLine:
    """从日志文件读回的一行（字段与采集层的 LogLine 对齐，便于复用同一套合并口径）。"""

    timestamp: str
    source: str
    text: str
    port: int = 0


def parse_log_line(raw: str) -> FileLine | None:
    """文件行 → FileLine；格式不符（例如人工追加的内容）返回 None。"""
    matched = _LINE_PATTERN.match(raw.rstrip("\r\n"))
    if not matched:
        return None
    return FileLine(
        timestamp=matched.group("timestamp"),
        source=matched.group("source"),
        text=matched.group("text"),
    )


# ── 写入与轮转 ────────────────────────────────────────────────


class LogFileSink:
    """单个端口来源的日志文件写入器：追加、按上限轮转、目录自动创建。

    线程安全：采集线程可能多连接并发调用，内部串行化。
    """

    def __init__(
        self,
        *,
        sku: str,
        port: int,
        directory: str | Path,
        max_bytes: int = DEFAULT_FILE_MAX_BYTES,
    ) -> None:
        self._sku = str(sku or "unknown")
        self._port = int(port)
        self._directory = Path(directory)
        self._max_bytes = max(1024, int(max_bytes or DEFAULT_FILE_MAX_BYTES))
        self._handle = None
        self._size = 0
        self._retry_after = 0.0
        self._lock = threading.Lock()

    # ── 只读属性 ──

    @property
    def directory(self) -> Path:
        return self._directory

    @property
    def path(self) -> Path:
        return self._directory / self.file_name

    @property
    def file_name(self) -> str:
        return current_file_name(self._sku, self._port)

    @property
    def max_bytes(self) -> int:
        return self._max_bytes

    @property
    def size_bytes(self) -> int:
        """当前文件已写入的字节数（未打开时按磁盘实际大小）。"""
        with self._lock:
            return self._size_now()

    # ── 写入 ──

    def write(self, line: Any) -> bool:
        """追加一行；成功返回 True。任何 IO 失败只记录错误并返回 False。"""
        if time.monotonic() < self._retry_after:
            return False
        text = format_log_line(line)
        payload = len(text.encode("utf-8"))
        with self._lock:
            try:
                self._open()
                self._rotate_if_needed(payload, line)
                self._handle.write(text)
                self._handle.flush()
                self._size += payload
                return True
            except (OSError, ValueError) as exc:
                self._retry_after = time.monotonic() + RETRY_COOLDOWN_SECONDS
                logger.error("device log file write failed (%s): %s", self.path, exc)
                self._close()
                return False

    def close(self) -> None:
        with self._lock:
            self._close()

    # ── 内部 ──

    def _size_now(self) -> int:
        try:
            return self.path.stat().st_size
        except OSError:
            return 0

    def _open(self) -> None:
        if self._handle is not None:
            return
        self._directory.mkdir(parents=True, exist_ok=True)
        self._handle = self.path.open("a", encoding="utf-8", newline="\n")
        self._size = self._size_now()

    def _close(self) -> None:
        if self._handle is None:
            return
        try:
            self._handle.close()
        except OSError as exc:  # 关闭失败无需上报调用方，文件已 flush
            logger.warning("device log file close failed (%s): %s", self.path, exc)
        self._handle = None

    def _rotate_if_needed(self, incoming_bytes: int, line: Any) -> None:
        if self._size + incoming_bytes <= self._max_bytes:
            return
        if self._size == 0:  # 单行就超上限：留着写，避免「每行都轮转」
            return
        self._rotate(_day_of(line))

    def _rotate(self, day: str) -> None:
        """当前文件改名存档并重新开始写当前文件（MUST NOT 覆盖既有存档）。"""
        self._close()
        target = self._unique_archive_path(day)
        os.replace(self.path, target)
        logger.info(
            "device log rotated: %s → %s (max %d bytes)",
            self.file_name,
            target.name,
            self._max_bytes,
        )
        self._size = 0
        self._open()

    def _unique_archive_path(self, day: str) -> Path:
        for index in range(1, MAX_ROTATE_INDEX + 1):
            candidate = self._directory / archive_file_name(self._sku, self._port, day, index)
            if not candidate.exists():
                return candidate
        raise OSError(
            f"同日轮转次数超过 {MAX_ROTATE_INDEX}，拒绝覆盖 {self._directory} 下的既有存档"
        )


# ── 尾部读取 ──────────────────────────────────────────────────


def tail_lines(path: str | Path, limit: int) -> list[str]:
    """读文件尾部最多 limit 行（按块倒读，不整文件加载），返回原始顺序（旧→新）。

    文件不存在或不是文件时返回空列表；解析格式留给调用方（`parse_log_line`）。
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
                # 多读一块（+1）是为了判断是否还有更早的行，避免边界少一行
                if sum(chunk.count(b"\n") for chunk in chunks) > wanted:
                    break
    except OSError as exc:
        logger.error("device log file read failed (%s): %s", target, exc)
        return []
    lines = b"".join(chunks).split(b"\n")
    if lines and lines[-1] == b"":
        lines.pop()  # 文件以换行结尾时最后会多出一个空串
    return [_strip_cr(chunk.decode("utf-8", errors="replace")) for chunk in lines[-wanted:]]


def _strip_cr(text: str) -> str:
    """去掉 CRLF 残留的回车（外部工具写入的文件也可能是 CRLF）。"""
    return text[:-1] if text.endswith("\r") else text


# ── 时间戳 ↔ epoch（采集层与文件读取共用同一口径）────────────────


def line_epoch(stamp: str) -> float | None:
    """`YYYY-MM-DD HH:MM:SS.mmm`（北京时间）→ epoch；解析失败返回 None。"""
    try:
        moment = datetime.strptime(str(stamp).strip(), STAMP_FORMAT)
    except (TypeError, ValueError):
        return None
    return moment.replace(tzinfo=BEIJING_TZ).timestamp()


# ── 范围读取 ──────────────────────────────────────────────────


def _parse_rows(raw: bytes) -> list[FileLine]:
    """一段原始字节 → 可解析的行（跳过分片残行与人工追加的内容）。"""
    rows: list[FileLine] = []
    for item in raw.split(b"\n"):
        line = parse_log_line(_strip_cr(item.decode("utf-8", errors="replace")))
        if line is not None:
            rows.append(line)
    return rows


def _reaches_before(chunk: bytes, start_epoch: float) -> bool:
    """该块里是否已出现早于范围起点的行（文件时间递增 → 可以停止倒读）。"""
    for line in _parse_rows(chunk):
        moment = line_epoch(line.timestamp)
        if moment is not None and moment < start_epoch:
            return True
    return False


def range_lines(
    path: str | Path,
    start_epoch: float,
    end_epoch: float,
    limit: int = 5000,
) -> list[FileLine]:
    """读文件里落在 `[start_epoch, end_epoch]` 的行（尾部倒读，读到起点之前即停）。

    只用于「内存缓冲覆盖不到的历史时段」：文件是追加写的、时间戳递增，所以从文件尾部按块
    倒读、一旦块内出现早于 `start_epoch` 的行就可以停下，不必扫全文件。

    Args:
        path: 日志文件路径。
        start_epoch: 范围起点（含）。
        end_epoch: 范围终点（含）。
        limit: 最多返回的行数上限（超出时保留**最新**的一侧，保护上下文长度）。

    Returns:
        范围内可解析的行，按原始顺序（旧 → 新）；文件不存在 / 不可读 / 范围内没有行时返回空列表。
    """
    target = Path(path)
    wanted = max(0, int(limit))
    if wanted == 0 or not target.is_file():
        return []
    chunks: list[bytes] = []
    truncated_head = False
    try:
        with target.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            position = handle.tell()
            while position > 0:
                size = min(READ_CHUNK_BYTES, position)
                position -= size
                handle.seek(position)
                chunk = handle.read(size)
                chunks.insert(0, chunk)
                if _reaches_before(chunk, start_epoch):
                    break
            truncated_head = position > 0
    except OSError as exc:
        logger.error("device log range read failed (%s): %s", target, exc)
        return []
    parts = b"".join(chunks).split(b"\n")
    if truncated_head and parts:
        parts = parts[1:]  # 最早一块的前半行没有前文，丢弃以免解析出半个时间戳
    rows: list[FileLine] = []
    for line in _parse_rows(b"\n".join(parts)):
        moment = line_epoch(line.timestamp)
        if moment is None or not (start_epoch <= moment <= end_epoch):
            continue
        rows.append(line)
    return rows[-wanted:] if len(rows) > wanted else rows
