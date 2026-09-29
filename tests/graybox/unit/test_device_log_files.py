"""灰盒·单元测试 — 无线串口日志文件归档（变更 add-device-log-port-console）。

零外部依赖、零数据库：
覆盖逐行追加与可读性、目录自动创建、50MB 上限轮转与「绝不覆盖」、尾部倒读行数语义、
文件行解析回读（供页面按同一口径合并倒序）。
"""

from __future__ import annotations

from pathlib import Path

from engines.device.logfiles import (
    FileLine,
    LogFileSink,
    archive_file_name,
    current_file_name,
    log_file_path,
    parse_log_line,
    tail_lines,
)

SKU = "H6810"
PORT = 7005
STAMP = "2026-09-28 15:47:41.466"
DAY = "20260928"


def _line(text: str, stamp: str = STAMP, source: str = "tcp") -> FileLine:
    return FileLine(timestamp=stamp, source=source, text=text)


def _sink(tmp_path: Path, max_bytes: int = 1024 * 1024) -> LogFileSink:
    return LogFileSink(sku=SKU, port=PORT, directory=tmp_path, max_bytes=max_bytes)


# ── 2.1 逐行追加 ─────────────────────────────────────────────


def test_naming_follows_sku_and_port() -> None:
    assert current_file_name(SKU, PORT) == "H6810_7005.log"
    assert archive_file_name(SKU, PORT, DAY) == "H6810_7005_20260928.log"
    assert archive_file_name(SKU, PORT, DAY, 2) == "H6810_7005_20260928_2.log"


def test_lines_are_appended_and_history_kept(tmp_path: Path) -> None:
    """逐行追加：后写的行在末尾，此前写入的行完整保留。"""
    sink = _sink(tmp_path)
    sink.write(_line("first"))
    sink.write(_line("second"))
    sink.close()

    content = (tmp_path / "H6810_7005.log").read_text(encoding="utf-8")
    assert content.splitlines() == [
        f"{STAMP} [tcp] first",
        f"{STAMP} [tcp] second",
    ]


def test_line_carries_timestamp_source_and_raw_text(tmp_path: Path) -> None:
    """文件行 = 北京时间毫秒 + 来源 + 设备原文（记事本能直接读懂）。"""
    sink = _sink(tmp_path)
    sink.write(_line("[light_switch][I]: switch_off", source="tcp"))
    sink.close()
    raw = (tmp_path / "H6810_7005.log").read_text(encoding="utf-8").rstrip("\n")
    assert raw == f"{STAMP} [tcp] [light_switch][I]: switch_off"


def test_write_is_visible_immediately_without_close(tmp_path: Path) -> None:
    """写入即刷盘：不 close 也能读到刚写的行（页面上要立刻看见）。"""
    sink = _sink(tmp_path)
    sink.write(_line("visible-now"))
    try:
        assert "visible-now" in (tmp_path / "H6810_7005.log").read_text(encoding="utf-8")
    finally:
        sink.close()


def test_directory_is_created_on_first_write(tmp_path: Path) -> None:
    """目录不存在时自动创建（含多级父目录）。"""
    target = tmp_path / "logs" / "wireless"
    sink = _sink(target)
    sink.write(_line("in-new-dir"))
    sink.close()
    assert (target / "H6810_7005.log").is_file()


def test_size_bytes_reports_current_file_size(tmp_path: Path) -> None:
    sink = _sink(tmp_path)
    sink.write(_line("abc"))
    try:
        assert sink.size_bytes == (tmp_path / "H6810_7005.log").stat().st_size
        assert sink.size_bytes > 0
    finally:
        sink.close()


# ── 2.2 轮转 ─────────────────────────────────────────────────


def test_rotates_at_limit_and_keeps_writing_current_name(tmp_path: Path) -> None:
    """到达上限 → 旧文件改名存档，当前文件继续沿用原名写入。"""
    sink = _sink(tmp_path, max_bytes=1024)
    payload = "x" * 80
    for _ in range(30):
        sink.write(_line(payload))
    sink.close()

    current = tmp_path / "H6810_7005.log"
    archive = tmp_path / f"H6810_7005_{DAY}.log"
    assert current.is_file()
    assert archive.is_file()
    assert current.stat().st_size <= 1024
    assert archive.stat().st_size > 0


def test_rotation_never_drops_lines(tmp_path: Path) -> None:
    """轮转不丢行：存档 + 当前文件的行数之和 = 写入总行数。"""
    sink = _sink(tmp_path, max_bytes=1024)
    total = 40
    for index in range(total):
        sink.write(_line(f"line-{index:03d}-{'y' * 60}"))
    sink.close()

    files = sorted(tmp_path.glob("H6810_7005*.log"))
    assert len(files) >= 2
    written = sum(len(path.read_text(encoding="utf-8").splitlines()) for path in files)
    assert written == total


