"""设备日志总线 —— 常驻采集 + 按设备缓冲 + 动作证据窗口。

定位（引擎层，零 `django` / 零 `apps` 依赖）：

1. **常驻采集**设备日志：TCP 监听（设备主动连入）与串口两条来源；采集不随单次动作开关。
2. 每条日志在**收到时刻**打上北京时间毫秒时间戳，按通道（设备）隔离进环形缓冲。
3. 为「执行模型动作 → 验收模型判定」提供**动作证据窗口**：开窗 → 动作 → 读窗；
   读窗按「动作发出时刻 + 阈值」筛选窗口日志，逐条标注证据等级。

边界：串口 / TCP 句柄只出现在本模块；上层（`apps`）只经公开函数访问，不持有句柄。
时间戳一律北京时间（固定 UTC+8，不依赖 `tzdata`），因为设备日志本身不带时间字段。
"""

from __future__ import annotations

import json
import logging
import socket
import threading
import time

from collections import deque
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Protocol

from .logfiles import (
    BEIJING_TZ,
    DEFAULT_FILE_MAX_BYTES,
    STAMP_FORMAT,
    LogFileSink,
    log_file_path,
    range_lines,
)

logger = logging.getLogger(__name__)

__all__ = [
    "CONCLUSION_HIT",
    "CONCLUSION_NO_HIT",
    "CONCLUSION_NO_LOG",
    "CONCLUSION_OUT_OF_WINDOW",
    "DEFAULT_CHANNEL",
    "GRADE_BEFORE",
    "GRADE_OUT",
    "GRADE_PERIODIC",
    "GRADE_STRONG",
    "KeywordIndex",
    "LogBus",
    "LogBusConfig",
    "LogEvidenceProvider",
    "LogLine",
    "LogSourceSpec",
    "LogSourceUnknown",
    "build_evidence",
    "get_log_bus",
    "get_or_create_log_bus",
    "merge_lines_by_timestamp",
    "now_stamp",
    "parse_stamp",
    "start_log_bus",
    "stop_log_bus",
]

DEFAULT_CHANNEL = "*"  # 未按设备分通道时的共享通道
DEFAULT_WINDOW_SECONDS = 5.0  # 动作后取证阈值
DEFAULT_BASELINE_SECONDS = 30.0  # 动作前基线窗口
DEFAULT_BUFFER_SECONDS = 600.0  # 缓冲保留时长
DEFAULT_BUFFER_MAX_LINES = 20000  # 单通道最大行数
SERIAL_RETRY_SECONDS = 3.0
LINE_LIMIT = 4096
MAX_WINDOWS = 64  # 保留的窗口数（够一次任务的全部步骤）
FILE_RANGE_MAX_LINES = 5000  # 单次按范围回读文件的行数上限（保护上下文与内存）

GRADE_STRONG = "strong"  # 强证据：窗口内首现且动作前基线未出现
GRADE_PERIODIC = "periodic"  # 疑似周期：窗口内出现但动作前基线已出现同名
GRADE_BEFORE = "before_action"  # 动作前的相近日志（仅作上下文）
GRADE_OUT = "out_of_window"  # 晚于「动作 + 阈值」，不作为本次证据

CONCLUSION_HIT = "hit"
CONCLUSION_NO_HIT = "no_hit"
CONCLUSION_NO_LOG = "no_log"
CONCLUSION_OUT_OF_WINDOW = "out_of_window"


# ── 时间戳（北京时间，毫秒）────────────────────────────────────


def format_stamp(moment: datetime) -> str:
    """datetime → `YYYY-MM-DD HH:MM:SS.mmm`（毫秒）。"""
    return moment.astimezone(BEIJING_TZ).strftime(STAMP_FORMAT)[:-3]


def now_stamp() -> str:
    """当前北京时间，精确到毫秒。"""
    return format_stamp(datetime.now(BEIJING_TZ))


def parse_stamp(text: str) -> datetime | None:
    """`YYYY-MM-DD HH:MM:SS.mmm` → 北京时间 datetime；解析失败返回 None。"""
    if not text:
        return None
    try:
        return datetime.strptime(text.strip(), STAMP_FORMAT).replace(tzinfo=BEIJING_TZ)
    except ValueError:
        return None


def _epoch(text: str) -> float:
    moment = parse_stamp(text)
    return moment.timestamp() if moment else time.time()


# ── 关键词索引（数据驱动，改表不改代码）──────────────────────


def _merge_log_sources(buffered: list[LogLine], on_disk: list[LogLine]) -> list[LogLine]:
    """缓冲行与文件行按（时间戳、来源、原文）去重合并，按时间升序返回（缓冲优先）。"""
    seen: set[tuple[str, str, str]] = set()
    merged: list[LogLine] = []
    for line in list(buffered) + list(on_disk):
        key = (line.timestamp, line.source, line.text)
        if key in seen:
            continue
        seen.add(key)
        merged.append(line)
    return sorted(merged, key=lambda item: item.epoch)


