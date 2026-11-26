from __future__ import annotations

import json

import pytest

from backend.apps.task_list import task_runner
from backend.apps.task_list.models import Task
from backend.models.constants import TaskStatus
from engines.backend_bridge.reports import REPORT_ROOT

pytestmark = [pytest.mark.integration, pytest.mark.django_db]

REPORT_PATH = REPORT_ROOT / "20260101_000000" / "20260101_000000_sop_bound.html"


def _resolved() -> dict:
    executor = {
        "run_name": "exec",
        "system_prompt": "sp",
        "provider": "deepseek",
        "api_key_env": "K1",
        "model_name": "m1",
        "base_url": "",
        "tools": [],
    }
    verifier = dict(executor, run_name="ver", system_prompt="vp", api_key_env="K2")
    return {"executor": executor, "verifier": verifier}


def test_failed_task_keeps_abort_report_locator(monkeypatch):
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

    async def fake_run_bound_sop(spec, executor, verifier, **kwargs):
        kwargs["on_abort"](REPORT_PATH, RuntimeError("模型拒绝（400）"))
        raise RuntimeError("模型拒绝（400）")

    monkeypatch.setattr(
        "engines.backend_bridge.workflow.bound_sop.run_bound_sop", fake_run_bound_sop
    )

    task_runner.run_task_async(task.id, 0)

    task.refresh_from_db()
    payload = json.loads(task.result)
    assert task.status == TaskStatus.FAILED
    assert payload["report_run"] == "20260101_000000"
    assert payload["report_name"] == "20260101_000000_sop_bound.html"
    assert payload["failure_kind"] == "platform"
