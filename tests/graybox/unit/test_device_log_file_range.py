"""灰盒·单元测试 — 日志文件的按时间范围回读（变更 log-read-from-files）。

零依赖：只看 `range_lines` 的四条口径 ——
1. 只返回落在范围内的行，且保持原始顺序（旧 → 新）；
2. 范围完全早于文件时如实返回空（不抛错）；
3. 超过行数上限时保留最新一侧；
4. 无法解析的行（人工追加内容 / 半个时间戳）被跳过。
"""

from __future__ import annotations

from pathlib import Path

import pytest

from engines.device.logfiles import line_epoch, range_lines

pytestmark = [pytest.mark.unit]

LINES = [
    "2026-09-29 11:46:00.000 [tcp] ram free heap size: 11400",
    "2026-09-29 11:47:04.687 [tcp] [light_switch][I]: switch_on",
    "2026-09-29 11:47:04.742 [tcp] [base mode][I]: music_mode_start",
    "2026-09-29 11:47:20.000 [tcp] ram free heap size: 11368",
    "人工追加的一行（没有时间戳）",
]


@pytest.fixture()
def log_file(tmp_path: Path) -> Path:
    path = tmp_path / "H6810_7005.log"
    path.write_text("\n".join(LINES) + "\n", encoding="utf-8")
    return path


def test_line_epoch_parses_beijing_milliseconds() -> None:
    epoch = line_epoch("2026-09-29 11:47:04.687")
    assert epoch is not None
    assert line_epoch("不是时间戳") is None


def test_range_returns_only_lines_inside_and_keeps_order(log_file: Path) -> None:
    start = line_epoch("2026-09-29 11:47:04.000")
    end = line_epoch("2026-09-29 11:47:04.999")
    rows = range_lines(log_file, start, end)
    assert [row.text for row in rows] == [
        "[light_switch][I]: switch_on",
        "[base mode][I]: music_mode_start",
    ]
    assert [row.timestamp for row in rows] == [
        "2026-09-29 11:47:04.687",
        "2026-09-29 11:47:04.742",
    ]


def test_range_before_file_returns_empty(log_file: Path) -> None:
    start = line_epoch("2026-09-29 09:00:00.000")
    end = line_epoch("2026-09-29 09:00:30.000")
    assert range_lines(log_file, start, end) == []


def test_missing_file_returns_empty(tmp_path: Path) -> None:
    assert range_lines(tmp_path / "nope.log", 0.0, 9e12) == []


def test_limit_keeps_newest_side(log_file: Path) -> None:
    start = line_epoch("2026-09-29 11:46:00.000")
    end = line_epoch("2026-09-29 11:48:00.000")
    rows = range_lines(log_file, start, end, limit=2)
    assert [row.timestamp for row in rows] == [
        "2026-09-29 11:47:04.742",
        "2026-09-29 11:47:20.000",
    ]


def test_unparsable_lines_are_skipped(log_file: Path) -> None:
    rows = range_lines(log_file, 0.0, 9e12)
    assert all(row.source == "tcp" for row in rows)
    assert len(rows) == 4  # 人工追加的那一行被跳过