class KeywordIndex:
    """「串口日志关键词 → 功能模块 / 功能点」索引，带最长匹配消解。"""

    def __init__(self, mapping: dict[str, list[dict[str, Any]]] | None = None) -> None:
        self._map: dict[str, list[dict[str, Any]]] = dict(mapping or {})
        # 长关键词优先，避免短关键词先认掉长关键词的一部分
        self._ordered: list[str] = sorted(self._map, key=len, reverse=True)

    @classmethod
    def from_file(cls, path: str | Path) -> KeywordIndex:
        """从数据文件加载；文件缺失或损坏时返回空索引并记录可读错误。"""
        target = Path(path)
        if not str(path).strip():
            logger.info("device log keyword file not configured; keyword matching disabled")
            return cls()
        if not target.exists():
            logger.error("device log keyword file missing: %s", target)
            return cls()
        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            logger.error("device log keyword file unreadable: %s (%s)", target, exc)
            return cls()
        mapping = raw.get("keywords") if isinstance(raw, dict) else raw
        if not isinstance(mapping, dict):
            logger.error("device log keyword file has unexpected shape: %s", target)
            return cls()
        index = cls(mapping)
        logger.info("device log keywords loaded: %d keywords from %s", len(index), target)
        return index

    def __bool__(self) -> bool:
        return bool(self._map)

    def __len__(self) -> int:
        return len(self._map)

    @property
    def mapping(self) -> dict[str, list[dict[str, Any]]]:
        return self._map

    def match(self, text: str) -> list[tuple[str, list[dict[str, Any]]]]:
        """返回该行命中的 (关键词, 功能点列表)，按出现先后排序，剔除被长关键词包住的命中。"""
        if not self._map or not text:
            return []
        lowered = text.lower()
        spans: list[tuple[int, int, str]] = []
        for keyword in self._ordered:
            start = lowered.find(keyword)
            while start >= 0:
                spans.append((start, start + len(keyword), keyword))
                start = lowered.find(keyword, start + 1)
        if not spans:
            return []
        spans.sort(key=lambda item: (item[0], -(item[1] - item[0])))
        kept: list[tuple[int, int, str]] = []
        for span in spans:
            # 被更长关键词整段包住的忽略（如 video_sound_effect_open 落在 viewing_..._open 里）
            if any(span[0] >= start and span[1] <= end for start, end, _ in kept):
                continue
            kept.append(span)
        hits: list[tuple[str, list[dict[str, Any]]]] = []
        seen: set[str] = set()
        for _, _, keyword in kept:
            if keyword in seen:
                continue
            seen.add(keyword)
            hits.append((keyword, self._map[keyword]))
        return hits


# ── 缓冲 ──────────────────────────────────────────────────────


@dataclass
class LogLine:
    """一行设备日志（时间戳为采集层收到该行的北京时间）。"""

    channel: str
    timestamp: str
    epoch: float
    source: str
    text: str
    port: int = 0  # 来源端口（串口来源为 0）；用于「按端口查询」

    def as_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "source": self.source,
            "port": self.port,
            "text": self.text,
        }


class _ChannelBuffer:
    """单通道环形缓冲：保留时长 + 最大行数双上限，先进先出淘汰。"""

    def __init__(self, max_lines: int, buffer_seconds: float) -> None:
        self._lines: deque[LogLine] = deque(maxlen=max(1, max_lines))
        self._buffer_seconds = max(1.0, buffer_seconds)
        self._lock = threading.Lock()

    def append(self, line: LogLine) -> None:
        with self._lock:
            self._lines.append(line)
            self._evict(line.epoch)

    def _evict(self, now: float) -> None:
        cutoff = now - self._buffer_seconds
        while self._lines and self._lines[0].epoch < cutoff:
            self._lines.popleft()

    def since(self, epoch: float) -> list[LogLine]:
        with self._lock:
            return [line for line in self._lines if line.epoch >= epoch]

    def between(self, start_epoch: float, end_epoch: float) -> list[LogLine]:
        with self._lock:
            return [line for line in self._lines if start_epoch <= line.epoch <= end_epoch]

    def __len__(self) -> int:
        with self._lock:
            return len(self._lines)


class _Windows:
    """窗口登记：窗口标识 → 通道 / 起点；保留最近若干个窗口。"""

    def __init__(self, limit: int = MAX_WINDOWS) -> None:
        self._items: deque[dict[str, Any]] = deque(maxlen=limit)
        self._counter = 0
        self._lock = threading.Lock()

    def open(self, channel: str, label: str) -> dict[str, Any]:
        with self._lock:
            self._counter += 1
            window = {
                "window_id": f"w{self._counter}",
                "channel": channel,
                "label": label,
                "opened_at": now_stamp(),
                "opened_epoch": time.time(),
            }
            self._items.append(window)
            return dict(window)

    def latest(self, channel: str | None = None) -> dict[str, Any] | None:
        with self._lock:
            for window in reversed(self._items):
                if channel is None or window["channel"] == channel:
                    return dict(window)
        return None

    def get(self, window_id: str) -> dict[str, Any] | None:
        with self._lock:
            for window in self._items:
                if window["window_id"] == window_id:
                    return dict(window)
        return None


