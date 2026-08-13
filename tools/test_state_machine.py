"""
SPEC: TaskCard 状态机全流转测试
用法: python tools/test_state_machine.py
"""

import os
import sys
import time

from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
import django

django.setup()

from apps.test_runner import state_machine as sm
from apps.test_runner.models import TaskCard, TestResult, TestRunRecord

PASS, FAIL, SKIP = 0, 0, 0
TEST_TASK_ID = f"SM-TEST-{int(time.time()) % 100000}"
_results = []


def title(msg):
    print(f"\n{'=' * 60}")
    print(f"  {msg}")
    print(f"{'=' * 60}")


def check(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        icon = "[PASS]"
    else:
        FAIL += 1
        icon = "[FAIL]"
    print(f"  {icon} {name}" + (f" -- {detail}" if detail else ""))
    _results.append({"name": name, "pass": bool(condition), "detail": detail})


def cleanup_test_data():
    """Remove test TaskCards and related records."""
    for tc in TaskCard.objects.filter(task_id__startswith="SM-TEST-"):
        if tc.run:
            TestResult.objects.filter(run=tc.run).delete()
            tc.run.delete()
        tc.delete()
    # Also clean orphan runs
    for r in TestRunRecord.objects.filter(run_id__startswith="SM-TEST-"):
        TestResult.objects.filter(run=r).delete()
        r.delete()


def make_task(status, outcome="", running=None, **kwargs):
    """Create a test TaskCard with given state."""
    tid = f"SM-TEST-{int(time.time() * 1000) % 1000000}"
    defaults = {
        "task_id": tid,
        "name": f"Test-{status}-{outcome}",
        "creator": "test",
        "task_type": "web_automation",
        "mode": "immediate",
        "device_serial": "web",
        "case_ids": ["WEB-20260728-155438-7389"],
        "loop_count": 1,
        "interval_seconds": 5,
        "status": status,
        "outcome": outcome,
    }
    defaults.update(kwargs)
    if running is not None:
        defaults["running"] = running
    else:
        defaults["running"] = status == "running"
    return TaskCard.objects.create(**defaults)


def make_run(run_id, status="RUNNING", finished_at=""):
    """Create a standalone TestRunRecord."""
    return TestRunRecord.objects.create(
        run_id=run_id,
        status=status,
        device_serial="web",
        selected_cases=[],
        loop_count=1,
        started_at=datetime.now().isoformat(),
        finished_at=finished_at,
    )


# ══════════════════════════════════════════════════
# 组 1: 正常生命线 idle → queued → running → done/completed
# ══════════════════════════════════════════════════
def test_group1():
    title("组 1: 正常生命线")

    # 1.1 idle → queued (sm.enqueue)
    tc = make_task("idle", "")
    try:
        sm.enqueue(tc, "web")
        tc.refresh_from_db()
        check("1.1 enqueue: status=queued", tc.status == "queued")
        check("1.1 enqueue: outcome 为空", tc.outcome == "")
        check("1.1 enqueue: running=False", tc.running == False)
    except Exception as e:
        check("1.1 enqueue", False, str(e))
    tc.delete()

    # 1.2 queued → running (sm.dequeue)
    tc = make_task("queued", "")
    run_id = f"SM-TEST-RUN-{int(time.time() * 1000) % 1000000}"
    try:
        run_record = sm.dequeue(tc, run_id, "web", [], 1)
        tc.refresh_from_db()
        check("1.2 dequeue: status=running", tc.status == "running")
        check("1.2 dequeue: outcome 为空", tc.outcome == "")
        check("1.2 dequeue: running=True", tc.running == True)
        check("1.2 dequeue: run FK 已关联", tc.run_id is not None)
        check("1.2 dequeue: TestRunRecord 已创建", run_record is not None)
        check("1.2 dequeue: TestRunRecord.status=RUNNING", run_record.status == "RUNNING")
    except Exception as e:
        check("1.2 dequeue", False, str(e))
        run_record = None
    # Cleanup for 1.2 — will be used in 1.3
    if run_record:
        run_record.delete()
    tc.delete()

    # 1.3 running → done/completed (sm.complete)
    tc = make_task("running", "")
    run = make_run(f"SM-TEST-COMPLETE-{int(time.time() * 1000) % 1000000}")
    tc.run = run
    tc.save(update_fields=["run"])
    try:
        sm.complete(
            tc,
            run,
            {"total": 1},
            [
                {
                    "id": "X",
                    "title": "T",
                    "total": 1,
                    "pass": 1,
                    "fail": 0,
                    "rate": 100,
                    "status": "done",
                }
            ],
            overall_pass=1,
        )
        tc.refresh_from_db()
        run.refresh_from_db()
        check("1.3 complete: status=done", tc.status == "done")
        check("1.3 complete: outcome=completed", tc.outcome == "completed")
        check("1.3 complete: running=False", tc.running == False)
        check("1.3 complete: case_items 已填充", len(tc.case_items) == 1)
        check("1.3 complete: RunRecord=COMPLETED", run.status == "COMPLETED")
        check("1.3 complete: RunRecord.finished_at 已设置", bool(run.finished_at))
    except Exception as e:
        check("1.3 complete", False, str(e))
    run.delete()
    tc.delete()


# ══════════════════════════════════════════════════
# 组 2: 取消排队 queued → idle
# ══════════════════════════════════════════════════
def test_group2():
    title("组 2: 取消排队")

    tc = make_task("queued", "")
    try:
        sm.cancel(tc)
        tc.refresh_from_db()
        check("2.1 cancel: status=idle", tc.status == "idle")
        check("2.1 cancel: outcome 为空", tc.outcome == "")
        check("2.1 cancel: running=False", tc.running == False)
    except Exception as e:
        check("2.1 cancel", False, str(e))
    tc.delete()


# ══════════════════════════════════════════════════
# 组 3: 手动停止 running → done/stopped
# ══════════════════════════════════════════════════
def test_group3():
    title("组 3: 手动停止")

    tc = make_task("running", "")
    run = make_run(f"SM-TEST-STOP-{int(time.time() * 1000) % 1000000}")
    tc.run = run
    tc.save(update_fields=["run"])
    try:
        sm.fail(tc, run, outcome="stopped")
        tc.refresh_from_db()
        run.refresh_from_db()
        check("3.1 fail(stopped): status=done", tc.status == "done")
        check("3.1 fail(stopped): outcome=stopped", tc.outcome == "stopped")
        check("3.1 fail(stopped): RunRecord=STOPPED", run.status == "STOPPED")
        check("3.1 fail(stopped): finished_at 已设置", bool(run.finished_at))
    except Exception as e:
        check("3.1 fail(stopped)", False, str(e))
    run.delete()
    tc.delete()


# ══════════════════════════════════════════════════
# 组 4: 异常终止 running → done/error
# ══════════════════════════════════════════════════
def test_group4():
    title("组 4: 异常终止")

    tc = make_task("running", "")
    run = make_run(f"SM-TEST-ERR-{int(time.time() * 1000) % 1000000}")
    tc.run = run
    tc.save(update_fields=["run"])
    try:
        sm.fail(tc, run, outcome="error")
        tc.refresh_from_db()
        run.refresh_from_db()
        check("4.1 fail(error): status=done", tc.status == "done")
        check("4.1 fail(error): outcome=error", tc.outcome == "error")
        check("4.1 fail(error): RunRecord=FAILED", run.status == "FAILED")
    except Exception as e:
        check("4.1 fail(error)", False, str(e))
    run.delete()
    tc.delete()


# ══════════════════════════════════════════════════
# 组 5: 孤儿恢复 running → done/interrupted
# ══════════════════════════════════════════════════
def test_group5():
    title("组 5: 孤儿恢复")

    # 5.1 running 孤儿恢复
    tc = make_task("running", "")
    run = make_run(f"SM-TEST-ORPHAN-{int(time.time() * 1000) % 1000000}")
    tc.run = run
    tc.save(update_fields=["run"])
    try:
        result = sm.recover_orphans()
        tc.refresh_from_db()
        run.refresh_from_db()
        check("5.1 recover_orphans: tasks 计数", result["tasks"] >= 1)
        check("5.1 recover_orphans: status=done", tc.status == "done")
        check("5.1 recover_orphans: outcome=interrupted", tc.outcome == "interrupted")
        check("5.1 recover_orphans: RunRecord=STOPPED", run.status == "STOPPED")
        check("5.1 recover_orphans: finished_at 已设置", bool(run.finished_at))
    except Exception as e:
        check("5.1 recover_orphans", False, str(e))
    run.delete()
    tc.delete()

    # 5.2 running=True 漂移孤儿（status=idle 但 running=True 的僵尸）
    tc = make_task("idle", "", running=True)
    try:
        result = sm.recover_orphans()
        tc.refresh_from_db()
        check("5.2 drift orphan: status=done", tc.status == "done")
        check("5.2 drift orphan: outcome=interrupted", tc.outcome == "interrupted")
    except Exception as e:
        check("5.2 drift orphan", False, str(e))
    tc.delete()

    # 5.3 孤儿 RunRecord（RUNNING 但无关联 TaskCard）
    orphan_run = make_run(f"SM-TEST-ORPHANRUN-{int(time.time() * 1000) % 1000000}")
    try:
        result = sm.recover_orphans()
        orphan_run.refresh_from_db()
        check(
            "5.3 stale run: RunRecord=FAILED",
            orphan_run.status == "FAILED",
            f"actual={orphan_run.status}",
        )
    except Exception as e:
        check("5.3 stale run", False, str(e))
    orphan_run.delete()


# ══════════════════════════════════════════════════
# 组 6: Web 多用例端到端执行
# ══════════════════════════════════════════════════
def test_group6():
    title("组 6: Web 端到端执行")

    import asyncio
    import json

    from apps.case_manager.models_web import WebTestCase
    from apps.test_runner.views.execution import _execute_unified_remote
    from models.step_types import TestStep
    from models.test_models import TestCaseDef

    def _build_tc(row):
        steps_raw = json.loads(getattr(row, "steps_json", "[]") or "[]")
        steps_data = [TestStep.from_dict(s) for s in steps_raw]
        return TestCaseDef(
            id=row.id,
            title=row.title,
            steps_data=steps_data,
            task_type="web_automation",
            extra_data={
                "url": getattr(row, "url", ""),
                "expected_result": getattr(row, "expected_result", ""),
            },
        )

    # 6.1 单用例执行
    try:
        row = WebTestCase.objects.get(id="WEB-20260728-155438-7389", enabled=True)
        tc_def = _build_tc(row)
        ts = str(int(time.time()))[-6:]
        task_id = f"SM-TEST-SINGLE-{ts}"

        task_card = TaskCard.objects.create(
            task_id=task_id,
            name=row.title,
            creator="test",
            task_type="web_automation",
            mode="immediate",
            device_serial="web",
            case_ids=[row.id],
            loop_count=1,
            interval_seconds=5,
            status="queued",
            running=False,
            start_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        async def _run():
            await _execute_unified_remote(
                task_id,
                [tc_def],
                1,
                5,
                client_task_id=task_id,
                task_type="web_automation",
                device_label="web",
            )

        asyncio.run(_run())

        task_card.refresh_from_db()
        results = list(TestResult.objects.filter(run__run_id=task_id))
        check(
            "6.1 single: TaskCard status=done",
            task_card.status == "done",
            f"actual={task_card.status}",
        )
        check("6.1 single: 产生了 TestResult", len(results) > 0, f"count={len(results)}")
        if results:
            check(
                "6.1 single: 至少 1 条 PASS",
                any(r.result == "pass" for r in results),
                f"results={[r.result for r in results]}",
            )

        # Cleanup
        TestResult.objects.filter(run__run_id=task_id).delete()
        if task_card.run:
            task_card.run.delete()
        task_card.delete()

    except Exception as e:
        import traceback

        traceback.print_exc()
        check("6.1 single case execution", False, str(e))

    # 6.2 多用例执行
    try:
        row1 = WebTestCase.objects.get(id="WEB-20260728-155438-7389", enabled=True)
        row2 = WebTestCase.objects.get(id="WEB-20260728-160030-1116", enabled=True)
        tc1 = _build_tc(row1)
        tc2 = _build_tc(row2)
        ts = str(int(time.time()))[-6:]
        task_id = f"SM-TEST-MULTI-{ts}"

        task_card = TaskCard.objects.create(
            task_id=task_id,
            name=f"{row1.title} + {row2.title}",
            creator="test",
            task_type="web_automation",
            mode="immediate",
            device_serial="web",
            case_ids=[row1.id, row2.id],
            loop_count=1,
            interval_seconds=5,
            status="queued",
            running=False,
            start_at=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        )

        async def _run2():
            await _execute_unified_remote(
                task_id,
                [tc1, tc2],
                1,
                5,
                client_task_id=task_id,
                task_type="web_automation",
                device_label="web",
            )

        asyncio.run(_run2())

        task_card.refresh_from_db()
        results = list(TestResult.objects.filter(run__run_id=task_id))
        check(
            "6.2 multi: TaskCard status=done",
            task_card.status == "done",
            f"actual={task_card.status}",
        )
        check("6.2 multi: 产生了 TestResult", len(results) > 0, f"count={len(results)}")

        # Group by case
        case_ids_found = set(r.case_id for r in results)
        check("6.2 multi: 两个 case 都有结果", len(case_ids_found) == 2, f"found={case_ids_found}")

        # Cleanup
        TestResult.objects.filter(run__run_id=task_id).delete()
        if task_card.run:
            task_card.run.delete()
        task_card.delete()

    except Exception as e:
        import traceback

        traceback.print_exc()
        check("6.2 multi case execution", False, str(e))


# ══════════════════════════════════════════════════
# 组 7: 非法流转防护
# ══════════════════════════════════════════════════
def test_group7():
    title("组 7: 非法流转防护")

    illegal_tests = [
        ("7.1 done/completed → enqueue", "done", "completed", lambda tc: sm.enqueue(tc, "web")),
        (
            "7.2 done/stopped → dequeue",
            "done",
            "stopped",
            lambda tc: sm.dequeue(tc, "X", "web", [], 1),
        ),
        (
            "7.3 done/interrupted → complete",
            "done",
            "interrupted",
            lambda tc, run: sm.complete(tc, run, {}, []),
        ),
        (
            "7.4 done/error → fail",
            "done",
            "error",
            lambda tc, run: sm.fail(tc, run, outcome="error"),
        ),
        (
            "7.5 idle → dequeue (skip queued)",
            "idle",
            "",
            lambda tc: sm.dequeue(tc, "X", "web", [], 1),
        ),
        (
            "7.6 queued → complete (skip running)",
            "queued",
            "",
            lambda tc, run: sm.complete(tc, run, {}, []),
        ),
    ]

    for name, status, outcome, fn in illegal_tests:
        tc = make_task(status, outcome)
        run = make_run(f"SM-TEST-ILLEGAL-{int(time.time() * 1000) % 1000000}")
        tc.run = run
        tc.save(update_fields=["run"])
        try:
            if "dequeue" in name:
                fn(tc)
            elif "enqueue" in name:
                fn(tc)
            else:
                fn(tc, run)
            check(f"{name}: 应抛 InvalidTransition", False, "未抛异常")
        except sm.InvalidTransition:
            check(f"{name}: InvalidTransition OK", True)
        except Exception as e:
            check(f"{name}: InvalidTransition", False, f"抛了其他异常: {type(e).__name__}: {e}")
        run.delete()
        tc.delete()


# ══════════════════════════════════════════════════
# Main
# ══════════════════════════════════════════════════
def main():
    global PASS, FAIL

    print("╔══════════════════════════════════════════════╗")
    print("║  TaskCard 状态机全流转测试                    ║")
    print("╚══════════════════════════════════════════════╝")

    cleanup_test_data()

    test_group1()
    test_group2()
    test_group3()
    test_group4()
    test_group5()
    test_group7()
    # 组 6 是端到端 Web 执行，耗时长，放最后
    test_group6()

    cleanup_test_data()

    print(f"\n{'=' * 60}")
    print(f"  结果: {PASS} PASS / {FAIL} FAIL / {PASS + FAIL} TOTAL")
    print(f"{'=' * 60}")

    return 0 if FAIL == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
