"""一个端口一条线程：绑定、多连接、按行切开。"""

from __future__ import annotations

import socket
import threading

from utils.logs import serial_log

from .detect import PortDetector
from .params import PortParams
from .writer import CaptureWriter


class _LineSplitter:
    """字节流切成整行。超过单行上限时先交出已截断的一段，再继续收后面的字节。"""

    def __init__(self, limit: int) -> None:
        self._buffer = bytearray()
        self._limit = max(1, int(limit))

    def feed(self, data: bytes) -> list[str]:
        self._buffer.extend(data)
        lines: list[str] = []
        while True:
            found = self._first_terminator()
            if found is None:
                break
            index, terminator = found
            if index > self._limit:
                lines.append(self._decode(self._buffer[: self._limit]))
                del self._buffer[: self._limit]
                continue
            lines.append(self._decode(self._buffer[:index]))
            del self._buffer[: index + 1]
            if terminator == b"\r" and self._buffer[:1] == b"\n":
                del self._buffer[:1]
        while len(self._buffer) > self._limit:
            lines.append(self._decode(self._buffer[: self._limit]))
            del self._buffer[: self._limit]
        return lines

    def _decode(self, raw: bytearray | bytes) -> str:
        return bytes(raw).decode("utf-8", errors="replace")

    def _first_terminator(self) -> tuple[int, bytes] | None:
        candidates = [(self._buffer.find(token), token) for token in (b"\n", b"\r")]
        found = [item for item in candidates if item[0] >= 0]
        return min(found, key=lambda item: item[0]) if found else None


class PortReceiver(threading.Thread):
    """监听一个 TCP 端口并按行把非空内容交给写入器。"""

    def __init__(self, params: PortParams, writer: CaptureWriter | None = None) -> None:
        super().__init__(name=f"uart-log-{int(params.port)}", daemon=True)
        self.params = params
        self._writer = writer or CaptureWriter(params.sku, params.port, params.log_directory)
        self._stop = threading.Event()
        self._listening = False
        self._listen_lock = threading.Lock()
        self._server: socket.socket | None = None

    @property
    def listening(self) -> bool:
        with self._listen_lock:
            return self._listening

    def stop(self) -> None:
        """停止监听并关掉套接字，让端口可以马上被别人绑定。"""
        self._stop.set()
        self._mark(False)
        server = self._server
        if server is not None:
            try:
                server.close()
            except OSError as exc:
                serial_log.warning(
                    "uart server close failed on port %s: %s",
                    int(self.params.port),
                    exc,
                )
        self.join(timeout=2.0)

    def run(self) -> None:
        if not PortDetector().available(self.params):
            return
        server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            server.bind((self.params.host, int(self.params.port)))
            server.listen(5)
            server.settimeout(0.5)
        except OSError as exc:
            serial_log.error("uart port %s bind failed: %s", int(self.params.port), exc)
            server.close()
            return
        self._server = server
        self._mark(True)
        serial_log.info(
            "uart collector listening on %s:%s sku=%s",
            self.params.host,
            int(self.params.port),
            self.params.sku,
        )
        try:
            while not self._stop.is_set():
                try:
                    client, _peer = server.accept()
                except TimeoutError:
                    continue
                except OSError as exc:
                    if self._stop.is_set():
                        break
                    serial_log.warning("uart accept failed: %s", exc)
                    self._stop.wait(self.params.retry_seconds)
                    continue
                threading.Thread(target=self._serve, args=(client,), daemon=True).start()
        finally:
            self._server = None
            self._mark(False)
            try:
                server.close()
            except OSError as exc:
                serial_log.warning(
                    "uart server close failed on port %s: %s",
                    int(self.params.port),
                    exc,
                )

    def _serve(self, client: socket.socket) -> None:
        splitter = _LineSplitter(self.params.line_limit)
        client.settimeout(0.5)
        try:
            while not self._stop.is_set():
                try:
                    data = client.recv(4096)
                except TimeoutError:
                    continue
                except OSError as exc:
                    serial_log.warning("uart recv failed: %s", exc)
                    break
                if not data:
                    break
                for line in splitter.feed(data):
                    if not line.strip():
                        continue
                    try:
                        self._writer.write(line)
                    except Exception as exc:
                        serial_log.error("uart capture write failed: %s", exc)
        finally:
            client.close()

    def _mark(self, listening: bool) -> None:
        with self._listen_lock:
            self._listening = listening