# ── 证据筛选 ──────────────────────────────────────────────────


def merge_lines_by_timestamp(
    lines: list[LogLine], *, with_port: bool = False
) -> list[dict[str, Any]]:
    """同一时刻的日志合并成一条：时间戳 + 来源相同即视为同一条，text 以换行连接。

    设备一次事件常在同一毫秒打出一串日志（`request → start → switch_off`），逐行摊开既长又难读；
    合并后 `text` 内部保留 `\\n`，读起来就是那一刻的完整经过。
    不同来源（tcp / serial）即使时间戳相同也 MUST NOT 合并，避免混淆来源。

    排序：**最新时间在最上面**（按时间戳倒序）；同一条记录内部仍保持原始先后顺序
    （那一刻的经过必须按发生顺序读），同一时间戳的多个来源之间保持采集到的先后。
    """
    merged: list[dict[str, Any]] = []
    index: dict[tuple[str, str], int] = {}
    for line in lines:
        key = (line.timestamp, line.source)
        position = index.get(key)
        if position is not None:
            merged[position]["text"] = f"{merged[position]['text']}\n{line.text}"
            continue
        index[key] = len(merged)
        entry: dict[str, Any] = {
            "timestamp": line.timestamp,
            "source": line.source,
            "text": line.text,
        }
        if with_port:
            entry["port"] = line.port
        merged.append(entry)
    # 稳定排序：时间戳倒序（最新在上），相同时间戳保持采集先后
    merged.sort(key=lambda item: item["timestamp"], reverse=True)
    return merged


def _grade_lines(
    occurrences: list[LogLine],
    *,
    intervals: list[tuple[float, float]],
    first_action_epoch: float,
    window_end: float,
    baseline_start: float,
) -> tuple[list[LogLine], list[LogLine], list[LogLine]]:
    """把某关键词的出现按时间切成 (证据窗内, 动作前基线内, 超窗)。

    证据窗是**每次动作各自 [动作, 动作+阈值] 的并集**：真机上一步会有多次点击，
    只认首次动作会把「倒数第二次点击后 0.6 秒的响应」判成超窗（实测踩到过）。
    落在本步内、但不落在任何一次动作响应窗内的行不进等级列表，仍留在原始日志里。
    """
    inside: list[LogLine] = []
    baseline: list[LogLine] = []
    outside: list[LogLine] = []
    for line in occurrences:
        if any(start <= line.epoch <= end for start, end in intervals):
            inside.append(line)
        elif baseline_start <= line.epoch < first_action_epoch:
            baseline.append(line)
        elif line.epoch > window_end:
            outside.append(line)
    return inside, baseline, outside


