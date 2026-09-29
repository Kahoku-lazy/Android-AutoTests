"""灰盒·单元测试 — 无线端口管理接口（变更 add-device-log-port-console）。

Django 测试客户端（不经运行中的服务）：零设备、不占固定端口。
覆盖三个端点的信封与字段、权限（列表/日志登录可读、开关仅超管）、四种结论、
读取行数夹紧、只从当前文件读取（不读存档）。
"""

from __future__ import annotations

import json
import socket

from pathlib import Path

import pytest

from django.contrib.auth import get_user_model

from apps.ai_assistant import api
from engines.device.logbus import stop_log_bus
from engines.device.logfiles import FileLine, LogFileSink
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.django_db(transaction=True)]

User = get_user_model()

LIST_URL = "/api/ai/log-ports/"
TOGGLE_URL = "/api/ai/log-ports/toggle/"
SKU = "H6810"
STAMP = "2026-09-28 15:47:41.466"


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(("127.0.0.1", 0))
        return int(probe.getsockname()[1])


def _headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


@pytest.fixture
def admin():
    return User.objects.create_superuser(username="log_admin", password="x")


@pytest.fixture
def member():
    return User.objects.create_user(username="log_member", password="x")


@pytest.fixture(autouse=True)
def _env(tmp_path: Path, settings):
    stop_log_bus()
    settings.DEVICE_LOG_ENABLED = True
    settings.DEVICE_LOG_TCP_PORT = 0
    settings.DEVICE_LOG_SOURCES = ""
    settings.DEVICE_LOG_SERIAL_PORT = ""
    settings.DEVICE_LOG_SOURCE_SKU = SKU
    settings.DEVICE_LOG_SOURCE_BAUD = 921600
    settings.DEVICE_LOG_LOG_DIR = str(tmp_path)
    settings.DEVICE_LOG_TAIL_LINES = 2000
    settings.DEVICE_LOG_TAIL_LINES_MAX = 5000
    yield
    stop_log_bus()


def _register(settings, port: int, sku: str = SKU, baud: int = 921600) -> None:
    settings.DEVICE_LOG_SOURCES = json.dumps({str(port): {"sku": sku, "baud": baud}})


def _write_log(settings, port: int, lines: list[FileLine]) -> None:
    sink = LogFileSink(sku=SKU, port=port, directory=str(settings.DEVICE_LOG_LOG_DIR))
    for line in lines:
        sink.write(line)
    sink.close()


# ── 5.1 端口列表 ─────────────────────────────────────────────


def test_list_requires_login(client) -> None:
    assert client.get(LIST_URL).status_code == 401


def test_list_returns_five_column_data(client, member, settings) -> None:
    """列表给出三列 + 开关 + 运行时监听/文件信息（snake_case、信封）。"""
    port = _free_port()
    _register(settings, port, baud=921600)
    response = client.get(LIST_URL, **_headers(member))
    assert response.status_code == 200
    body = response.json()
    assert body["status"] is True
    rows = body["data"]["ports"]
    assert len(rows) == 1
    row = rows[0]
    assert (row["port"], row["sku"], row["baud"]) == (port, "H6810", 921600)
    assert row["enabled"] is True
    assert row["log_file"] == f"H6810_{port}.log"
    assert set(row) >= {"port", "sku", "baud", "enabled", "listening", "log_file", "size_bytes"}


def test_list_reports_switch_state_after_toggle(client, admin, member, settings) -> None:
    port = _free_port()
    _register(settings, port)
    api.set_log_port_enabled(port, False)
    rows = client.get(LIST_URL, **_headers(member)).json()["data"]["ports"]
    assert rows[0]["enabled"] is False
    assert rows[0]["listening"] is False


# ── 5.2 开关 ─────────────────────────────────────────────────


def test_toggle_requires_superuser(client, member, settings) -> None:
    port = _free_port()
    _register(settings, port)
    response = client.post(
        TOGGLE_URL,
        {"port": port, "enabled": False},
        content_type="application/json",
        **_headers(member),
    )
    assert response.status_code == 403
    assert api.is_log_port_enabled(port) is True


def test_toggle_off_persists_and_reports_closed(client, admin, settings) -> None:
    port = _free_port()
    _register(settings, port)
    response = client.post(
        TOGGLE_URL,
        {"port": port, "enabled": False},
        content_type="application/json",
        **_headers(admin),
    )
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["enabled"] is False and data["listening"] is False
    assert data["note"] == f"端口 {port} 已关闭监听"
    assert api.is_log_port_enabled(port) is False


def test_toggle_on_starts_listening(client, admin, settings) -> None:
    port = _free_port()
    _register(settings, port)
    data = client.post(
        TOGGLE_URL,
        {"port": port, "enabled": True},
        content_type="application/json",
        **_headers(admin),
    ).json()["data"]
    assert data["enabled"] is True and data["listening"] is True


def test_toggle_unregistered_port_is_readable(client, admin, settings) -> None:
    """未登记端口：可读结论（400 + 中文说明），不是 500。"""
    _register(settings, 7005)
    response = client.post(
        TOGGLE_URL,
        {"port": 7004, "enabled": True},
        content_type="application/json",
        **_headers(admin),
    )
    assert response.status_code == 400
    assert "端口 7004 未配置为日志来源" in response.content.decode("utf-8")


