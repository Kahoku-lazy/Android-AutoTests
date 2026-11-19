"""
文件名: ➡ logbus.py 🏁
路径: ➡ engines/device/logbus.py 🏁
模块功能：➡ 设备日志端口来源登记与关键词表索引 🏁
Python 调试：➡ python -m engines.device.logbus 🏁
时间：➡ 2026-10-20 🏁
作者：➡ kahoku 🏁
版本：➡ 1.0.0 🏁
修改时间: ➡ 2026-11-19 🏁
类型: ➡ 工具模块 🏁
简介说明：➡
1. LogSourceSpec: 端口来源登记规格
2. KeywordIndex: 关键词表索引与匹配（小写比较、最长匹配消解）
3. 监听与写文件在 engines.uart_log
🏁
关联模块：➡
1. utils.logs: device_log
2. engines.uart_log: 端口监听与抓取写入
🏁
测试：➡
1. tests/serial_log/integration/test_keyword_api.py: 关键词映射注入 KeywordIndex
🏁
"""

from __future__ import annotations

import json

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from utils.logs import device_log

__all__ = [
    "DEFAULT_CHANNEL",
    "KeywordIndex",
    "LogSourceSpec",
]

DEFAULT_CHANNEL = "*"


@dataclass(frozen=True)
class LogSourceSpec:
    """一条日志来源登记：端口 + SKU + 波特率。

    波特率只在端口页展示，不参与监听。

    Attributes:
        port: 串口端口号。
        sku: 型号名；空串按通配 `*` 处理。
        baud: 波特率，只在端口页展示。
    """

    port: int
    sku: str = DEFAULT_CHANNEL
    baud: int = 0

    @property
    def channel(self) -> str:
        """该来源的型号名。"""
        return self.sku or DEFAULT_CHANNEL


class KeywordIndex:
    """「串口日志关键词 → 功能模块 / 功能点」索引，带最长匹配消解。"""

    def __init__(self, mapping: dict[str, list[dict[str, Any]]] | None = None) -> None:
        """
        建立关键词索引，并按长度降序准备匹配用的「小写关键词」列表。

        Args:
            mapping: 关键词到功能点列表的映射；省略时建空索引。
        """
        self._map: dict[str, list[dict[str, Any]]] = dict(mapping or {})
        # 匹配用小写关键词、返回用原始关键词：日志行按小写比较，真相源里的写法可能带大写。
        self._needles: list[tuple[str, str]] = sorted(
            ((keyword.lower(), keyword) for keyword in self._map),
            key=lambda item: len(item[0]),
            reverse=True,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> KeywordIndex:
        """从数据文件加载；文件缺失或损坏时返回空索引并记录可读错误。

        Args:
            path: 关键词 JSON 文件路径；空串表示未配置，直接返回空索引。

        Returns:
            加载成功的索引；文件缺失、编码错或 JSON 不可解析时是空索引。
        """
        target = Path(path)
        if not str(path).strip():
            device_log.info("device log keyword file not configured; keyword matching disabled")
            return cls()
        if not target.exists():
            device_log.error("device log keyword file missing: %s", target)
            return cls()
        try:
            raw = json.loads(target.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            # UnicodeDecodeError 与 JSONDecodeError 都是 ValueError，一并降级。
            device_log.error("device log keyword file unreadable: %s (%s)", target, exc)
            return cls()
        mapping = raw.get("keywords") if isinstance(raw, dict) else raw
        if not isinstance(mapping, dict):
            device_log.error("device log keyword file has unexpected shape: %s", target)
            return cls()
        index = cls(mapping)
        device_log.info("device log keywords loaded: %d keywords from %s", len(index), target)
        return index

    def __bool__(self) -> bool:
        return bool(self._map)

    def __len__(self) -> int:
        return len(self._map)

    @property
    def mapping(self) -> dict[str, list[dict[str, Any]]]:
        """返回当前关键词表映射（内部 dict 的引用，调用方只读，不要改写）。"""
        return self._map

    def match(self, text: str) -> list[tuple[str, list[dict[str, Any]]]]:
        """返回该行命中的 (关键词, 功能点列表)，按出现先后排序，剔除被长关键词包住的命中。

        Args:
            text: 一行日志原文。

        Returns:
            命中列表；关键词用真相源里的原始写法，功能点是其挂载的功能点字典列表。
        """
        if not self._map or not text:
            return []
        lowered = text.lower()
        spans: list[tuple[int, int, str]] = []
        for needle, keyword in self._needles:
            start = lowered.find(needle)
            while start >= 0:
                spans.append((start, start + len(needle), keyword))
                start = lowered.find(needle, start + 1)
        if not spans:
            return []
        spans.sort(key=lambda item: (item[0], -(item[1] - item[0])))
        kept: list[tuple[int, int, str]] = []
        for span in spans:
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
