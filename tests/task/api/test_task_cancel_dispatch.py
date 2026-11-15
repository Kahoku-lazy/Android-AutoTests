"""关闭任务后的收尾：不提前放行设备槽、工作线程退出才放行、兜底超时告警、终态不被覆盖。"""

from __future__ import annotations

import threading

import pytest

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list import api, task_runner
from backend.apps.task_list.models import Task

pytestmark = [pytest.mark.django_db, pytest.mark.integration]

SERIAL = "R5CT62RH88F"


@pytest.fixture(autouse=True)
def _clean_registry():
    """每个用例前后清空工作线程与兜底计时器登记，避免互相影响。"""
    task_runner._workers.clear()
    task_runner._release_timers.clear()
    yield
    for timer in task_runner._release_timers.values():
        timer.cancel()
    task_runner._release_timers.clear()
    task_runner._workers.clear()


def _task(status: str = "running", serial: str = SERIAL) -> Task:
    """造一条任务；默认 running 且占着一台设备。"""
    agent = AIAgent.objects.create(name="关闭任务助手")
    return Task.objects.create(
        agent=agent,
        title="关闭任务",
        status=status,
        device_serial=serial,
    )


def test_cancel_does_not_release_device(monkeypatch):
    """关闭任务只写终态，不拉起同设备排队的任务。"""
    running = _task(status="running")
    pending = _task(status="pending")
    released: list[str] = []
    monkeypatch.setattr(api, "dispatch_device", lambda serial: released.append(serial))
    monkeypatch.setattr(
        task_runner, "schedule_cancel_release", lambda *args, **kwargs: None
    )

    cancelled = api.cancel_running_task(running)

    assert cancelled.status == "cancelled"
    assert cancelled.result == "用户关闭"
    assert released == []
    pending.refresh_from_db()
    assert pending.status == "pending"


def test_worker_exit_releases_device(monkeypatch):
    """工作线程退出时放行设备槽，并把登记清掉。"""
    released: list[str] = []
    monkeypatch.setattr(api, "dispatch_device", lambda serial: released.append(serial))
    task_runner._workers[9] = threading.current_thread()

    task_runner.release_device_now(9, SERIAL)

    assert released == [SERIAL]
    assert 9 not in task_runner._workers


def test_force_release_writes_alarm_when_thread_alive(monkeypatch):
    """工作线程超时仍存活：写一条告警事件，然后强制放行。"""
    alarms: list[tuple[int, int]] = []
    released: list[str] = []
    monkeypatch.setattr(api, "dispatch_device", lambda serial: released.append(serial))
    monkeypatch.setattr(
        task_runner, "_record_cancel_timeout", lambda task_id, agent_id: alarms.append((task_id, agent_id))
    )

    class _AliveThread:
        """替身：永远处于存活状态。"""

        def is_alive(self) -> bool:
            return True

    task_runner._workers[11] = _AliveThread()

    task_runner._force_release_device(11, SERIAL, 3)

    assert alarms == [(11, 3)]
    assert released == [SERIAL]


def test_force_release_skips_alarm_when_thread_gone(monkeypatch):
    """工作线程已退出：不写告警，只做放行。"""
    alarms: list[tuple[int, int]] = []
    released: list[str] = []
    monkeypatch.setattr(api, "dispatch_device", lambda serial: released.append(serial))
    monkeypatch.setattr(
        task_runner, "_record_cancel_timeout", lambda task_id, agent_id: alarms.append((task_id, agent_id))
    )

    task_runner._force_release_device(12, SERIAL, 3)

    assert alarms == []
    assert released == [SERIAL]


def test_schedule_cancel_release_skips_task_without_device(monkeypatch):
    """不占设备的任务不登记兜底计时器。"""
    task_runner.schedule_cancel_release(13, "", 3)

    assert task_runner._release_timers == {}


def test_cancelled_terminal_is_not_overwritten(monkeypatch):
    """取消后工作线程照常收尾，但终态仍是 cancelled，失败原因不写回。"""
    task = _task(status="cancelled", serial=SERIAL)
    task.result = "用户关闭"
    task.save(update_fields=["result"])
    released: list[str] = []
    monkeypatch.setattr(api, "dispatch_device", lambda serial: released.append(serial))
    monkeypatch.setattr(api, "materialize_config_file", lambda task: ("", False))
    monkeypatch.setattr(api, "build_sop_run_input", lambda task: "")
    monkeypatch.setattr(api, "set_config_load_message", lambda task, message: None)
    monkeypatch.setattr(
        "engines.agents.workflow.platform_run.run_platform_sop",
        lambda *args, **kwargs: {"status": "fail", "reason": "用例未完成", "completed": [], "failed": ["甲"]},
    )

    task_runner.run_task_async(task.id, task.agent_id)

    task.refresh_from_db()
    assert task.status == "cancelled"
    assert task.result == "用户关闭"
    assert released == [SERIAL]
