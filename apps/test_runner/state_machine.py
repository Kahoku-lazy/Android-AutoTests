"""RunStateMachine — unified state manager for test execution tasks.

Replaces scattered state updates across runner.py / views.py / apps.py
with a single source of truth. Every TaskCard + TestRunRecord state
transition goes through this class. No code outside this file may
directly set TaskCard.status or TestRunRecord.status.

Design principles:
  - Single entry point for all state transitions
  - Atomic: TaskCard + TestRunRecord updated together in one transaction
  - Idempotent: repeating the same transition is a safe no-op
  - Validated: illegal transitions raise InvalidTransition
  - Observable: every transition logs via _log.info()
"""

import logging

from datetime import datetime
from typing import Optional

from django.db import transaction
from django.db.models import Q

from apps.device_pool.models import Device
from models.test_models import TaskCardStatus, TaskOutcome, TestRunStatus

from .models import TaskCard, TestResult, TestRunRecord

_log = logging.getLogger("test_runner.state")


class InvalidTransition(ValueError):
    """Raised when a state transition is not allowed."""


# ── Valid transition map ──
# (from_status, from_outcome) → allowed next (status, outcome)
_VALID_TRANSITIONS: dict = {
    # idle → queued (enqueue)
    (TaskCardStatus.IDLE.value, ""): [(TaskCardStatus.QUEUED.value, "")],
    # queued → running (dequeue) or idle (cancel)
    (TaskCardStatus.QUEUED.value, ""): [
        (TaskCardStatus.RUNNING.value, ""),
        (TaskCardStatus.IDLE.value, ""),
    ],
    # running → done (complete / fail)
    (TaskCardStatus.RUNNING.value, ""): [
        (TaskCardStatus.DONE.value, TaskOutcome.COMPLETED.value),
        (TaskCardStatus.DONE.value, TaskOutcome.STOPPED.value),
        (TaskCardStatus.DONE.value, TaskOutcome.INTERRUPTED.value),
        (TaskCardStatus.DONE.value, TaskOutcome.ERROR.value),
    ],
    # terminal states — no further transitions
    (TaskCardStatus.DONE.value, TaskOutcome.COMPLETED.value): [],
    (TaskCardStatus.DONE.value, TaskOutcome.STOPPED.value): [],
    (TaskCardStatus.DONE.value, TaskOutcome.INTERRUPTED.value): [],
    (TaskCardStatus.DONE.value, TaskOutcome.ERROR.value): [],
}


def _validate(task_card: TaskCard, new_status: str, new_outcome: str) -> None:
    """Raise InvalidTransition if the move is not allowed."""
    key = (task_card.status, task_card.outcome or "")
    allowed = _VALID_TRANSITIONS.get(key, [])
    target = (new_status, new_outcome)
    if target not in allowed:
        # Idempotent — same state is always OK
        if task_card.status == new_status and (task_card.outcome or "") == new_outcome:
            return
        raise InvalidTransition(
            f"TaskCard {task_card.task_id}: {task_card.status}/{task_card.outcome or ''}"
            f" → {new_status}/{new_outcome} is not a valid transition"
        )


@transaction.atomic
def _save_transition(
    task_card: TaskCard,
    run_record: Optional[TestRunRecord],
    new_status: str,
    new_outcome: str,
    task_extra: Optional[dict] = None,
    run_extra: Optional[dict] = None,
) -> None:
    """Atomic write: TaskCard + TestRunRecord in one transaction.

    Args:
        task_card: TaskCard instance (already fetched)
        run_record: TestRunRecord instance or None
        new_status: target TaskCard.status
        new_outcome: target TaskCard.outcome
        task_extra: dict of extra TaskCard fields to update
        run_extra: dict of extra TestRunRecord fields to update
    """
    task_card = TaskCard.objects.select_for_update().get(pk=task_card.pk)
    if run_record is not None:
        run_record = TestRunRecord.objects.select_for_update().get(pk=run_record.pk)

    _validate(task_card, new_status, new_outcome)

    task_card.status = new_status
    task_card.outcome = new_outcome
    if new_status == TaskCardStatus.RUNNING.value:
        task_card.running = True
    elif new_status == TaskCardStatus.DONE.value or new_status == TaskCardStatus.IDLE.value:
        task_card.running = False
    if task_extra:
        for k, v in task_extra.items():
            setattr(task_card, k, v)
    task_card.save()

    if run_record and run_extra:
        for k, v in run_extra.items():
            setattr(run_record, k, v)
        run_record.save()

    _log.info("%s → %s/%s", task_card.task_id, new_status, new_outcome)


# ═══════════════════════════════════════════════════════
# Public API — the ONLY way to change task/run state
# ═══════════════════════════════════════════════════════


