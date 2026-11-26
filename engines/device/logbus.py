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
    port: int
    sku: str = DEFAULT_CHANNEL
    baud: int = 0

    @property
    def channel(self) -> str:
        return self.sku or DEFAULT_CHANNEL


class KeywordIndex:
    def __init__(self, mapping: dict[str, list[dict[str, Any]]] | None = None) -> None:
        self._map: dict[str, list[dict[str, Any]]] = dict(mapping or {})
        self._needles: list[tuple[str, str]] = sorted(
            ((keyword.lower(), keyword) for keyword in self._map),
            key=lambda item: len(item[0]),
            reverse=True,
        )

    @classmethod
    def from_file(cls, path: str | Path) -> KeywordIndex:
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
        return self._map

    def match(self, text: str) -> list[tuple[str, list[dict[str, Any]]]]:
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
