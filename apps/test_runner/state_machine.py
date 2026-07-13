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
  - Observable: every transition prints to stdout
"""

from datetime import datetime
from django.db import transaction
from django.db.models import Q
from .models import TaskCard, TestRunRecord, TestResult
from apps.device_pool.models import Device


class InvalidTransition(ValueError):
    """Raised when a state transition is not allowed."""


# ── Valid transition map ──
# (from_status, from_outcome) → allowed next (status, outcome)
_VALID_TRANSITIONS = {
    # idle → queued (enqueue)
    ("idle", ""): [("queued", "")],
    # queued → running (dequeue) or idle (cancel)
    ("queued", ""): [("running", ""), ("idle", "")],
    # running → done (complete / fail)
    ("running", ""): [
        ("done", "completed"),
        ("done", "stopped"),
        ("done", "interrupted"),
        ("done", "error"),
    ],
    # terminal states — no further transitions
    ("done", "completed"): [],
    ("done", "stopped"): [],
    ("done", "interrupted"): [],
    ("done", "error"): [],
}


def _validate(task_card, new_status, new_outcome):
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
    task_card, run_record, new_status, new_outcome, task_extra=None, run_extra=None
):
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
    if new_status == "running":
        task_card.running = True
    elif new_status == "done" or new_status == "idle":
        task_card.running = False
    if task_extra:
        for k, v in task_extra.items():
            setattr(task_card, k, v)
    task_card.save()

    if run_record and run_extra:
        for k, v in run_extra.items():
            setattr(run_record, k, v)
        run_record.save()

    print(f"[state] {task_card.task_id} → {new_status}/{new_outcome}")


# ═══════════════════════════════════════════════════════
# Public API — the ONLY way to change task/run state
# ═══════════════════════════════════════════════════════


def enqueue(task_card, device_serial):
    """TaskCard IDLE → QUEUED. Task is waiting for device availability."""
    _save_transition(task_card, None, "queued", "", task_extra={"device_serial": device_serial})


def cancel(task_card):
    """TaskCard QUEUED → IDLE. User cancelled the queued task."""
    _save_transition(task_card, None, "idle", "")


@transaction.atomic
def dequeue(task_card, run_id, device_serial, selected_cases, loop_count):
    """TaskCard QUEUED → RUNNING. Creates TestRunRecord atomically.

    Returns: TestRunRecord instance
    """
    _validate(task_card, "running", "")

    run_record = TestRunRecord.objects.create(
        run_id=run_id,
        client_task_id=task_card.task_id,
        status="RUNNING",
        device_serial=device_serial,
        selected_cases=selected_cases,
        loop_count=loop_count,
        started_at=datetime.now().isoformat(),
    )

    task_card = TaskCard.objects.select_for_update().get(pk=task_card.pk)
    task_card.status = "running"
    task_card.running = True
    task_card.run = run_record
    task_card.save(update_fields=["status", "running", "run"])

    print(f"[state] {task_card.task_id} → running, run_id={run_id}")
    return run_record


def record_iteration(run_record, case_id, iteration, result, duration_ms, detail=""):
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
    task_card,
    run_record,
    summary,
    case_items,
    overall_pass=0,
    overall_fail=0,
    csv_path="",
    log_path="",
):
    """TaskCard RUNNING → DONE (completed). Run finished successfully."""
    _save_transition(
        task_card,
        run_record,
        "done",
        "completed",
        task_extra={
            "case_items": case_items,
            "overall_pass": overall_pass,
            "overall_fail": overall_fail,
        },
        run_extra={
            "status": "COMPLETED",
            "summary": summary,
            "finished_at": datetime.now().isoformat(),
            "csv_path": csv_path,
            "log_path": log_path,
        },
    )


def fail(
    task_card,
    run_record,
    outcome="error",
    overall_pass=0,
    overall_fail=0,
    case_items=None,
    summary=None,
):
    """TaskCard RUNNING → DONE (error|stopped|interrupted).

    Args:
        outcome: one of 'error', 'stopped', 'interrupted'
        case_items: optional per-case aggregation to persist on the TaskCard
        summary: optional run summary to persist on the TestRunRecord
    """
    if outcome not in ("error", "stopped", "interrupted"):
        raise ValueError(f"Invalid outcome for fail(): {outcome}")
    run_status = {"error": "FAILED", "stopped": "STOPPED", "interrupted": "STOPPED"}[outcome]

    task_extra = {"overall_pass": overall_pass, "overall_fail": overall_fail}
    if case_items is not None:
        task_extra["case_items"] = case_items
    run_extra = {"status": run_status, "finished_at": datetime.now().isoformat()}
    if summary is not None:
        run_extra["summary"] = summary

    _save_transition(
        task_card,
        run_record,
        "done",
        outcome,
        task_extra=task_extra,
        run_extra=run_extra,
    )


def recover_orphans():
    """Startup recovery: fix ALL stale records from previous crashed session.

    Call this once in AppConfig.ready().
    Returns: dict with counts of what was fixed.
    """
    fixed = {"tasks": 0, "runs": 0}

    # 1. Orphan tasks → interrupted. Catch BOTH status='running' AND the
    #    inconsistent 'idle/queued + running=True' zombies left by non-atomic
    #    direct .update() writes (status/running dual-source drift).
    orphans = TaskCard.objects.filter(Q(status="running") | Q(running=True))
    count = orphans.count()
    if count:
        now = datetime.now().isoformat()
        for tc in orphans:
            tc.status = "done"
            tc.running = False
            tc.outcome = "interrupted"
            tc.save(update_fields=["status", "running", "outcome"])
            # Also fix linked TestRunRecord if exists
            if tc.run_id:
                TestRunRecord.objects.filter(id=tc.run_id).update(status="STOPPED", finished_at=now)
        fixed["tasks"] = count
        print(f"[state] recover_orphans: {count} running TaskCard(s) → interrupted")

    # 2. Stale TestRunRecord (RUNNING without active process) → FAILED
    stale_runs = TestRunRecord.objects.filter(
        status="RUNNING",
        finished_at="",
    )
    count = stale_runs.count()
    if count:
        now = datetime.now().isoformat()
        # Only fix runs NOT linked to an active (running) TaskCard
        running_task_run_ids = set(
            TaskCard.objects.filter(status="running", run_id__isnull=False).values_list(
                "run_id", flat=True
            )
        )
        stale_unlinked = stale_runs.exclude(id__in=running_task_run_ids)
        fixed_count = stale_unlinked.update(
            status="FAILED",
            finished_at=now,
        )
        if fixed_count:
            fixed["runs"] = fixed_count
            print(f"[state] recover_orphans: {fixed_count} stale TestRunRecord(s) → FAILED")

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
            from apps.device_pool.models import DeviceLock

            DeviceLock.objects.filter(device=dev, lock_type="process", status="active").update(
                status="released",
                released_at=datetime.now(),
                release_reason="disconnect",
            )
        except Exception:
            pass
    if busy_devices:
        fixed["devices"] = busy_devices.count()
        print(f"[state] recover_orphans: {busy_devices.count()} BUSY device(s) → ONLINE")

    return fixed


def repair_queued_terminal_drift() -> int:
    """修复 status=queued 但 outcome 已终态的数据漂移（历史 bug 遗留）。"""
    drift = TaskCard.objects.filter(
        status="queued",
        outcome__in=["completed", "stopped", "interrupted", "error"],
    )
    count = drift.count()
    if count:
        drift.update(status="done", running=False)
        print(f"[state] repair_queued_terminal_drift: {count} TaskCard(s) queued→done")
    return count