def enqueue(task_card: TaskCard, device_serial: str) -> None:
    """TaskCard IDLE → QUEUED. Task is waiting for device availability."""
    _save_transition(
        task_card,
        None,
        TaskCardStatus.QUEUED.value,
        "",
        task_extra={"device_serial": device_serial},
    )


def cancel(task_card: TaskCard) -> None:
    """TaskCard QUEUED → IDLE. User cancelled the queued task."""
    _save_transition(task_card, None, TaskCardStatus.IDLE.value, "")


@transaction.atomic
def dequeue(
    task_card: TaskCard,
    run_id: str,
    device_serial: str,
    selected_cases: list[dict],
    loop_count: int,
) -> TestRunRecord:
    """TaskCard QUEUED → RUNNING. Creates or upgrades TestRunRecord atomically.

    AI 路径：start_run 已预建 PENDING 记录——复用并升级为 running（保留原
    started_at）；队列路径：记录不存在则新建。Returns: TestRunRecord instance
    """
    _validate(task_card, TaskCardStatus.RUNNING.value, "")

    run_record, created = TestRunRecord.objects.get_or_create(
        run_id=run_id,
        defaults={
            "client_task_id": task_card.task_id,
            "status": TestRunStatus.RUNNING.value,
            "device_serial": device_serial,
            "selected_cases": selected_cases,
            "loop_count": loop_count,
            "started_at": datetime.now().isoformat(),
        },
    )
    if not created:
        run_record.client_task_id = task_card.task_id
        run_record.status = TestRunStatus.RUNNING.value
        run_record.device_serial = device_serial
        run_record.selected_cases = selected_cases
        run_record.loop_count = loop_count
        run_record.save(
            update_fields=[
                "client_task_id",
                "status",
                "device_serial",
                "selected_cases",
                "loop_count",
            ]
        )

    task_card = TaskCard.objects.select_for_update().get(pk=task_card.pk)
    task_card.status = TaskCardStatus.RUNNING.value
    task_card.running = True
    task_card.run = run_record
    task_card.save(update_fields=["status", "running", "run"])

    _log.info("%s → running, run_id=%s", task_card.task_id, run_id)
    return run_record


def record_iteration(
    run_record: TestRunRecord,
    case_id: str,
    iteration: int,
    result: str,
    duration_ms: float,
    detail: str = "",
) -> None:
    """Append a single TestResult row. Does NOT change TaskCard state."""
    TestResult.objects.create(
        run=run_record,
        case_id=case_id,
        iteration=iteration,
        result=result,
        duration_ms=duration_ms,
        detail=detail,
    )


def complete(
    task_card: TaskCard,
    run_record: TestRunRecord,
    summary: dict,
    case_items: list[dict],
    overall_pass: int = 0,
    overall_fail: int = 0,
    csv_path: str = "",
    log_path: str = "",
) -> None:
    """TaskCard RUNNING → DONE (completed). Run finished successfully."""
    _save_transition(
        task_card,
        run_record,
        TaskCardStatus.DONE.value,
        TaskOutcome.COMPLETED.value,
        task_extra={
            "case_items": case_items,
            "overall_pass": overall_pass,
            "overall_fail": overall_fail,
        },
        run_extra={
            "status": TestRunStatus.COMPLETED.value,
            "summary": summary,
            "finished_at": datetime.now().isoformat(),
            "csv_path": csv_path,
            "log_path": log_path,
        },
    )


def fail(
    task_card: TaskCard,
    run_record: TestRunRecord,
    outcome: str = "error",
    overall_pass: int = 0,
    overall_fail: int = 0,
    case_items: Optional[list[dict]] = None,
    summary: Optional[dict] = None,
) -> None:
    """TaskCard RUNNING → DONE (error|stopped|interrupted).

    Args:
        outcome: one of 'error', 'stopped', 'interrupted'
        case_items: optional per-case aggregation to persist on the TaskCard
        summary: optional run summary to persist on the TestRunRecord
    """
    if outcome not in TaskOutcome.fail_values():
        raise ValueError(f"Invalid outcome for fail(): {outcome}")
    run_status = {
        TaskOutcome.ERROR.value: TestRunStatus.FAILED.value,
        TaskOutcome.STOPPED.value: TestRunStatus.STOPPED.value,
        TaskOutcome.INTERRUPTED.value: TestRunStatus.STOPPED.value,
    }[outcome]

    task_extra: dict = {"overall_pass": overall_pass, "overall_fail": overall_fail}
    if case_items is not None:
        task_extra["case_items"] = case_items
    run_extra: dict = {"status": run_status, "finished_at": datetime.now().isoformat()}
    if summary is not None:
        run_extra["summary"] = summary

    _save_transition(
        task_card,
        run_record,
        TaskCardStatus.DONE.value,
        outcome,
        task_extra=task_extra,
        run_extra=run_extra,
    )


