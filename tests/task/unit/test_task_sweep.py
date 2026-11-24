"""心跳还在的任务不收；心跳停了收成中断，并拉起同设备排队。"""

from __future__ import annotations

import json

from datetime import timedelta
from unittest.mock import patch

import pytest

from django.utils import timezone

from backend.apps.task_list import api
from backend.apps.task_list.models import Task
from backend.models.constants import TaskStatus

pytestmark = [pytest.mark.django_db(transaction=True), pytest.mark.unit]


def _task(status: str, serial: str = "DEV-A") -> Task:
    return Task.objects.create(title="扫", status=status, device_serial=serial)


def test_fresh_heartbeat_is_not_swept():
    running = _task(TaskStatus.RUNNING)
    api.touch_heartbeat(running.id)
    pending = _task(TaskStatus.PENDING)

    assert api.sweep_stale_tasks() == 0
    running.refresh_from_db()
    pending.refresh_from_db()
    assert running.status == TaskStatus.RUNNING
    assert running.heartbeat_at is not None
    assert pending.status == TaskStatus.PENDING


def test_stale_heartbeat_becomes_process_lost_and_starts_pending():
    running = _task(TaskStatus.RUNNING)
    running.heartbeat_at = timezone.now() - timedelta(seconds=api.SWEEP_STALE_SECONDS + 5)
    running.save(update_fields=["heartbeat_at"])
    pending = _task(TaskStatus.PENDING)

    with patch("backend.apps.task_list.task_runner.spawn_task_thread") as spawn:
        assert api.sweep_stale_tasks() == 1
        spawn.assert_called_once()

    running.refresh_from_db()
    pending.refresh_from_db()
    assert running.status == TaskStatus.INTERRUPTED
    payload = json.loads(running.result)
    assert payload["cause"] == "process_lost"
    assert "服务重启" not in running.result
    assert payload["failed_steps"][0]["kind"] == "interrupted"
    assert payload["failed_steps"][0]["name"] == "任务中断"
    assert payload["failed_steps"][0]["expected"] == "流程应跑完"
    assert pending.status == TaskStatus.RUNNING


def test_running_ids_extracted_from_drain_payload():
    from utils.service_ctl import services as services_mod

    class _Resp:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

        def read(self):
            return b'{"status": true, "data": {"running": 2, "running_ids": [3, "4", "x"]}}'

    with patch("urllib.request.urlopen", return_value=_Resp()):
        base = "http://127.0.0.1/api/system/drain/"
        assert services_mod.running_ids_from_drain(base) == [3, 4]
    with patch("urllib.request.urlopen", side_effect=OSError("down")):
        assert services_mod.running_ids_from_drain(base) == []


def test_stop_timeout_mark_sets_cause_and_file_can_be_cleared(tmp_path, monkeypatch):
    from backend.apps.task_list import sweep_mark

    running = _task(TaskStatus.RUNNING)
    other = _task(TaskStatus.RUNNING, serial="DEV-B")
    monkeypatch.setattr(sweep_mark, "MARK", tmp_path / "stop-timeout-tasks.json")
    sweep_mark.write_stop_timeout_ids([running.id])

    assert api.sweep_stale_tasks(sweep_mark.read_stop_timeout_ids()) == 2
    running.refresh_from_db()
    other.refresh_from_db()
    assert json.loads(running.result)["cause"] == "stop_timeout"
    assert json.loads(other.result)["cause"] == "process_lost"
    sweep_mark.clear_stop_timeout_ids()
    assert sweep_mark.read_stop_timeout_ids() == set()
