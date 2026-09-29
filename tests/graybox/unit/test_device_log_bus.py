"""灰盒·单元测试 — 设备日志采集与缓冲（device-log-capture 能力）。

零外部依赖、不连设备、不占用固定端口（用临时空闲端口）。
覆盖：时间戳格式、TCP 采集、串口失败降级、通道隔离与缓冲淘汰、端口占用探测、来源标记、
开关关闭，以及**按端口独立启停与日志落文件**（变更 add-device-log-port-console）。
"""

from __future__ import annotations

import re
import socket
import time

from datetime import timedelta
from pathlib import Path

import pytest

from engines.device.logbus import (
    DEFAULT_CHANNEL,
    LogBus,
    LogBusConfig,
    LogSourceSpec,
    now_stamp,
    parse_stamp,
)

STAMP_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}\.\d{3}$")


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _wait_collector(bus: LogBus, timeout: float = 5.0) -> int:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if bus.bound_port:
            return bus.bound_port
        time.sleep(0.05)
    raise AssertionError("采集线程没能在超时内绑定端口")


def _send(port: int, payload: bytes) -> None:
    with socket.create_connection(("127.0.0.1", port), timeout=3) as client:
        client.sendall(payload)


def _wait_lines(bus: LogBus, channel: str, count: int, timeout: float = 5.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if bus.line_count(channel) >= count:
            return
        time.sleep(0.05)
    raise AssertionError(
        f"通道 {channel} 在超时内只收到 {bus.line_count(channel)} 行，期望 {count} 行"
    )


# ── 2.3 时间戳 ───────────────────────────────────────────────


def test_now_stamp_is_beijing_millisecond() -> None:
    """时间戳为北京时间、毫秒精度，且可回读（不依赖 tzdata）。"""
    stamp = now_stamp()
    assert STAMP_PATTERN.match(stamp), stamp
    parsed = parse_stamp(stamp)
    assert parsed is not None
    assert parsed.utcoffset() == timedelta(hours=8)
    assert parsed.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3] == stamp


def test_parse_stamp_rejects_garbage() -> None:
    assert parse_stamp("") is None
    assert parse_stamp("2026-09-28") is None


# ── 2.1 TCP 采集 ─────────────────────────────────────────────


def test_tcp_collector_receives_lines() -> None:
    """本地 socket 灌入多行 → 逐行收下（含 CRLF 与裸 LF）。"""
    bus = LogBus(LogBusConfig(tcp_host="127.0.0.1", tcp_port=_free_port()))
    try:
        bus.start()
        port = _wait_collector(bus)
        _send(port, b"line-one\r\nline-two\nline-three\r\n")
        _wait_lines(bus, DEFAULT_CHANNEL, 3)
        texts = [item["text"] for item in bus.snapshot()]
        assert texts == ["line-one", "line-two", "line-three"]
    finally:
        bus.stop()


def test_tcp_collector_survives_reconnect() -> None:
    """客户端断开后重连，采集不中断。"""
    bus = LogBus(LogBusConfig(tcp_host="127.0.0.1", tcp_port=_free_port()))
    try:
        bus.start()
        port = _wait_collector(bus)
        _send(port, b"first\r\n")
        _wait_lines(bus, DEFAULT_CHANNEL, 1)
        _send(port, b"second\r\n")
        _wait_lines(bus, DEFAULT_CHANNEL, 2)
        assert [item["text"] for item in bus.snapshot()] == ["first", "second"]
    finally:
        bus.stop()


# ── 2.2 串口失败降级 ─────────────────────────────────────────


def test_serial_failure_keeps_tcp_source_working(caplog: pytest.LogCaptureFixture) -> None:
    """串口打不开只记录错误，网络来源照常工作（不中断采集）。"""
    bus = LogBus(
        LogBusConfig(
            tcp_host="127.0.0.1",
            tcp_port=_free_port(),
            serial_port="COM_NOT_EXIST_FOR_TEST",
        )
    )
    try:
        with caplog.at_level("ERROR"):
            bus.start()
            port = _wait_collector(bus)
            _send(port, b"tcp-still-works\r\n")
            _wait_lines(bus, DEFAULT_CHANNEL, 1)
        assert bus.snapshot()[0]["text"] == "tcp-still-works"
    finally:
        bus.stop()


# ── 2.4 通道隔离与缓冲淘汰 ───────────────────────────────────


def test_channels_are_isolated() -> None:
    """两台设备的日志互不串台。"""
    bus = LogBus(LogBusConfig(enabled=True, tcp_port=0))
    bus.feed("device-a-line", channel="dev-a")
    bus.feed("device-b-line", channel="dev-b")
    assert [item["text"] for item in bus.snapshot(channel="dev-a")] == ["device-a-line"]
    assert [item["text"] for item in bus.snapshot(channel="dev-b")] == ["device-b-line"]


