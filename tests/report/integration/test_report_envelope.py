"""报告接口统一信封 — 集成测试（change: unify-report-envelope）。

覆盖：报告列表 / 内容查看 / 任务流程的成功与错误信封，文件下载仍为附件（非 JSON），
以及已删除的用例分解与 Run 详情端点确实不再存在。
"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.test import Client

from backend.shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.integration]


@pytest.fixture()
def client() -> Client:
    user = get_user_model().objects.create_user(username="report-envelope", password="x")
    return Client(HTTP_AUTHORIZATION="Bearer " + create_access_token(str(user.pk)))


def test_report_list_uses_standard_envelope(client, monkeypatch):
    from backend.apps.report_generator import views

    monkeypatch.setattr(
        views,
        "build_report_list",
        lambda *args, **kwargs: {"summary": {}, "trend": {}, "runs": []},
    )

    resp = client.get("/api/reports/")
    body = resp.json()

    assert resp.status_code == 200
    assert set(body) == {"status", "data"}
    assert body["status"] is True
    assert body["data"]["runs"] == []


def test_removed_report_endpoints_return_404(client):
    """用例分解与 Run 详情两个空壳端点已随页面删除，不再提供。"""
    assert client.get("/api/reports/cases/", {"result": "bogus"}).status_code == 404
    assert client.get("/api/reports/run/1/").status_code == 404


def test_report_content_uses_standard_envelope(client, monkeypatch, tmp_path):
    from django.conf import settings

    (tmp_path / "r.md").write_text("# hi", encoding="utf-8")
    monkeypatch.setattr(settings, "LOG_DIR", tmp_path)

    resp = client.get("/api/reports/r.md/content/")
    body = resp.json()

    assert resp.status_code == 200
    assert body["status"] is True
    assert body["data"]["name"] == "r.md"
    assert body["data"]["content"] == "# hi"


def test_report_content_missing_uses_error_envelope(client, monkeypatch, tmp_path):
    from django.conf import settings

    monkeypatch.setattr(settings, "LOG_DIR", tmp_path)

    resp = client.get("/api/reports/nope.md/content/")
    body = resp.json()

    assert resp.status_code == 404
    assert body["status"] is False
    assert body["message"] == "not found"


def test_report_download_stays_attachment(client, monkeypatch, tmp_path):
    from django.conf import settings

    (tmp_path / "r.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    monkeypatch.setattr(settings, "LOG_DIR", tmp_path)

    resp = client.get("/api/reports/r.csv/")

    assert resp.status_code == 200
    assert resp["Content-Type"].startswith("text/csv")
    assert "attachment" in resp["Content-Disposition"]


def test_task_flow_uses_standard_envelope(client, monkeypatch):
    from backend.apps.task_list import views

    payload = {"task": {"id": 1}, "rounds": [], "cases": [], "conclusion": None}
    monkeypatch.setattr(views, "report_cache_meta", lambda user_id, task_id: ("running", 0))
    monkeypatch.setattr(views, "build_task_flow", lambda user_id, task_id: payload)

    resp = client.get("/api/tasks/1/report/")
    body = resp.json()

    assert resp.status_code == 200
    assert body["status"] is True
    assert body["data"] == payload


def test_task_flow_missing_uses_error_envelope(client, monkeypatch):
    from backend.apps.task_list import views

    monkeypatch.setattr(views, "report_cache_meta", lambda user_id, task_id: ("failed", 0))
    monkeypatch.setattr(views, "build_task_flow", lambda user_id, task_id: None)

    resp = client.get("/api/tasks/1/report/")
    body = resp.json()

    assert resp.status_code == 404
    assert body["status"] is False
    assert body["message"] == "任务不存在"


def test_terminal_task_flow_is_cached_and_etagged(client, monkeypatch):
    """终态任务第二次请求不再重建，并且带上可复用的 ETag。"""
    from backend.apps.task_list import views

    calls = {"n": 0}
    payload = {"task": {"id": 9001}, "rounds": [], "cases": [], "conclusion": None}

    def fake_build(user_id, task_id):
        calls["n"] += 1
        return payload

    monkeypatch.setattr(views, "report_cache_meta", lambda user_id, task_id: ("failed", 9001))
    monkeypatch.setattr(views, "build_task_flow", fake_build)

    first = client.get("/api/tasks/9001/report/")
    second = client.get("/api/tasks/9001/report/")

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["data"] == payload
    assert calls["n"] == 1
    etag = first["ETag"]
    assert etag and second["ETag"] == etag

    third = client.get("/api/tasks/9001/report/", HTTP_IF_NONE_MATCH=etag)
    assert third.status_code == 304
    assert third.content == b""


def test_running_task_flow_is_not_cached(client, monkeypatch):
    """运行中任务每轮都可能新增事件，不能返回缓存。"""
    from backend.apps.task_list import views

    calls = {"n": 0}

    def fake_build(user_id, task_id):
        calls["n"] += 1
        return {"task": {"id": 9002}, "rounds": [], "cases": [], "conclusion": None}

    monkeypatch.setattr(views, "report_cache_meta", lambda user_id, task_id: ("running", 9002))
    monkeypatch.setattr(views, "build_task_flow", fake_build)

    client.get("/api/tasks/9002/report/")
    client.get("/api/tasks/9002/report/")

    assert calls["n"] == 2
