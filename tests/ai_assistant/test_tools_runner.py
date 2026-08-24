"""测试执行 AI 工具 — schema / registry / handler / api.get_run_status 单元测试。

覆盖新增 get_run_status 与 get_run_results 信封化（run_status + results），
伪 Manager 零 DB。
"""

from types import SimpleNamespace

import pytest

from apps.ai_assistant.agent_scope import tool_registry

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]


# ── schema / registry ──


def test_get_run_status_schema_registered():
    s = next(t for t in tool_registry.TOOL_SCHEMAS if t["name"] == "get_run_status")
    assert s["module"] == "runner"
    assert s["action"] == "get_run_status"
    assert s["read_only"] is True
    assert s["category"] == "测试执行"


def test_get_run_results_summary_mentions_run_status():
    s = next(t for t in tool_registry.TOOL_SCHEMAS if t["name"] == "get_run_results")
    assert "run_status" in s["summary"]


def test_runner_status_handlers_resolvable():
    assert tool_registry.resolve("runner", "get_run_status") is not None
    assert tool_registry.resolve("runner", "get_run_results") is not None


# ── get_run_status handler ──


def test_get_run_status_handler_returns_digest(monkeypatch):
    from apps.test_runner import api as tr_api

    monkeypatch.setattr(
        tr_api,
        "get_run_status",
        lambda rid: {"run_id": rid, "status": "completed", "result_count": 3},
    )
    out = tool_registry.resolve("runner", "get_run_status")("7", run_id="R-1")
    assert out["status"] == "completed"
    assert out["result_count"] == 3


def test_get_run_status_handler_requires_run_id():
    with pytest.raises(ValueError, match="run_id"):
        tool_registry.resolve("runner", "get_run_status")("7")


def test_get_run_status_handler_missing_run_raises(monkeypatch):
    from apps.test_runner import api as tr_api

    monkeypatch.setattr(tr_api, "get_run_status", lambda rid: None)
    with pytest.raises(ValueError, match="run 不存在"):
        tool_registry.resolve("runner", "get_run_status")("7", run_id="R-X")


# ── get_run_results 信封 ──


def test_get_run_results_handler_envelope(monkeypatch):
    from apps.test_runner import api as tr_api

    monkeypatch.setattr(tr_api, "get_run_status", lambda rid: {"status": "RUNNING"})
    monkeypatch.setattr(tr_api, "get_run_results", lambda rid: [])
    out = tool_registry.resolve("runner", "get_run_results")("7", run_id="R-1")
    assert out == {"run_status": {"status": "RUNNING"}, "results": []}


def test_get_run_results_handler_missing_run_raises(monkeypatch):
    from apps.test_runner import api as tr_api

    monkeypatch.setattr(tr_api, "get_run_status", lambda rid: None)
    with pytest.raises(ValueError, match="run 不存在"):
        tool_registry.resolve("runner", "get_run_results")("7", run_id="R-X")


# ── api.get_run_status（伪 ORM）──


class _FakeCountQS:
    def __init__(self, count):
        self._count = count

    def filter(self, *args, **kwargs):
        return self

    def count(self):
        return self._count


def _patch_run_record(monkeypatch, rec):
    from apps.test_runner import api as tr_api

    class _Manager:
        def get(self, **kw):
            if rec is None:
                raise tr_api.TestRunRecord.DoesNotExist
            return rec

    monkeypatch.setattr(tr_api.TestRunRecord, "objects", _Manager())
    monkeypatch.setattr(tr_api.TestResult, "objects", _FakeCountQS(3))


def _rec(**kw):
    base = dict(
        run_id="R-1",
        status="completed",
        device_serial="SN1",
        client_task_id="",
        loop_count=1,
        selected_cases=[{"case_id": "TC-1", "title": "x", "steps_data": []}],
        summary={"x": {"pass": 2, "fail": 1, "rate": "67%"}},
        started_at="2026-08-20 10:00:00",
        finished_at="2026-08-20 10:05:00",
    )
    base.update(kw)
    return SimpleNamespace(**base)


def test_api_get_run_status_fields(monkeypatch):
    _patch_run_record(monkeypatch, _rec())
    from apps.test_runner.api import get_run_status

    d = get_run_status("R-1")
    assert d["status"] == "completed"
    assert d["device_serial"] == "SN1"
    assert d["result_count"] == 3
    assert d["selected_cases"][0]["case_id"] == "TC-1"
    assert d["summary"]["x"]["rate"] == "67%"
    assert d["finished_at"] == "2026-08-20 10:05:00"


def test_api_get_run_status_none_fields(monkeypatch):
    _patch_run_record(monkeypatch, _rec(selected_cases=None, summary=None, started_at=""))
    from apps.test_runner.api import get_run_status

    d = get_run_status("R-1")
    assert d["selected_cases"] == []
    assert d["summary"] == {}


def test_api_get_run_status_missing(monkeypatch):
    _patch_run_record(monkeypatch, None)
    from apps.test_runner.api import get_run_status

    assert get_run_status("R-X") is None