def test_same_day_second_rotation_appends_index(tmp_path: Path) -> None:
    """同一天多次轮转：存档名追加序号，既有存档内容不变。"""
    sink = _sink(tmp_path, max_bytes=1024)
    payload = "z" * 80
    for _ in range(60):
        sink.write(_line(payload))
    sink.close()

    first = tmp_path / f"H6810_7005_{DAY}.log"
    second = tmp_path / f"H6810_7005_{DAY}_2.log"
    assert first.is_file() and second.is_file()
    assert first.stat().st_size > 0 and second.stat().st_size > 0


def test_existing_archive_is_never_overwritten(tmp_path: Path) -> None:
    """同名存档已存在时 MUST NOT 覆盖：新存档改用下一个序号。"""
    occupied = tmp_path / f"H6810_7005_{DAY}.log"
    occupied.write_text("手工留下的内容\n", encoding="utf-8")
    sink = _sink(tmp_path, max_bytes=1024)
    payload = "q" * 90
    for _ in range(20):
        sink.write(_line(payload))
    sink.close()

    assert occupied.read_text(encoding="utf-8") == "手工留下的内容\n"
    assert (tmp_path / f"H6810_7005_{DAY}_2.log").is_file()


def test_reopen_after_restart_appends_to_current_file(tmp_path: Path) -> None:
    """平台重启后从当前文件末尾续写（不覆盖、不清空）。"""
    _sink(tmp_path).write(_line("before-restart"))
    sink = _sink(tmp_path)  # 新实例 = 重启后的采集器
    sink.write(_line("after-restart"))
    sink.close()
    texts = (tmp_path / "H6810_7005.log").read_text(encoding="utf-8").splitlines()
    assert len(texts) == 2
    assert texts[0].endswith("before-restart") and texts[1].endswith("after-restart")


def test_rotated_day_comes_from_line_timestamp(tmp_path: Path) -> None:
    """轮转日期取该行时间戳（北京时间）的日期，而不是本机当天。"""
    sink = _sink(tmp_path, max_bytes=1024)
    payload = "m" * 80
    for _ in range(20):
        sink.write(_line(payload, stamp="2026-01-02 08:00:00.000"))
    sink.close()
    assert (tmp_path / "H6810_7005_20260102.log").is_file()


# ── 2.3 尾部读取 ─────────────────────────────────────────────


def test_tail_returns_only_last_lines_in_file_order(tmp_path: Path) -> None:
    """超过 limit 只取尾部，且保持文件原始顺序（旧→新）。"""
    path = tmp_path / "H6810_7005.log"
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("\n".join(f"line-{index}" for index in range(100)) + "\n")
    tail = tail_lines(path, 10)
    assert len(tail) == 10
    assert tail[0] == "line-90" and tail[-1] == "line-99"


def test_tail_returns_all_when_file_shorter(tmp_path: Path) -> None:
    path = tmp_path / "H6810_7005.log"
    with path.open("w", encoding="utf-8", newline="") as handle:
        handle.write("a\nb\n")
    assert tail_lines(path, 50) == ["a", "b"]


def test_tail_on_missing_or_empty_file(tmp_path: Path) -> None:
    assert tail_lines(tmp_path / "nope.log", 10) == []
    empty = tmp_path / "empty.log"
    empty.write_text("", encoding="utf-8")
    assert tail_lines(empty, 10) == []


def test_tail_reads_large_file_without_loading_it_all(tmp_path: Path) -> None:
    """大文件只读尾部：limit=5 时 5 万行文件的首行不出现在结果里。"""
    path = tmp_path / "big.log"
    with path.open("w", encoding="utf-8") as handle:
        for index in range(50000):
            handle.write(f"row-{index:06d}-{'p' * 30}\n")
    tail = tail_lines(path, 5)
    assert len(tail) == 5
    assert tail[-1].startswith("row-049999")
    assert not any("row-000000" in item for item in tail)


def test_tail_accepts_crlf_lines(tmp_path: Path) -> None:
    """外部工具写入的 CRLF 文件也能读（不把 \\r 带进正文）。"""
    path = tmp_path / "crlf.log"
    path.write_bytes(f"{STAMP} [tcp] one\r\n{STAMP} [tcp] two\r\n".encode())
    parsed = [parse_log_line(raw) for raw in tail_lines(path, 10)]
    assert [item.text for item in parsed if item] == ["one", "two"]  # type: ignore[union-attr]


# ── 回读解析（页面按同一口径合并用）──────────────────────────


def test_parse_round_trip() -> None:
    parsed = parse_log_line(f"{STAMP} [tcp] [light_switch][I]: switch_off")
    assert parsed is not None
    assert (parsed.timestamp, parsed.source, parsed.text) == (
        STAMP,
        "tcp",
        "[light_switch][I]: switch_off",
    )


def test_parse_rejects_unexpected_lines() -> None:
    assert parse_log_line("人工追加的一行") is None
    assert parse_log_line("") is None


def test_log_file_path_uses_directory_and_name(tmp_path: Path) -> None:
    assert log_file_path(tmp_path, SKU, PORT) == tmp_path / "H6810_7005.log"