def test_buffer_is_bounded_by_max_lines() -> None:
    """超过单通道行数上限时 FIFO 淘汰，占用有界。"""
    bus = LogBus(LogBusConfig(enabled=True, tcp_port=0, buffer_max_lines=10))
    for index in range(50):
        bus.feed(f"line-{index}")
    assert bus.line_count() == 10
    texts = [item["text"] for item in bus.snapshot()]
    assert texts[0] == "line-40" and texts[-1] == "line-49"


# ── 2.5 端口占用探测 ─────────────────────────────────────────


def test_occupied_port_is_reported_not_silently_hijacked() -> None:
    """端口已被占用时不静默重复绑定：不绑定端口、也收不到数据。"""
    blocker = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    blocker.bind(("127.0.0.1", 0))
    blocker.listen(1)
    port = int(blocker.getsockname()[1])
    bus = LogBus(LogBusConfig(tcp_host="127.0.0.1", tcp_port=port))
    try:
        bus.start()
        time.sleep(0.5)
        assert bus.bound_port is None
        assert bus.line_count() == 0
    finally:
        bus.stop()
        blocker.close()


# ── 2.6 来源标记 ─────────────────────────────────────────────


def test_source_is_recorded() -> None:
    """同一通道混合来源的日志可按来源区分。"""
    bus = LogBus(LogBusConfig(enabled=True, tcp_port=0))
    bus.feed("from-network", source="tcp")
    bus.feed("from-serial", source="serial")
    sources = {item["text"]: item["source"] for item in bus.snapshot()}
    assert sources == {"from-network": "tcp", "from-serial": "serial"}


# ── 1.3 开关关闭降级 ─────────────────────────────────────────


def test_disabled_bus_does_not_start_collectors() -> None:
    """开关关闭 → 不启动采集且不报错。"""
    bus = LogBus(
        LogBusConfig(enabled=False, tcp_port=_free_port(), serial_port="COM_NOT_EXIST_FOR_TEST")
    )
    assert bus.start() is False
    assert bus.running is False
    assert bus.bound_port is None
    bus.stop()


# ── 按端口独立启停（变更 add-device-log-port-console）─────────


def _source_bus(port: int, **kwargs) -> LogBus:
    return LogBus(
        LogBusConfig(
            tcp_host="127.0.0.1",
            sources=[LogSourceSpec(port=port, sku="H6810", baud=921600)],
            **kwargs,
        )
    )


def test_source_can_be_started_and_stopped_individually() -> None:
    """单端口启停：开→收日志，关→不再监听，来源登记可用于端口查询。"""
    port = _free_port()
    bus = _source_bus(port)
    try:
        assert bus.configured_ports() == [port]
        assert bus.channel_for_port(port) == "H6810"
        assert bus.start_source(port) is True
        _wait_collector(bus)
        assert bus.running_ports() == [port] and bus.is_listening(port)
        _send(port, b"hello-from-source\r\n")
        _wait_lines(bus, "H6810", 1)

        assert bus.stop_source(port) is True
        assert bus.running_ports() == [] and bus.is_listening(port) is False
    finally:
        bus.stop()


def test_stop_source_releases_the_port() -> None:
    """关闭开关必须真正释放端口：关闭后其它程序能立即绑定同一端口。"""
    port = _free_port()
    bus = _source_bus(port)
    try:
        bus.start_source(port)
        _wait_collector(bus)
        assert bus.stop_source(port) is True

        deadline = time.time() + 5.0
        while time.time() < deadline:
            probe = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                probe.bind(("127.0.0.1", port))
                return
            except OSError:
                time.sleep(0.1)
            finally:
                probe.close()
        raise AssertionError("端口没有在超时内被释放")
    finally:
        bus.stop()


def test_starting_same_source_twice_keeps_one_listener() -> None:
    """重复打开同一端口是幂等的：不产生第二个监听、日志不重复。"""
    port = _free_port()
    bus = _source_bus(port)
    try:
        bus.start_source(port)
        _wait_collector(bus)
        assert bus.start_source(port) is True
        _send(port, b"only-once\r\n")
        _wait_lines(bus, "H6810", 1)
        time.sleep(0.3)
        assert bus.line_count("H6810") == 1
    finally:
        bus.stop()


def test_unconfigured_source_is_not_started() -> None:
    """未登记的端口不启动（返回 False），也不报错。"""
    bus = _source_bus(_free_port())
    try:
        assert bus.start_source(7004) is False
        assert bus.running_ports() == []
    finally:
        bus.stop()