def build_evidence(
    *,
    channel: str,
    window_id: str,
    window_opened_at: str,
    lines: list[LogLine],
    keywords: KeywordIndex,
    action_times: list[str] | None = None,
    action_time: str = "",
    threshold_seconds: float = DEFAULT_WINDOW_SECONDS,
    baseline_seconds: float = DEFAULT_BASELINE_SECONDS,
) -> dict[str, Any]:
    """按「本步每次动作发出时刻 + 阈值」筛选日志并标注等级（纯函数，便于单测）。

    Args:
        lines: 候选日志（窗口开启时刻起、含动作前基线区间）。
        action_times: 本步**全部**副作用动作的发出时刻（北京时间毫秒）；并集取证据窗。
        action_time: 单动作调用方式的兼容入口（等价于只传一个 action_times）。
        两者都为空时退化为窗口开启时刻。
        threshold_seconds: 每次动作后的取证阈值。
        baseline_seconds: 动作前基线窗口长度（用于判定疑似周期）。
        threshold_seconds: 动作后取证阈值。
        baseline_seconds: 动作前基线窗口长度（用于判定疑似周期）。
    """
    stamps = [stamp for stamp in (action_times or []) if stamp]
    if action_time:
        stamps.append(action_time)
    if not stamps:
        stamps = [window_opened_at]
    actions = sorted(_epoch(stamp) for stamp in stamps)
    first_action_epoch = actions[0]
    last_action_epoch = actions[-1]
    threshold = max(0.0, threshold_seconds)
    intervals = [(epoch, epoch + threshold) for epoch in actions]
    opened_epoch = _epoch(window_opened_at)
    window_end = last_action_epoch + threshold
    baseline_start = first_action_epoch - max(0.0, baseline_seconds)

    window_lines = [line for line in lines if line.epoch >= opened_epoch]
    hits: list[dict[str, Any]] = []
    before_action: list[dict[str, Any]] = []
    out_of_window: list[dict[str, Any]] = []

    occurrences: dict[str, list[LogLine]] = {}
    features_of: dict[str, list[dict[str, Any]]] = {}
    for line in window_lines:
        for keyword, features in keywords.match(line.text):
            occurrences.setdefault(keyword, []).append(line)
            features_of[keyword] = features

    for keyword, keyword_lines in occurrences.items():
        inside, baseline, outside = _grade_lines(
            keyword_lines,
            intervals=intervals,
            first_action_epoch=first_action_epoch,
            window_end=window_end,
            baseline_start=baseline_start,
        )
        for line in baseline:
            before_action.append(
                {
                    "keyword": keyword,
                    "timestamp": line.timestamp,
                    "text": line.text,
                    "grade": GRADE_BEFORE,
                }
            )
        for line in outside:
            out_of_window.append(
                {
                    "keyword": keyword,
                    "timestamp": line.timestamp,
                    "text": line.text,
                    "grade": GRADE_OUT,
                    "delta_seconds": round(line.epoch - last_action_epoch, 3),
                }
            )
        if not inside:
            continue
        grade = GRADE_PERIODIC if baseline else GRADE_STRONG
        hits.append(
            {
                "keyword": keyword,
                "grade": grade,
                "count": len(inside),
                "timestamps": [line.timestamp for line in inside],
                "occurrences": [
                    {
                        "timestamp": line.timestamp,
                        "source": line.source,
                        "text": line.text,
                        "grade": grade,
                    }
                    for line in inside
                ],
                "features": features_of.get(keyword, []),
                "baseline_occurrences": [
                    {"timestamp": line.timestamp, "text": line.text} for line in baseline
                ],
            }
        )

    if not window_lines:
        conclusion = CONCLUSION_NO_LOG
    elif hits:
        conclusion = CONCLUSION_HIT
    elif out_of_window:
        conclusion = CONCLUSION_OUT_OF_WINDOW
    else:
        conclusion = CONCLUSION_NO_HIT

    return {
        "channel": channel,
        "window_id": window_id,
        "window_opened_at": window_opened_at,
        "action_time": stamps[0],
        "action_times": stamps,
        "threshold_seconds": threshold_seconds,
        "baseline_seconds": baseline_seconds,
        "window_line_count": len(window_lines),
        "conclusion": conclusion,
        "hits": hits,
        "before_action": before_action,
        "out_of_window": out_of_window,
        # 同一时刻的日志合并为一条（text 内保留换行），供验收模型按「那一刻」阅读
        "lines": merge_lines_by_timestamp(window_lines, with_port=True),
    }


# ── 总线 ──────────────────────────────────────────────────────


@dataclass(frozen=True)
class LogSourceSpec:
    """一条日志来源登记：端口 + SKU（通道名）+ 波特率。

    波特率是**无线串口盒串口侧的参数**，只作端口管理页展示，不参与采集（采集走 TCP 监听）。
    """

    port: int
    sku: str = DEFAULT_CHANNEL
    baud: int = 0

    @property
    def channel(self) -> str:
        """该来源在缓冲里的通道名（用被测设备 SKU，证据里也标这个名）。"""
        return self.sku or DEFAULT_CHANNEL


@dataclass
class LogBusConfig:
    """采集与判定配置（由 Django 侧从 settings 组装后传入）。"""

    enabled: bool = True
    tcp_host: str = "0.0.0.0"
    tcp_port: int = 7005  # 0 = 不监听网络来源
    serial_port: str = ""  # 空 = 不采集串口
    serial_baud: int = 115200
    buffer_seconds: float = DEFAULT_BUFFER_SECONDS
    buffer_max_lines: int = DEFAULT_BUFFER_MAX_LINES
    window_seconds: float = DEFAULT_WINDOW_SECONDS
    baseline_seconds: float = DEFAULT_BASELINE_SECONDS
    keyword_file: str = ""
    channel: str = DEFAULT_CHANNEL
    # 日志来源登记（显式形态）：端口 + SKU + 波特率
    sources: list[LogSourceSpec] = field(default_factory=list)
    # 日志来源登记（兼容形态）：端口 → 通道；sources 为空时据此退化出单端口来源
    source_channels: dict[int, str] = field(default_factory=dict)
    # 日志文件归档（device-log-file-archive）：目录为空 = 不落文件
    log_dir: str = ""
    file_max_bytes: int = DEFAULT_FILE_MAX_BYTES


class LogEvidenceProvider(Protocol):
    """给 AI 引擎注入的日志证据协议（仅标准库类型，引擎不碰设备句柄）。"""

    def open_window(self, device: str, label: str = "") -> str: ...

    def read_window(
        self,
        device: str,
        window_id: str = "",
        action_times: list[str] | None = None,
        wait_seconds: float = 0.0,
    ) -> dict[str, Any]: ...


