"""灰盒·单元测试 — 日志关键词只读目录（spec: device-log-keyword-catalog）。

零设备、零采集：只断言「取哪份表、给出什么、缺表怎么办」与端点的信封 / 权限。
覆盖：
1. 采集在跑（进程内已有总线）→ 取运行中的索引，origin=runtime；
2. 采集未创建 → 直读配置文件，origin=file；
3. 文件缺失 / 不可解析 → 空列表 + 可读 note，不抛错；
4. 计数口径（关键词数、功能点数按模块+编号+名称去重）与表内顺序保持；
5. 端点：未登录 401、登录 200，且响应不含任何写入口径。
"""

from __future__ import annotations

import json

from pathlib import Path

import pytest

from django.contrib.auth import get_user_model

from apps.ai_assistant import log_keywords
from engines.device.logbus import LogBusConfig, get_or_create_log_bus, stop_log_bus
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.unit, pytest.mark.django_db(transaction=True)]

User = get_user_model()

URL = "/api/ai/log-keywords/"

KEYWORDS = {
    "switch_on": [{"id": 0, "module": "设备开关", "feature": "打开设备成功"}],
    "blue_led_set_success": [{"id": 9, "module": "彩色模式", "feature": "手动-蓝灯设置成功"}],
    "color_configs_set_success": [
        {"id": 2, "module": "音效律动", "feature": "灯光颜色设置成功"},
        {"id": 17, "module": "彩色模式", "feature": "手动-颜色设置成功"},
    ],
    "switch_off": [{"id": 1, "module": "设备开关", "feature": "关闭设备成功"}],
}


def _headers(user) -> dict:
    return {"HTTP_AUTHORIZATION": f"Bearer {create_access_token(str(user.id))}"}


@pytest.fixture
def admin():
    return User.objects.create_superuser(username="kw_admin", password="x")


@pytest.fixture
def member():
    return User.objects.create_user(username="kw_member", password="x")


@pytest.fixture
def keyword_file(tmp_path: Path, settings) -> str:
    """把关键词表指到临时文件；本用例的文件内容与表内顺序固定。"""
    target = tmp_path / "device_log_keywords.json"
    target.write_text(
        json.dumps({"source": "stub", "keywords": KEYWORDS}, ensure_ascii=False), encoding="utf-8"
    )
    settings.DEVICE_LOG_KEYWORD_FILE = str(target)
    return str(target)


@pytest.fixture(autouse=True)
def _clean_bus():
    stop_log_bus()
    yield
    stop_log_bus()


def test_reads_file_when_no_running_bus(keyword_file) -> None:
    payload = log_keywords.collect_keywords()
    assert payload["origin"] == "file"
    assert [row["keyword"] for row in payload["keywords"]] == list(KEYWORDS)
    assert payload["keyword_count"] == 4
    # 功能点按「模块 + 编号 + 名称」去重：4 个关键词共 5 个不同功能点
    assert payload["feature_count"] == 5
    assert payload["keyword_file"] == keyword_file
    assert payload["updated_at"]
    assert payload["note"] == ""


def test_prefers_running_bus_index(keyword_file, tmp_path: Path) -> None:
    """有总线时取运行中的索引（判定真正在用的那份），而不是磁盘上 settings 指的那份。"""
    runtime = tmp_path / "runtime_keywords.json"
    runtime.write_text(
        json.dumps({"keywords": {"running_only": [{"id": 1, "module": "M", "feature": "F"}]}}),
        encoding="utf-8",
    )
    get_or_create_log_bus(LogBusConfig(enabled=False, keyword_file=str(runtime)))
    payload = log_keywords.collect_keywords()
    assert payload["origin"] == "runtime"
    assert [row["keyword"] for row in payload["keywords"]] == ["running_only"]


def test_missing_file_gives_readable_note(tmp_path: Path, settings) -> None:
    settings.DEVICE_LOG_KEYWORD_FILE = str(tmp_path / "missing.json")
    payload = log_keywords.collect_keywords()
    assert payload["keywords"] == []
    assert payload["keyword_count"] == 0
    assert payload["feature_count"] == 0
    assert payload["origin"] == "none"
    assert "不可用" in payload["note"]


def test_broken_file_gives_readable_note(tmp_path: Path, settings) -> None:
    target = tmp_path / "broken.json"
    target.write_text("{not json", encoding="utf-8")
    settings.DEVICE_LOG_KEYWORD_FILE = str(target)
    payload = log_keywords.collect_keywords()
    assert payload["keywords"] == []
    assert payload["origin"] == "none"
    assert payload["note"]


def test_unconfigured_file_gives_readable_note(settings) -> None:
    settings.DEVICE_LOG_KEYWORD_FILE = ""
    payload = log_keywords.collect_keywords()
    assert payload["keywords"] == []
    assert payload["origin"] == "none"
    assert "DEVICE_LOG_KEYWORD_FILE" in payload["note"]


def test_endpoint_requires_login(client, keyword_file) -> None:
    resp = client.get(URL)
    assert resp.status_code in (401, 403)


def test_endpoint_returns_catalog_to_member(client, member, keyword_file) -> None:
    """只读目录登录可读（与「无线端口」列表同口径），不要求超管。"""
    resp = client.get(URL, **_headers(member))
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] is True
    data = body["data"]
    assert data["keyword_count"] == 4
    assert data["keywords"][0]["keyword"] == "switch_on"
    assert data["keywords"][0]["features"][0]["module"] == "设备开关"
    # 一个关键词对应多个功能点时全部带出
    multi = next(row for row in data["keywords"] if row["keyword"] == "color_configs_set_success")
    assert [item["module"] for item in multi["features"]] == ["音效律动", "彩色模式"]
