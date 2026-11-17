"""终态只在仍为 running 时改写，失败原因进 JSON，不盖掉 workflow_id。"""

from __future__ import annotations

import json
import pytest

from backend.apps.task_list import api
from backend.apps.task_list.models import Task
from backend.apps.task_list.task_runner import _failure_payload, run_task_async
from types import SimpleNamespace
from backend.models.constants import TaskKind, TaskStatus
from engines.ae_harness.middleware.control import BudgetExceeded

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.unit]


def _task(status: str = TaskStatus.RUNNING) -> Task:
    return Task.objects.create(
        title="收口",
        status=status,
        task_kind=TaskKind.ASSISTANT_SOP,
        device_serial="DEV-A",
        result=api.dump_task_run_payload({"workflow_id": 7, "reason": "用户关闭"}),
    )


def test_claim_keeps_cancelled_and_workflow_id():
    task = _task(TaskStatus.CANCELLED)

    claimed = api.claim_terminal(
        task.id,
        status=TaskStatus.FAILED,
        result=api.dump_task_run_payload({"failure_kind": "platform", "reason": "平台执行错误"}),
        release_device=False,
    )

    task.refresh_from_db()
    assert claimed is None
    assert task.status == TaskStatus.CANCELLED
    assert "failure_kind" not in task.result
    assert json.loads(task.result)["workflow_id"] == 7


def test_second_claim_does_not_overwrite():
    task = _task()
    first = api.claim_terminal(
        task.id,
        status=TaskStatus.INTERRUPTED,
        result=api.dump_task_run_payload({"cause": "process_lost", "reason": "进程退出"}),
        release_device=False,
    )
    second = api.claim_terminal(
        task.id,
        status=TaskStatus.FAILED,
        result=api.dump_task_run_payload({"failure_kind": "platform", "reason": "后来的错误"}),
        release_device=False,
    )

    task.refresh_from_db()
    assert first is not None
    assert second is None
    assert task.status == TaskStatus.INTERRUPTED
    assert json.loads(task.result)["cause"] == "process_lost"
    assert json.loads(task.result)["workflow_id"] == 7


def test_exception_after_cancel_keeps_cancelled(monkeypatch):
    task = _task()
    api.claim_terminal(
        task.id,
        status=TaskStatus.CANCELLED,
        result=api.dump_task_run_payload({"reason": "用户关闭", "status": "cancelled"}),
        release_device=False,
    )

    def _boom(*_args, **_kwargs):
        raise RuntimeError("SynchronousOnlyOperation")

    monkeypatch.setattr("backend.apps.task_list.task_runner._resolve_assistant_sop", _boom)
    run_task_async(task.id, 0)

    task.refresh_from_db()
    assert task.status == TaskStatus.CANCELLED
    payload = json.loads(task.result)
    assert payload["workflow_id"] == 7
    assert "failure_kind" not in payload


def test_provider_preview_is_short_and_keeps_workflow():
    task = _task()

    class BadRequestError(Exception):
        status_code = 400

    BadRequestError.__module__ = "openai"
    body = _failure_payload(BadRequestError("Thinking mode does not support this tool_choice"))
    api.claim_terminal(
        task.id,
        status=TaskStatus.FAILED,
        result=api.dump_task_run_payload(body),
        release_device=False,
    )
    task.refresh_from_db()
    preview = api.task_result_preview(task.result)
    assert preview == "模型拒绝（400）"
    assert "Thinking mode" not in preview
    assert json.loads(task.result)["workflow_id"] == 7
    assert json.loads(task.result)["failure_kind"] == "provider"


def test_budget_is_interrupted_not_failed():
    task = _task()
    body = _failure_payload(BudgetExceeded("超限"))
    api.claim_terminal(
        task.id,
        status=TaskStatus.INTERRUPTED,
        result=api.dump_task_run_payload(body),
        release_device=False,
    )
    task.refresh_from_db()
    assert task.status == TaskStatus.INTERRUPTED
    assert json.loads(task.result)["cause"] == "budget"


def test_verdict_keeps_four_questions_and_workflow():
    task = _task()
    steps = [
        SimpleNamespace(
            subject="回到桌面",
            passed=False,
            attempts=3,
            message="没看到 dock",
            expected="设备停在桌面，能看见 dock",
        ),
        SimpleNamespace(subject="打开设置", passed=True, attempts=1, message="已打开", expected="设置页"),
    ]
    rows = api.failed_step_rows(steps, "verdict")
    api.claim_terminal(
        task.id,
        status=TaskStatus.FAILED,
        result=api.dump_task_run_payload(
            {
                "failure_kind": "verdict",
                "reason": "回到桌面：没看到 dock",
                "failed_steps": rows,
            }
        ),
        release_device=False,
    )

    task.refresh_from_db()
    payload = json.loads(task.result)
    assert payload["workflow_id"] == 7
    assert payload["failed_steps"] == [
        {
            "seq": 1,
            "name": "回到桌面",
            "expected": "设备停在桌面，能看见 dock",
            "actual": "没看到 dock",
            "attempts": 3,
            "kind": "verdict",
        }
    ]
    assert api.task_result_preview(task.result) == "回到桌面：没看到 dock"


def test_empty_steps_are_platform_category():
    row = api.category_step("platform", "没有步骤结论")
    assert row["name"] == "平台错误"
    assert row["expected"] == "每步都有验收结论"
    assert row["actual"] == "没有步骤结论"
    assert row["kind"] == "platform"


def test_provider_without_steps_is_one_category_step():
    class BadRequestError(Exception):
        status_code = 400

    BadRequestError.__module__ = "openai"
    body = _failure_payload(BadRequestError("raw gateway text"))
    row = body["failed_steps"][0]
    assert row["name"] == "模型拒绝"
    assert row["actual"] == "模型拒绝（400）"
    assert "gateway" not in row["actual"]


def test_exception_keeps_steps_already_failed():
    kept = [
        {
            "seq": 2,
            "name": "打开设置",
            "expected": "进入设置页",
            "actual": "仍在桌面",
            "attempts": 2,
            "kind": "verdict",
        }
    ]
    body = _failure_payload(RuntimeError("查库"), kept)
    assert body["failure_kind"] == "platform"
    assert body["failed_steps"] == kept
    assert api.task_result_preview(api.dump_task_run_payload(body)) == "查库"


def test_process_lost_step_names_the_interrupt():
    row = api.category_step("interrupted", "进程退出时任务仍在执行，结果未写回")
    assert row["name"] == "任务中断"
    assert row["expected"] == "流程应跑完"
    assert "服务重启" not in row["actual"]


def test_four_failure_kinds():
    assert _failure_payload(BudgetExceeded("x"))["cause"] == "budget"
    device = type("AdbError", (Exception,), {})("掉线")
    assert _failure_payload(device)["failure_kind"] == "device"
    platform = RuntimeError("查库")
    assert _failure_payload(platform)["failure_kind"] == "platform"
    assert _failure_payload(platform)["reason"] == "查库"