class LogBus:
    """设备日志总线：采集线程 + 按通道缓冲 + 窗口证据。"""

    def __init__(self, config: LogBusConfig | None = None) -> None:
        self._config = config or LogBusConfig()
        self._buffers: dict[str, _ChannelBuffer] = {}
        self._buffers_lock = threading.Lock()
        self._windows = _Windows()
        self._keywords = KeywordIndex.from_file(self._config.keyword_file)
        self._stop_event = threading.Event()
        self._threads: list[threading.Thread] = []
        self._started = False
        self._device_channels: dict[str, str] = {}
        self._lock = threading.RLock()
        # 按端口持有的 TCP 采集线程、日志文件写入器、真正绑定成功的端口集合
        self._collectors: dict[int, _TcpCollector] = {}
        self._sinks: dict[int, LogFileSink] = {}
        self._listening: set[int] = set()
        self._collectors_lock = threading.RLock()

    # ── 配置与状态 ──

    @property
    def running(self) -> bool:
        return self._started

    @property
    def bound_port(self) -> int | None:
        """实际监听的端口（仅当恰好一个来源在监听时给出，兼容单端口用法）。"""
        ports = self.running_ports()
        return ports[0] if len(ports) == 1 else None

    @property
    def keywords(self) -> KeywordIndex:
        return self._keywords

    def resolve_channel(self, device: str = "") -> str:
        """设备 → 通道：显式注册过就用注册值，否则用默认通道。"""
        if device and device in self._device_channels:
            return self._device_channels[device]
        return self._config.channel

    def register_device_channel(self, device: str, channel: str) -> None:
        self._device_channels[device] = channel

    # ── 只读查询（供业务工具使用，不去连端口）──

    def _specs(self) -> list[LogSourceSpec]:
        """有效的日志来源登记：显式 `sources` 优先，否则由兼容形态 / 单端口配置退化。"""
        if self._config.sources:
            return [spec for spec in self._config.sources if int(spec.port or 0)]
        if self._config.source_channels:
            baud = int(self._config.serial_baud or 0)
            return [
                LogSourceSpec(port=int(port), sku=str(channel), baud=baud)
                for port, channel in self._config.source_channels.items()
            ]
        if self._config.tcp_port:
            return [
                LogSourceSpec(
                    port=int(self._config.tcp_port),
                    sku=self._config.channel,
                    baud=int(self._config.serial_baud or 0),
                )
            ]
        return []

    def source_specs(self) -> list[LogSourceSpec]:
        """配置里登记的全部日志来源（端口 / SKU / 波特率）。"""
        return self._specs()

    def spec_for_port(self, port: int) -> LogSourceSpec | None:
        for spec in self._specs():
            if int(spec.port) == int(port):
                return spec
        return None

    def _sources(self) -> dict[int, str]:
        """「端口 → 通道」视图（按端口读范围与反查用）。"""
        return {int(spec.port): spec.channel for spec in self._specs()}

    def configured_ports(self) -> list[int]:
        return sorted(self._sources())

    def channel_for_port(self, port: int | None) -> str:
        """端口 → 通道；未登记的端口抛 LogSourceUnknown（调用方转成可读结论，不做连接）。"""
        sources = self._sources()
        if port:
            channel = sources.get(int(port))
            if channel is None:
                raise LogSourceUnknown(f"端口 {int(port)} 未配置为日志来源")
            return channel
        first = next(iter(self._specs()), None)
        if first is not None:
            return first.channel
        return self._config.channel

    def read_range(
        self,
        *,
        start_epoch: float,
        end_epoch: float,
        port: int | None = None,
        channel: str = "",
        file_limit: int = FILE_RANGE_MAX_LINES,
    ) -> dict[str, Any]:
        """按时间范围读取原始日志行（只读；端口只用于选通道）。

        数据源 = **内存缓冲 ∪ 该端口已落盘的日志文件**：缓冲只保留最近一段（`buffer_seconds`）
        与上限行数，早于它的时刻必须从日志文件回溯，否则「查不到」会被误读成「设备没打日志」。
        两路结果按（时间戳、来源、原文）去重后按时间升序返回，并回报各自行数供排查取数来源。
        """
        target = channel or self.channel_for_port(port)
        with self._buffers_lock:
            buffer = self._buffers.get(target)
        buffered = buffer.between(start_epoch, end_epoch) if buffer else []
        target_port = (
            int(port)
            if port
            else next((item for item, name in self._sources().items() if name == target), 0)
        )
        on_disk = self._file_range(target_port, target, start_epoch, end_epoch, file_limit)
        return {
            "channel": target,
            "port": target_port,
            "lines": _merge_log_sources(buffered, on_disk),
            "buffer_lines": len(buffered),
            "file_lines": len(on_disk),
        }

    def _file_range(
        self,
        port: int,
        channel: str,
        start_epoch: float,
        end_epoch: float,
        limit: int,
    ) -> list[LogLine]:
        """从该端口的日志文件里回溯时间范围；未落盘 / 未登记时返回空（不抛错）。"""
        log_dir = str(self._config.log_dir or "")
        if not log_dir or not port:
            return []
        spec = self.spec_for_port(port)
        if spec is None:
            return []
        path = log_file_path(log_dir, spec.sku, spec.port)
        rows: list[LogLine] = []
        for item in range_lines(path, start_epoch, end_epoch, limit):
            moment = parse_stamp(item.timestamp)
            if moment is None:
                continue
            rows.append(
                LogLine(
                    channel=channel,
                    timestamp=item.timestamp,
                    epoch=moment.timestamp(),
                    source=item.source,
                    text=item.text,
                    port=int(spec.port),
                )
            )
        return rows

    # ── 采集 ──

    def start(self) -> bool:
        """启动配置里登记的全部来源（一键全起；单端口启停见 `start_source`）。

        开关关闭或缺配置时不算失败，返回是否真的起了线程。
        """
        with self._lock:
            if self._started:
                return True
            if not self._config.enabled:
                logger.info("device log bus disabled by config; collectors not started")
                return False
            started = False
            for spec in self._specs():
                if self.start_source(spec.port):
                    started = True
            if self._config.serial_port:
                collector = _SerialCollector(
                    self, self._config.serial_port, self._config.serial_baud
                )
                self._threads.append(collector)
                collector.start()
                started = True
            self._started = True
            if not started:
                logger.warning(
                    "device log bus started with no source configured (no tcp port, no serial)"
                )
            return started

    def start_source(self, port: int) -> bool:
        """启动单个端口的监听（幂等：已在监听直接返回 True，不产生第二个线程）。"""
        spec = self.spec_for_port(port)
        if spec is None:
            logger.error("device log source %s not configured; not started", port)
            return False
        if not self._config.enabled:
            logger.info("device log bus disabled by config; source %s not started", spec.port)
            return False
        with self._lock:
            with self._collectors_lock:
                existing = self._collectors.get(int(spec.port))
                if existing is not None and existing.is_alive():
                    return True
                collector = _TcpCollector(
                    self,
                    self._config.tcp_host,
                    int(spec.port),
                    spec.channel,
                    self._sink_for(spec),
                )
                self._collectors[int(spec.port)] = collector
            collector.start()
            self._started = True
            return True

    def stop_source(self, port: int) -> bool:
        """停止单个端口的监听并释放端口；未在监听返回 False（不算错误）。"""
        with self._collectors_lock:
            collector = self._collectors.pop(int(port), None)
        if collector is None:
            return False
        collector.stop()
        return True

    def running_ports(self) -> list[int]:
        """当前**真正绑定成功**在监听的端口（绑定失败的不算）。"""
        with self._collectors_lock:
            return sorted(self._listening)

    def is_listening(self, port: int) -> bool:
        with self._collectors_lock:
            return int(port) in self._listening

    def _mark_listening(self, port: int, listening: bool) -> None:
        with self._collectors_lock:
            if listening:
                self._listening.add(int(port))
            else:
                self._listening.discard(int(port))

    def _sink_for(self, spec: LogSourceSpec) -> LogFileSink | None:
        """该来源的日志文件写入器；未配置日志目录时返回 None（只进内存缓冲）。"""
        if not self._config.log_dir:
            return None
        with self._collectors_lock:
            sink = self._sinks.get(int(spec.port))
            if sink is None:
                sink = LogFileSink(
                    sku=spec.channel,
                    port=int(spec.port),
                    directory=self._config.log_dir,
                    max_bytes=int(self._config.file_max_bytes),
                )
                self._sinks[int(spec.port)] = sink
            return sink

    def stop(self) -> None:
        """停止全部来源（含串口）并释放端口。"""
        self._stop_event.set()
        for port in list(self._collectors):
            self.stop_source(port)
        for thread in self._threads:
            thread.join(timeout=2)
        self._threads.clear()
        for sink in list(self._sinks.values()):
            sink.close()
        with self._lock:
            self._started = False
        logger.info("device log bus stopped")

    # ── 数据 ──

    def feed(self, text: str, channel: str = "", source: str = "tcp", port: int = 0) -> LogLine:
        """写入一行日志（采集线程与测试共用入口）。"""
        target = channel or self._config.channel
        line = LogLine(
            channel=target,
            timestamp=now_stamp(),
            epoch=time.time(),
            source=source,
            text=text,
            port=int(port or 0),
        )
        with self._buffers_lock:
            buffer = self._buffers.get(target)
            if buffer is None:
                buffer = _ChannelBuffer(self._config.buffer_max_lines, self._config.buffer_seconds)
                self._buffers[target] = buffer
        buffer.append(line)
        # 归档是加分项：写文件失败只记录错误，不影响内存缓冲与证据链（见 logfiles）
        sink = self._sinks.get(int(port or 0))
        if sink is not None:
            try:
                sink.write(line)
            except Exception as exc:  # 归档故障不允许拖垮采集
                logger.error("device log file sink failed on port %s: %s", port, exc)
        return line

    def snapshot(self, channel: str = "", seconds: float | None = None) -> list[dict[str, Any]]:
        """通道内最近的原始日志行（按时间升序）。"""
        target = channel or self._config.channel
        with self._buffers_lock:
            buffer = self._buffers.get(target)
        if buffer is None:
            return []
        since = time.time() - seconds if seconds else 0.0
        return [line.as_dict() for line in buffer.since(since)]

    def line_count(self, channel: str = "") -> int:
        target = channel or self._config.channel
        with self._buffers_lock:
            buffer = self._buffers.get(target)
        return len(buffer) if buffer else 0

    # ── 窗口 ──

    def open_window(self, device: str = "", label: str = "") -> str:
        """开一个日志证据窗口，返回窗口标识（必须早于动作发出）。"""
        channel = self.resolve_channel(device)
        window = self._windows.open(channel, label)
        logger.info(
            "device log window opened: id=%s channel=%s label=%s at=%s",
            window["window_id"],
            channel,
            label,
            window["opened_at"],
        )
        return str(window["window_id"])

    def read_window(
        self,
        device: str = "",
        window_id: str = "",
        action_times: list[str] | None = None,
        action_time: str = "",
        wait_seconds: float = 0.0,
    ) -> dict[str, Any]:
        """读窗口并按「本步每次动作发出时刻 + 阈值」出证据；未开窗时抛错，不用历史日志顶替。"""
        channel = self.resolve_channel(device)
        window = self._windows.get(window_id) if window_id else self._windows.latest(channel)
        if window is None:
            raise LogWindowMissing(
                f"设备 {device or channel} 没有已开启的日志证据窗口：请在把步骤交给执行模型之前开窗"
            )
        stamps = [stamp for stamp in (action_times or []) if stamp]
        if action_time:
            stamps.append(action_time)
        if not stamps:
            stamps = [str(window["opened_at"])]
        actions = sorted(_epoch(stamp) for stamp in stamps)
        if wait_seconds > 0:
            # 等到「最后一次动作 + 阈值」之后再读，保证慢一点的日志也能被收进来
            deadline = actions[-1] + self._config.window_seconds
            remaining = min(wait_seconds, max(0.0, deadline - time.time()))
            if remaining > 0:
                time.sleep(remaining)
        window_channel = str(window["channel"])
        with self._buffers_lock:
            buffer = self._buffers.get(window_channel)
        baseline_start = actions[0] - self._config.baseline_seconds
        lines = buffer.since(min(baseline_start, float(window["opened_epoch"]))) if buffer else []
        return build_evidence(
            channel=window_channel,
            window_id=str(window["window_id"]),
            window_opened_at=str(window["opened_at"]),
            lines=lines,
            keywords=self._keywords,
            action_times=stamps,
            threshold_seconds=self._config.window_seconds,
            baseline_seconds=self._config.baseline_seconds,
        )

    # ── 供采集线程用 ──

    @property
    def stop_event(self) -> threading.Event:
        return self._stop_event