def test_multi_port_sources_are_isolated_and_both_listen() -> None:
    """登记多个端口时各写各的通道与文件，互不串台。"""
    port_a, port_b = _free_port(), _free_port()
    bus = LogBus(
        LogBusConfig(
            tcp_host="127.0.0.1",
            sources=[
                LogSourceSpec(port=port_a, sku="H6810"),
                LogSourceSpec(port=port_b, sku="H6199"),
            ],
        )
    )
    try:
        assert bus.start_source(port_a) and bus.start_source(port_b)
        deadline = time.time() + 5.0
        while time.time() < deadline and len(bus.running_ports()) < 2:
            time.sleep(0.05)
        assert bus.running_ports() == sorted([port_a, port_b])
        _send(port_a, b"from-a\r\n")
        _send(port_b, b"from-b\r\n")
        _wait_lines(bus, "H6810", 1)
        _wait_lines(bus, "H6199", 1)
        assert [item["text"] for item in bus.snapshot(channel="H6810")] == ["from-a"]
        assert [item["text"] for item in bus.snapshot(channel="H6199")] == ["from-b"]
    finally:
        bus.stop()


# ── 日志落文件（归档是加分项，坏了不能拖垮采集）──────────────


def test_feed_writes_current_log_file(tmp_path: Path) -> None:
    """采集到的行同时落盘：`{SKU}_{端口}.log` 出现该行。"""
    port = _free_port()
    bus = _source_bus(port, log_dir=str(tmp_path))
    try:
        bus.start_source(port)
        _wait_collector(bus)
        _send(port, b"file-line\r\n")
        _wait_lines(bus, "H6810", 1)

        target = tmp_path / f"H6810_{port}.log"
        deadline = time.time() + 5.0
        while time.time() < deadline and not target.is_file():
            time.sleep(0.05)
        assert "file-line" in target.read_text(encoding="utf-8")
    finally:
        bus.stop()


def test_sink_failure_does_not_break_collection() -> None:
    """文件写入抛错时缓冲照常收行（归档故障不影响证据链）。"""

    class _BrokenSink:
        def write(self, line) -> None:
            raise OSError("disk full")

        def close(self) -> None:
            return None

    bus = LogBus(LogBusConfig(enabled=True, tcp_port=0))
    bus._sinks[7005] = _BrokenSink()  # type: ignore[assignment]
    line = bus.feed("still-buffered", port=7005)
    assert line.text == "still-buffered"
    assert [item["text"] for item in bus.snapshot()] == ["still-buffered"]


def test_no_log_dir_means_memory_only() -> None:
    """未配置日志目录时不落文件（只进内存缓冲）。"""
    bus = LogBus(LogBusConfig(enabled=True, tcp_port=0))
    bus.feed("memory-only", port=7005)
    assert bus._sinks == {}
    assert [item["text"] for item in bus.snapshot()] == ["memory-only"]


# ── 按范围读取：缓冲 ∪ 已落盘文件（变更 log-read-from-files）──────


def _range_bus(tmp_path: Path) -> LogBus:
    return LogBus(
        LogBusConfig(
            enabled=True,
            tcp_port=0,
            channel="H6810",
            source_channels={7005: "H6810"},
            log_dir=str(tmp_path),
        )
    )


def _epoch(stamp: str) -> float:
    moment = parse_stamp(stamp)
    assert moment is not None
    return moment.timestamp()


def test_read_range_falls_back_to_log_file(tmp_path: Path) -> None:
    """缓冲里没有的时段（超出保留时长 / 重启后）：从日志文件里按范围取到。"""
    bus = _range_bus(tmp_path)
    (tmp_path / "H6810_7005.log").write_text(
        "2026-09-29 11:47:04.687 [tcp] [light_switch][I]: switch_on\n",
        encoding="utf-8",
    )

    found = bus.read_range(
        start_epoch=_epoch("2026-09-29 11:47:04.000"),
        end_epoch=_epoch("2026-09-29 11:47:05.000"),
        port=7005,
    )

    assert [line.text for line in found["lines"]] == ["[light_switch][I]: switch_on"]
    assert (found["buffer_lines"], found["file_lines"]) == (0, 1)


def test_read_range_dedupes_buffer_and_file(tmp_path: Path) -> None:
    """同一行既在缓冲又在文件里时只出现一次，且仍按时间升序。"""
    bus = _range_bus(tmp_path)
    first = bus.feed("first", port=7005)
    second = bus.feed("second", port=7005)
    bus._sinks[7005].close() if bus._sinks else None
    duplicates = "\n".join(
        f"{line.timestamp} [{line.source}] {line.text}" for line in (first, second)
    )
    (tmp_path / "H6810_7005.log").write_text(duplicates + "\n", encoding="utf-8")

    found = bus.read_range(
        start_epoch=first.epoch - 1,
        end_epoch=second.epoch + 1,
        port=7005,
    )

    assert [line.text for line in found["lines"]] == ["first", "second"]
    assert (found["buffer_lines"], found["file_lines"]) == (2, 2)


def test_read_range_without_file_is_buffer_only(tmp_path: Path) -> None:
    """没有对应日志文件时照常返回缓冲行，不抛错。"""
    bus = _range_bus(tmp_path)
    line = bus.feed("only-in-buffer", port=7005)

    found = bus.read_range(start_epoch=line.epoch - 1, end_epoch=line.epoch + 1, port=7005)

    assert [item.text for item in found["lines"]] == ["only-in-buffer"]
    assert found["file_lines"] == 0
