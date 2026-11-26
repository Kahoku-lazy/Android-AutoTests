from __future__ import annotations

import json

import pytest

from backend.apps.task_list import task_runner
from backend.apps.task_list.models import Task
from backend.apps.usage_ledger.models import ModelUsage
from backend.models.constants import TaskStatus
from engines.backend_bridge.reports import REPORT_ROOT

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

REPORT_PATH = REPORT_ROOT / "20260101_000000" / "20260101_000000_sop_bound.html"
USAGE_STAMP = "2026-11-25_18-23-21.317"
THINKING_REJECTION = "Error code: 400 - Thinking mode does not support this tool_choice"


class BadGatewayRequest(Exception):
    status_code = 400


BadGatewayRequest.__module__ = "openai"


def _resolved() -> dict:
    executor = {
        "run_name": "exec",
        "system_prompt": "sp",
        "provider": "deepseek",
        "api_key_env": "DEEPSEEK_API_KEY",
        "model_name": "deepseek-flash",
        "base_url": "",
        "tools": [],
    }
    verifier = dict(executor, run_name="ver", system_prompt="vp")
    return {"executor": executor, "verifier": verifier}


def _usage_snapshot() -> dict:
    return {
        "model": "deepseek-flash",
        "tokens": {"input": 1000, "output": 100, "cache_hit": 200, "cache_creation": 0},
        "usages": [
            {
                "round": 1,
                "api_key_env": "DEEPSEEK_API_KEY",
                "model": "deepseek-flash",
                "started_at": USAGE_STAMP,
                "input_tokens": 600,
                "output_tokens": 50,
                "cache_input_tokens": 100,
                "cache_creation_input_tokens": 0,
            },
            {
                "round": 2,
                "api_key_env": "DEEPSEEK_API_KEY",
                "model": "deepseek-flash",
                "started_at": USAGE_STAMP,
                "input_tokens": 400,
                "output_tokens": 50,
                "cache_input_tokens": 100,
                "cache_creation_input_tokens": 0,
            },
        ],
        "cost_s": 12.5,
    }


def _prepare(monkeypatch) -> Task:
    task = Task.objects.create(
        title="失败任务",
        task_kind="assistant_sop",
        orchestration="sop",
        status=TaskStatus.RUNNING,
        device_serial="",
        result=json.dumps({"workflow_id": 1}),
    )
    monkeypatch.setattr(task_runner, "close_old_connections", lambda: None)
    monkeypatch.setattr(
        task_runner, "_resolve_assistant_sop", lambda _task: (_resolved(), "steps: []")
    )
    monkeypatch.setattr("engines.ae_harness.workflow.sop.load_spec", lambda _path: object())
    return task


def _patch_run(monkeypatch, exc: Exception, usage: dict | None = None) -> None:
    async def fake_run_bound_sop(spec, executor, verifier, **kwargs):
        kwargs["on_abort"](REPORT_PATH, exc, usage or {})
        raise exc

    monkeypatch.setattr(
        "engines.backend_bridge.workflow.bound_sop.run_bound_sop", fake_run_bound_sop
    )


def test_failed_task_keeps_abort_report_locator(monkeypatch):
    task = _prepare(monkeypatch)
    _patch_run(monkeypatch, RuntimeError("模型拒绝（400）"))

    task_runner.run_task_async(task.id, 0)

    task.refresh_from_db()
    payload = json.loads(task.result)
    assert task.status == TaskStatus.FAILED
    assert payload["report_run"] == "20260101_000000"
    assert payload["report_name"] == "20260101_000000_sop_bound.html"
    assert payload["failure_kind"] == "platform"


def test_failed_task_records_abort_usage(monkeypatch):
    task = _prepare(monkeypatch)
    snapshot = _usage_snapshot()
    _patch_run(monkeypatch, RuntimeError("运行中断"), snapshot)

    task_runner.run_task_async(task.id, 0)

    task.refresh_from_db()
    assert task.status == TaskStatus.FAILED
    assert task.input_tokens == 1000
    assert task.output_tokens == 100
    assert task.cache_input_tokens == 200
    assert task.cost_total > 0
    rows = ModelUsage.objects.filter(execution_id=str(task.id), source="task")
    assert rows.count() == 2

    cost_before = task_runner.api.summarize_ledger_cost(task.id)[0]["cost_total"]
    task_runner._record_task_usages(snapshot["usages"], task.id, snapshot["model"])
    task.refresh_from_db()
    assert ModelUsage.objects.filter(execution_id=str(task.id), source="task").count() == 2
    assert task_runner.api.summarize_ledger_cost(task.id)[0]["cost_total"] == cost_before
    assert task.cost_total == cost_before


def test_thinking_rejection_names_handover_round(monkeypatch):
    task = _prepare(monkeypatch)
    _patch_run(monkeypatch, BadGatewayRequest(THINKING_REJECTION), _usage_snapshot())

    task_runner.run_task_async(task.id, 0)

    task.refresh_from_db()
    payload = json.loads(task.result)
    assert task.status == TaskStatus.FAILED
    assert payload["failure_kind"] == "provider"
    assert payload["reason"] == "交卷轮被思考模式拒绝（400）"
    assert payload["summary"] == payload["reason"]
    assert payload["failed_steps"][0]["name"] == "交卷轮被拒绝"
    assert payload["failed_steps"][0]["kind"] == "provider"
    assert "交卷轮" in payload["failed_steps"][0]["actual"]


def test_other_provider_400_keeps_original_wording(monkeypatch):
    task = _prepare(monkeypatch)
    _patch_run(monkeypatch, BadGatewayRequest("Error code: 400 - invalid request"))

    task_runner.run_task_async(task.id, 0)

    task.refresh_from_db()
    payload = json.loads(task.result)
    assert payload["failure_kind"] == "provider"
    assert payload["reason"] == "模型拒绝（400）"
    assert payload["failed_steps"][0]["name"] == "模型拒绝"