def test_toggle_without_port_is_validation_error(client, admin, settings) -> None:
    _register(settings, 7005)
    response = client.post(TOGGLE_URL, {}, content_type="application/json", **_headers(admin))
    assert response.status_code == 400


# ── 5.3 日志行 ───────────────────────────────────────────────


def test_lines_requires_login(client, settings) -> None:
    port = _free_port()
    _register(settings, port)
    assert client.get(f"/api/ai/log-ports/{port}/lines/").status_code == 401


def test_lines_merge_same_ms_and_sort_newest_first(client, member, settings) -> None:
    port = _free_port()
    _register(settings, port)
    _write_log(
        settings,
        port,
        [
            FileLine(timestamp=STAMP, source="tcp", text="first"),
            FileLine(timestamp=STAMP, source="tcp", text="second"),
            FileLine(timestamp="2026-09-28 15:47:42.466", source="tcp", text="later"),
        ],
    )
    body = client.get(f"/api/ai/log-ports/{port}/lines/", **_headers(member)).json()
    data = body["data"]
    assert data["conclusion"] == "ok"
    assert data["line_count"] == 2 and data["raw_line_count"] == 3
    assert [item["timestamp"] for item in data["lines"]] == ["2026-09-28 15:47:42.466", STAMP]
    assert data["lines"][1]["text"] == "first\nsecond"
    assert data["log_file"] == f"H6810_{port}.log"


def test_lines_empty_file_reports_no_log(client, member, settings) -> None:
    port = _free_port()
    _register(settings, port)
    data = client.get(f"/api/ai/log-ports/{port}/lines/", **_headers(member)).json()["data"]
    assert data["conclusion"] == "no_log" and data["lines"] == []


def test_lines_unregistered_port_returns_readable_conclusion(client, member, settings) -> None:
    _register(settings, 7005)
    response = client.get("/api/ai/log-ports/7004/lines/", **_headers(member))
    assert response.status_code == 200
    data = response.json()["data"]
    assert data["conclusion"] == "port_not_configured"
    assert data["note"] == "端口 7004 未配置为日志来源"
    assert data["line_count"] == 0


def test_lines_disabled_port_returns_readable_conclusion(client, member, settings) -> None:
    port = _free_port()
    _register(settings, port)
    _write_log(settings, port, [FileLine(timestamp=STAMP, source="tcp", text="old-line")])
    api.set_log_port_enabled(port, False)

    data = client.get(f"/api/ai/log-ports/{port}/lines/", **_headers(member)).json()["data"]
    assert data["conclusion"] == "port_disabled"
    assert data["note"] == f"端口 {port} 已关闭监听"
    assert data["line_count"] == 0


def test_lines_tail_is_clamped(client, member, settings) -> None:
    port = _free_port()
    _register(settings, port)
    _write_log(
        settings,
        port,
        [
            FileLine(timestamp=f"2026-09-28 15:47:4{index}.000", source="tcp", text=f"line-{index}")
            for index in range(5)
        ],
    )
    limited = client.get(
        f"/api/ai/log-ports/{port}/lines/", {"tail": 2}, **_headers(member)
    ).json()["data"]
    assert limited["tail"] == 2 and limited["line_count"] == 2

    over = client.get(
        f"/api/ai/log-ports/{port}/lines/", {"tail": 999999}, **_headers(member)
    ).json()["data"]
    assert over["tail"] == 5000 and over["line_count"] == 5

    junk = client.get(
        f"/api/ai/log-ports/{port}/lines/", {"tail": "abc"}, **_headers(member)
    ).json()["data"]
    assert junk["tail"] == 2000


def test_lines_reads_current_file_only_not_archives(client, member, settings) -> None:
    """只读当前文件：存档里的行 MUST NOT 出现在结果里。"""
    port = _free_port()
    _register(settings, port)
    archive = Path(settings.DEVICE_LOG_LOG_DIR) / f"H6810_{port}_20260928.log"
    archive.write_text(f"{STAMP} [tcp] archived-line\n", encoding="utf-8")
    _write_log(settings, port, [FileLine(timestamp=STAMP, source="tcp", text="current-line")])

    data = client.get(f"/api/ai/log-ports/{port}/lines/", **_headers(member)).json()["data"]
    texts = [item["text"] for item in data["lines"]]
    assert texts == ["current-line"]
    assert "archived-line" not in "\n".join(texts)


def test_lines_tail_does_not_accept_a_file_name(client, member, settings) -> None:
    """文件名由后端按登记来源拼装：前端无法指定路径（防目录穿越）。"""
    port = _free_port()
    _register(settings, port)
    body = client.get(
        f"/api/ai/log-ports/{port}/lines/",
        {"tail": 10, "file": "../../../etc/passwd"},
        **_headers(member),
    ).json()
    assert body["status"] is True
    assert body["data"]["log_file"] == f"H6810_{port}.log"
