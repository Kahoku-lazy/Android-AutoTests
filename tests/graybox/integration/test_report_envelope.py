"""报告接口统一信封 — 集成测试（change: unify-report-envelope）。

覆盖：报告列表 / 用例分解 / 内容查看 / 任务流程的成功与错误信封，
以及文件下载仍为附件（非 JSON）。
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


def test_report_cases_invalid_result_uses_error_envelope(client):
    resp = client.get("/api/reports/cases/", {"result": "bogus"})
    body = resp.json()

    assert resp.status_code == 400
    assert body["status"] is False
    assert body["message"] == "result 必须为 pass 或 fail"


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
    monkeypatch.setattr(views, "build_task_flow", lambda user_id, task_id: payload)

    resp = client.get("/api/tasks/1/report/")
    body = resp.json()

    assert resp.status_code == 200
    assert body["status"] is True
    assert body["data"] == payload


def test_task_flow_missing_uses_error_envelope(client, monkeypatch):
    from backend.apps.task_list import views

    monkeypatch.setattr(views, "build_task_flow", lambda user_id, task_id: None)

    resp = client.get("/api/tasks/1/report/")
    body = resp.json()

    assert resp.status_code == 404
    assert body["status"] is False
    assert body["message"] == "任务不存在"