class LogWindowMissing(RuntimeError):
    """步骤执行时没有已开启的证据窗口（不允许用历史日志顶替）。"""


class LogSourceUnknown(ValueError):
    """查询了一个未被平台采集的日志端口。"""


# ── 采集线程 ──────────────────────────────────────────────────


class _LineSplitter:
    """字节流 → 整行（CRLF 算一个换行，半截缓冲有上限）。"""

    def __init__(self, limit: int = LINE_LIMIT) -> None:
        self._buffer = bytearray()
        self._limit = limit

    def feed(self, data: bytes) -> list[str]:
        self._buffer.extend(data)
        lines: list[str] = []
        while True:
            found = self._first_terminator()
            if found is None:
                break
            index, terminator = found
            lines.append(bytes(self._buffer[:index]).decode("utf-8", errors="replace"))
            del self._buffer[: index + 1]
            if terminator == b"\r" and self._buffer[:1] == b"\n":
                del self._buffer[:1]
        if len(self._buffer) > self._limit:
            # 二进制流迟迟没有换行：丢弃半截缓冲，避免无限增长
            self._buffer.clear()
        return lines

    def _first_terminator(self) -> tuple[int, bytes] | None:
        candidates = [(self._buffer.find(token), token) for token in (b"\n", b"\r")]
        found = [item for item in candidates if item[0] >= 0]
        return min(found, key=lambda item: item[0]) if found else None


