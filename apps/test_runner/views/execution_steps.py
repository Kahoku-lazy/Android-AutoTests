"""Test execution lifecycle steps — DB persistence + state machine transitions.

These @_bg_sync functions bridge sync Django ORM into the async execution flow.
Each function is independently callable and testable.
"""

import logging

from datetime import datetime

from .. import state_machine as sm
from ..models import TaskCard, TestResult, TestRunRecord
from .helpers import _bg_log, _bg_sync

_log = logging.getLogger("test_runner.bg")


# ── Pure helpers ──────────────────────────────────────────────────


def _build_case_snapshots(test_cases: list) -> list[dict]:
    """将用例列表序列化为快照，执行前冻结，后续编辑不影响审计记录。"""
    snapshots = []
    for tc in test_cases:
        snapshots.append(
            {
                "case_id": tc.id,
                "title": tc.title,
                "steps_data": [
                    s.to_dict()
                    if hasattr(s, "to_dict")
                    else (s.__dict__ if hasattr(s, "__dict__") else str(s))
                    for s in (tc.steps_data or [])
                ],
            }
        )
    return snapshots


def _compute_perf_stats(perf_results: list) -> dict | None:
    """Compute max, min, avg, median from perf_element_time measurements.

    Returns overall stats + per-case breakdown for frontend display.
    """
    if not perf_results:
        return None
    durations = [r["duration"] for r in perf_results]
    durations.sort()
    n = len(durations)
    if n % 2 == 1:
        median = durations[n // 2]
    else:
        median = (durations[n // 2 - 1] + durations[n // 2]) / 2

    # Per-case grouping
    by_case: dict[str, dict] = {}
    for r in perf_results:
        cid = r.get("case_id", "")
        if cid not in by_case:
            by_case[cid] = {
                "case_id": cid,
                "case_title": r.get("case_title", ""),
                "items": [],
                "durations": [],
            }
        by_case[cid]["items"].append(r)
        by_case[cid]["durations"].append(r["duration"])

    per_case = []
    for cid, cdata in by_case.items():
        cd = cdata["durations"]
        cd.sort()
        cn = len(cd)
        if cn % 2 == 1:
            cmedian = cd[cn // 2]
        else:
            cmedian = (cd[cn // 2 - 1] + cd[cn // 2]) / 2
        per_case.append(
            {
                "case_id": cid,
                "case_title": cdata["case_title"],
                "count": cn,
                "max": round(max(cd), 3),
                "min": round(min(cd), 3),
                "avg": round(sum(cd) / cn, 3),
                "median": round(cmedian, 3),
                "items": cdata["items"],
            }
        )

    return {
        "count": n,
        "max": round(max(durations), 3),
        "min": round(min(durations), 3),
        "avg": round(sum(durations) / n, 3),
        "median": round(median, 3),
        "per_case": per_case,
    }


# ── Lifecycle steps — @_bg_sync wraps sync ORM for async context ──


@_bg_sync
def _persist_run_start(
    client_tid: str,
    run_id: str,
    dev_serial: str,
    test_cases: list,
    loop_count: int,
) -> TestRunRecord:
    """冻结用例快照 → 走状态机 idle→queued→running → 创建 TestRunRecord。

    幂等：已处于 running 状态时直接返回已有记录。
    """
    snapshots = _build_case_snapshots(test_cases)

    tc_card = None
    if client_tid:
        try:
            tc_card = TaskCard.objects.get(task_id=client_tid)
        except TaskCard.DoesNotExist:
            tc_card = None

    if tc_card is not None:
        try:
            if tc_card.status == "queued":
                return sm.dequeue(tc_card, run_id, dev_serial, snapshots, loop_count)
            if tc_card.status == "idle":
                sm.enqueue(tc_card, dev_serial)
                # sm.enqueue() updates the DB row but not the in-memory instance
                # (it re-fetches inside _save_transaction). Refresh so the
                # subsequent sm.dequeue() sees status="queued" not "idle".
                tc_card.refresh_from_db()
                return sm.dequeue(tc_card, run_id, dev_serial, snapshots, loop_count)
            if tc_card.status == "running" and tc_card.run_id:
                return tc_card.run
            _bg_log.warning(
                "start_run skip transition %s: status=%s outcome=%s",
                client_tid,
                tc_card.status,
                tc_card.outcome or "",
            )
        except sm.InvalidTransition as e:
            _bg_log.warning("start_run transition %s: %s", client_tid, e)
        except Exception:
            _bg_log.exception("start_run %s failed", client_tid)

    return TestRunRecord.objects.create(
        run_id=run_id,
        client_task_id=client_tid or "",
        status="RUNNING",
        device_serial=dev_serial,
        selected_cases=snapshots,
        loop_count=loop_count,
        started_at=datetime.now().isoformat(),
    )


@_bg_sync
def _persist_case_results(run_record: TestRunRecord, run_model) -> None:
    """批量写入本轮所有 TestResult。"""
    if run_model is None:
        return
    results = [
        TestResult(
            run=run_record,
            case_id=r.case_id,
            case_type=r.case_type,
            iteration=r.iteration,
            result=r.result,
            duration_ms=r.duration_ms,
            detail=r.detail,
            step_details=getattr(r, "step_details", None) or [],
        )
        for r in (run_model.case_results or [])
    ]
    if results:
        TestResult.objects.bulk_create(results)


@_bg_sync
def _finalize_run(run_record: TestRunRecord, run_model, client_tid: str) -> None:
    """聚合 case_results → 组装 case_items + summary → 走状态机终态转换。

    终态判定优先级：
    1. 用户手动停止 (outcome=stopped/interrupted/error) → sm.fail
    2. runner 正常完成 (status=completed)                → sm.complete
    3. 其他 (status 异常)                                → sm.fail(stopped)
    """
    if run_model is None:
        return

    # ── 聚合 ──
    by_case: dict[str, dict] = {}
    overall_pass = 0
    overall_fail = 0
    for r in run_model.case_results:
        if r.case_id not in by_case:
            by_case[r.case_id] = {"pass": 0, "fail": 0, "total": 0}
        by_case[r.case_id]["total"] += 1
        if r.result == "pass":
            by_case[r.case_id]["pass"] += 1
            overall_pass += 1
        elif r.result in ("fail", "stopped"):
            by_case[r.case_id]["fail"] += 1
            overall_fail += 1

    tc_card = None
    if client_tid:
        try:
            tc_card = TaskCard.objects.get(task_id=client_tid)
        except TaskCard.DoesNotExist:
            tc_card = None

    case_items = []
    for cid, counts in by_case.items():
        # Title from selected_cases snapshot
        title = cid
        for sc in run_record.selected_cases or []:
            if sc.get("case_id") == cid:
                title = sc.get("title", cid)
                break
        # Preserve step definitions from existing TaskCard case_items
        steps = []
        if tc_card is not None:
            for old_ci in tc_card.case_items or []:
                if str(old_ci.get("id")) == str(cid) and old_ci.get("steps"):
                    steps = old_ci["steps"]
                    break
        item = {
            "id": cid,
            "title": title,
            "total": counts["total"],
            "pass": counts["pass"],
            "fail": counts["fail"],
            "rate": round(counts["pass"] / counts["total"] * 100) if counts["total"] else 0,
            "status": "done",
        }
        if steps:
            item["steps"] = steps
        case_items.append(item)

    # Compute perf stats — always if data exists
    perf_stats = _compute_perf_stats(run_model.perf_results)
    summary = dict(run_model.summary)
    if perf_stats:
        summary["_perf"] = perf_stats

    # ── 状态机终态转换 ──
    if tc_card is not None:
        try:
            if tc_card.outcome in ("stopped", "interrupted", "error"):
                sm.fail(
                    tc_card,
                    run_record,
                    outcome=tc_card.outcome,
                    overall_pass=overall_pass,
                    overall_fail=overall_fail,
                    case_items=case_items,
                    summary=summary,
                )
            elif run_model.status.value == "completed":
                sm.complete(
                    tc_card,
                    run_record,
                    summary,
                    case_items,
                    overall_pass=overall_pass,
                    overall_fail=overall_fail,
                )
            else:
                sm.fail(
                    tc_card,
                    run_record,
                    outcome="stopped",
                    overall_pass=overall_pass,
                    overall_fail=overall_fail,
                    case_items=case_items,
                    summary=summary,
                )
        except sm.InvalidTransition as e:
            _bg_log.warning("finalize transition %s: %s", client_tid, e)
        except Exception:
            _bg_log.exception("finalize %s failed", client_tid)
    else:
        run_record.status = run_model.status.value
        run_record.summary = summary
        run_record.finished_at = datetime.now().isoformat()
        run_record.save(update_fields=["status", "summary", "finished_at"])


@_bg_sync
def _mark_run_failed(
    run_record: TestRunRecord | None,
    run_model,
    client_tid: str,
) -> None:
    """异常路径兜底：尽力标记为 FAILED/error，抢救已产生的 perf 数据。

    不抛异常——这是最后的安全网，失败只能记录日志。
    """
    perf_stats = None
    if run_model and run_model.perf_results:
        perf_stats = _compute_perf_stats(run_model.perf_results)

    tc_card = None
    if client_tid:
        try:
            tc_card = TaskCard.objects.get(task_id=client_tid)
        except TaskCard.DoesNotExist:
            tc_card = None

    # 已有终态（用户手动停止等）→ 不动
    if tc_card is not None and tc_card.outcome not in (
        "stopped",
        "interrupted",
        "error",
    ):
        try:
            summary = dict(getattr(run_model, "summary", {}) or {})
            if perf_stats:
                summary["_perf"] = perf_stats
            sm.fail(tc_card, run_record, outcome="error", summary=summary)
            return  # fail() 内部已完结 run_record
        except sm.InvalidTransition as e:
            _bg_log.warning("mark_failed transition %s: %s", client_tid, e)
        except Exception:
            _bg_log.exception("mark_failed %s failed", client_tid)

    # TaskCard 终态/缺失/转换失败 → 降级为直接 finalize run_record
    if run_record:
        run_record.status = "FAILED"
        run_record.finished_at = datetime.now().isoformat()
        if perf_stats:
            run_record.summary = {**(run_record.summary or {}), "_perf": perf_stats}
            run_record.save(update_fields=["status", "finished_at", "summary"])
        else:
            run_record.save(update_fields=["status", "finished_at"])