def recover_orphans() -> dict[str, int]:
    """Startup recovery: fix ALL stale records from previous crashed session.

    Call this once in AppConfig.ready().
    Returns: dict with counts of what was fixed.
    """
    fixed: dict[str, int] = {"tasks": 0, "runs": 0}

    # 1. Orphan tasks → interrupted. Catch BOTH status='running' AND the
    #    inconsistent 'idle/queued + running=True' zombies left by non-atomic
    #    direct .update() writes (status/running dual-source drift).
    orphans = TaskCard.objects.filter(Q(status=TaskCardStatus.RUNNING.value) | Q(running=True))
    count = orphans.count()
    if count:
        now = datetime.now().isoformat()
        for tc in orphans:
            tc.status = TaskCardStatus.DONE.value
            tc.running = False
            tc.outcome = TaskOutcome.INTERRUPTED.value
            tc.save(update_fields=["status", "running", "outcome"])
            # Also fix linked TestRunRecord if exists
            if tc.run_id:
                TestRunRecord.objects.filter(run_id=tc.run_id).update(
                    status=TestRunStatus.STOPPED.value, finished_at=now
                )
        fixed["tasks"] = count
        _log.info("recover_orphans: %d running TaskCard(s) → interrupted", count)

    # 2. Stale TestRunRecord (RUNNING without active process) → FAILED
    stale_runs = TestRunRecord.objects.filter(
        status=TestRunStatus.RUNNING.value,
        finished_at="",
    )
    count = stale_runs.count()
    if count:
        now = datetime.now().isoformat()
        # Only fix runs NOT linked to an active (running) TaskCard
        running_task_run_ids = set(
            TaskCard.objects.filter(
                status=TaskCardStatus.RUNNING.value, run_id__isnull=False
            ).values_list("run_id", flat=True)
        )
        stale_unlinked = stale_runs.exclude(run_id__in=running_task_run_ids)
        fixed_count = stale_unlinked.update(
            status=TestRunStatus.FAILED.value,
            finished_at=now,
        )
        if fixed_count:
            fixed["runs"] = fixed_count
            _log.info("recover_orphans: %d stale TestRunRecord(s) → FAILED", fixed_count)

    # 3. Release devices occupied by crashed test-runner processes.
    #    Match by occupied_by prefix regardless of status — a device left
    #    ONLINE but still occupied_by='runner-*' is an orphaned lock too.
    busy_devices = Device.objects.filter(
        occupied_by__startswith="runner-",
    )
    for dev in busy_devices:
        dev.status = "ONLINE"
        dev.occupied_by = ""
        dev.occupied_at = None
        dev.save(update_fields=["status", "occupied_by", "occupied_at"])
        try:
            from apps.device_pool.api import release_device_locks_for_device

            release_device_locks_for_device(dev, reason="disconnect")
        except Exception:
            import logging

            logging.getLogger("test_runner.state").exception(
                "recover_orphans: release_device_locks_for_device(%s) failed, continuing", dev
            )
    if busy_devices:
        fixed["devices"] = busy_devices.count()
        _log.info("recover_orphans: %d BUSY device(s) → ONLINE", busy_devices.count())

    return fixed


def repair_queued_terminal_drift() -> int:
    """修复 status=queued 但 outcome 已终态的数据漂移（历史 bug 遗留）。"""
    drift = TaskCard.objects.filter(
        status=TaskCardStatus.QUEUED.value,
        outcome__in=TaskOutcome.terminal_values(),
    )
    count = drift.count()
    if count:
        drift.update(status=TaskCardStatus.DONE.value, running=False)
        _log.info("repair_queued_terminal_drift: %d TaskCard(s) queued→done", count)
    return count


def display_state(tc: TaskCard) -> str:
    """任务「处于什么状态」的权威判定（后端唯一入口，Step 5）。

    返回四值（与前端展示分桶一一对应）：
        running — 执行中
        queued  — 排队中
        done    — 已终态（终态原因见 tc.outcome）
        idle    — 未执行

    判定顺序与历史语义对齐（含 queued+终态漂移容错——DB 自愈由
    repair_queued_terminal_drift 负责，本函数对内存中脏行同样容错）。
    """
    if tc.running:
        return "running"
    if tc.status == TaskCardStatus.QUEUED.value:
        if tc.outcome in TaskOutcome.terminal_values():
            return "done"  # 历史漂移数据：queued + 终态 outcome → 已终态
        return "queued"
    if tc.outcome in TaskOutcome.terminal_values():
        return "done"
    return "idle"