class _TcpCollector(threading.Thread):
    """单个端口的 TCP 监听采集：多连接、逐行切分、断线不断采集、可独立停止并释放端口。"""

    def __init__(
        self,
        bus: LogBus,
        host: str,
        port: int,
        channel: str = "",
        sink: LogFileSink | None = None,
    ) -> None:
        super().__init__(name=f"device-log-tcp-{port}", daemon=True)
        self._bus = bus
        self._host = host
        self._port = int(port)
        self._channel = channel or bus.resolve_channel()
        self._sink = sink
        self._stop = threading.Event()
        self._server: socket.socket | None = None

    def stop(self) -> None:
        """请求停止并**释放监听端口**：关掉 server socket 打断 accept，再等线程收尾。

        accept 有 0.5s 超时兜底，因此即使 close 没立刻打断阻塞，也能在秒级内停掉并释放端口。
        """
        self._stop.set()
        self._bus._mark_listening(self._port, False)
        server = self._server
        if server is not None:
            try:
                server.close()
            except OSError as exc:
                logger.warning("device log server close failed on port %s: %s", self._port, exc)
        self.join(timeout=2.0)

    def _stopping(self) -> bool:
        return self._stop.is_set() or self._bus.stop_event.is_set()

    def run(self) -> None:
        if _port_in_use(self._host, self._port):
            # Windows 允许两个进程绑同一端口 → 不探测就会「以为在采集、其实一条都收不到」
            logger.error(
                "device log port %d already in use; this collector will NOT receive data "
                "(check: netstat -ano | findstr :%d)",
                self._port,
                self._port,
            )
            return
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((self._host, self._port))
            server.listen(5)
            server.settimeout(0.5)
        except OSError as exc:
            logger.error("device log port %d bind failed: %s", self._port, exc)
            server.close()
            return
        self._server = server
        self._bus._mark_listening(self._port, True)
        logger.info(
            "device log collector listening on %s:%d (channel=%s)",
            self._host,
            self._port,
            self._channel,
        )
        try:
            while not self._stopping():
                try:
                    client, peer = server.accept()
                except TimeoutError:
                    continue
                except OSError as exc:
                    if self._stopping():
                        break
                    logger.warning("device log accept failed: %s", exc)
                    continue
                logger.info("device log client connected: %s:%s", peer[0], peer[1])
                threading.Thread(target=self._serve, args=(client,), daemon=True).start()
        finally:
            self._server = None
            self._bus._mark_listening(self._port, False)
            try:
                server.close()
            except OSError as exc:
                logger.warning("device log server close failed on port %s: %s", self._port, exc)
            logger.info("device log collector on port %d stopped", self._port)

    def _serve(self, client: socket.socket) -> None:
        splitter = _LineSplitter()
        client.settimeout(0.5)
        try:
            while not self._stopping():
                try:
                    data = client.recv(4096)
                except TimeoutError:
                    continue
                except OSError as exc:
                    logger.warning("device log recv failed: %s", exc)
                    break
                if not data:
                    break
                for line in splitter.feed(data):
                    if line.strip():
                        self._bus.feed(line, channel=self._channel, source="tcp", port=self._port)
        finally:
            client.close()


class _SerialCollector(threading.Thread):
    """串口采集：可配置串口 / 波特率，打开失败或掉线自动重试。"""

    def __init__(self, bus: LogBus, port: str, baud: int) -> None:
        super().__init__(name="device-log-serial", daemon=True)
        self._bus = bus
        self._port = port
        self._baud = baud

    def run(self) -> None:
        try:
            import serial  # 延迟导入：未装 pyserial 时只影响串口来源
        except ImportError:
            logger.error("pyserial not installed; serial device log source disabled")
            return
        while not self._bus.stop_event.is_set():
            try:
                handle = serial.Serial(port=self._port, baudrate=self._baud, timeout=0.2)
            except (OSError, serial.SerialException) as exc:
                logger.error("device log serial %s open failed: %s", self._port, exc)
                self._bus.stop_event.wait(SERIAL_RETRY_SECONDS)
                continue
            logger.info("device log serial opened: %s @ %d", self._port, self._baud)
            splitter = _LineSplitter()
            try:
                while not self._bus.stop_event.is_set():
                    data = handle.read(max(handle.in_waiting, 1))
                    if not data:
                        continue
                    for line in splitter.feed(data):
                        if line.strip():
                            self._bus.feed(line, source="serial")
            except (OSError, serial.SerialException) as exc:
                logger.warning("device log serial read failed: %s", exc)
            finally:
                try:
                    handle.close()
                except (OSError, serial.SerialException):
                    pass
            if not self._bus.stop_event.is_set():
                logger.warning("device log serial %s closed; retrying", self._port)
                self._bus.stop_event.wait(SERIAL_RETRY_SECONDS)


def _port_in_use(host: str, port: int) -> bool:
    """端口上是否已有程序在监听（用于启动前探测）。"""
    probe_host = "127.0.0.1" if host in ("", "0.0.0.0") else host
    try:
        with socket.create_connection((probe_host, port), timeout=0.5):
            return True
    except OSError:
        return False


# ── 进程内单例（由 Django 侧持有）────────────────────────────


_BUS: LogBus | None = None
_BUS_LOCK = threading.Lock()


def get_log_bus() -> LogBus | None:
    return _BUS


def get_or_create_log_bus(config: LogBusConfig) -> LogBus:
    """取（或建）总线单例，但**不启动任何采集**：启停由端口监听开关显式控制。"""
    global _BUS
    with _BUS_LOCK:
        if _BUS is None:
            _BUS = LogBus(config)
        return _BUS


def start_log_bus(config: LogBusConfig) -> LogBus:
    """幂等启动配置里登记的全部来源（一键全起）；单端口启停见 `LogBus.start_source`。"""
    bus = get_or_create_log_bus(config)
    bus.start()
    return bus


def stop_log_bus() -> None:
    global _BUS
    with _BUS_LOCK:
        if _BUS is not None:
            _BUS.stop()
            _BUS = None
