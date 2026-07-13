"""report-generator HTTP routes — endpoints under /api/reports/*."""
from datetime import datetime, timedelta
from pathlib import Path
from django.http import JsonResponse, FileResponse
from django.conf import settings
from django.db.models import Count, Q

# ── Shared Q objects for test result filtering ──
# Used in Count('results', filter=...) on TestRunRecord → needs results__ prefix
PASS_Q = Q(results__result__iexact="pass") | Q(results__result__iexact="passed")
FAIL_Q = Q(results__result__iexact="fail") | Q(results__result__iexact="failed")

# Used directly on TestResult queries → no prefix needed
PASS_Q_DIRECT = Q(result__iexact="pass") | Q(result__iexact="passed")
FAIL_Q_DIRECT = Q(result__iexact="fail") | Q(result__iexact="failed")


def _safe_pct(part, total):
    """Return percentage as float, 0 if total is 0."""
    if total == 0:
        return 0.0
    return round(part / total * 100, 1)


# ── Helpers ──

def _compute_duration(started_at, finished_at):
    """Return human-readable duration string from two ISO timestamps."""
    if not started_at or not finished_at:
        return ""
    try:
        t1 = datetime.fromisoformat(started_at)
        t2 = datetime.fromisoformat(finished_at)
        secs = int((t2 - t1).total_seconds())
        if secs >= 60:
            return f"{secs // 60}m{secs % 60}s"
        return f"{secs}s"
    except Exception:
        return ""


# ── Run-level reports (DB-driven) ──

def list_reports(request):
    """GET /api/reports — List execution runs with optional date filter + KPI summary.

    Query params:
        start_date  ISO date string (e.g. 2026-07-01)
        end_date    ISO date string (e.g. 2026-07-13)
    """
    from apps.test_runner.models import TestRunRecord, TaskCard

    qs = TestRunRecord.objects.all()

    # ── Date filtering (started_at is CharField storing ISO timestamps) ──
    start_date = request.GET.get('start_date', '').strip()
    end_date = request.GET.get('end_date', '').strip()
    if start_date:
        qs = qs.filter(started_at__gte=start_date)
    if end_date:
        try:
            end_dt = datetime.fromisoformat(end_date) + timedelta(days=1)
            qs = qs.filter(started_at__lt=end_dt.isoformat())
        except ValueError:
            pass

    # ── Annotate with pass/fail counts ──
    annotated = qs.annotate(
        total=Count('results'),
        passed=Count('results', filter=PASS_Q),
    )

    # ── KPI summary computed from resolved pass/fail (see loop below) ──

    # ── Paginated rows for display ──
    rows = annotated.order_by('-id')[:50]

    # ── Bulk-fetch TaskCard data (single query, no N+1) ──
    # TaskCard.overall_pass/overall_fail is the source of truth for pass/fail counts.
    # TestResult aggregation is only a fallback for runs without a TaskCard.
    client_task_ids = [r.client_task_id for r in rows if r.client_task_id]
    task_map = {}
    if client_task_ids:
        tcs = TaskCard.objects.filter(task_id__in=client_task_ids).only(
            'task_id', 'name', 'creator', 'outcome',
            'overall_pass', 'overall_fail', 'case_ids', 'loop_count',
        )
        task_map = {tc.task_id: tc for tc in tcs}

    runs = []
    for r in rows:
        tc = task_map.get(r.client_task_id)
        if tc:
            # ── Use TaskCard data (source of truth) ──
            total = tc.overall_pass + tc.overall_fail
            passed = tc.overall_pass
            failed = tc.overall_fail
            case_count = len(tc.case_ids) if tc.case_ids else 0
        else:
            # ── Fallback: TestResult aggregation ──
            case_count = len(r.selected_cases) if r.selected_cases else 0
            total = r.total or 0
            passed = r.passed or 0
            failed = total - passed
        rate = round(passed / total * 100) if total else 0
        runs.append({
            "run_id": r.run_id,
            "status": r.status,
            "device_serial": r.device_serial,
            "loop_count": tc.loop_count if tc else r.loop_count,
            "case_count": case_count,
            "total": total,
            "passed": passed,
            "failed": failed,
            "rate": rate,
            "duration": _compute_duration(r.started_at, r.finished_at),
            "started_at": r.started_at,
            "finished_at": r.finished_at,
            "client_task_id": r.client_task_id or "",
            "task_name": tc.name if tc else None,
            "creator": tc.creator if tc else None,
            "outcome": tc.outcome if tc else None,
        })

    # ── KPI summary: aggregate from TaskCard data when available ──
    # Recompute over displayed rows using the resolved pass/fail values
    summary_total_pass = sum(r['passed'] for r in runs)
    summary_total_fail = sum(r['failed'] for r in runs)
    summary_total_iterations = summary_total_pass + summary_total_fail

    # ── Daily trend: group runs by day for pass/fail/rate chart ──
    from collections import defaultdict, OrderedDict
    daily = defaultdict(lambda: {"pass": 0, "fail": 0, "durations": []})
    for r in runs:
        if r["started_at"]:
            day = r["started_at"][:10]  # "2026-07-13"
            daily[day]["pass"] += r["passed"]
            daily[day]["fail"] += r["failed"]
            if r["duration"]:
                daily[day]["durations"].append(r["duration"])
    sorted_days = sorted(daily.keys())
    trend = {
        "labels": [d[5:] for d in sorted_days],  # "07-13"
        "pass": [daily[d]["pass"] for d in sorted_days],
        "fail": [daily[d]["fail"] for d in sorted_days],
        "rate": [
            round(daily[d]["pass"] / (daily[d]["pass"] + daily[d]["fail"]) * 100, 1)
            if (daily[d]["pass"] + daily[d]["fail"]) else 0
            for d in sorted_days
        ],
    }

    return JsonResponse({
        "ok": True,
        "summary": {
            "total_runs": len(runs),
            "total_iterations": summary_total_iterations,
            "total_pass": summary_total_pass,
            "total_fail": summary_total_fail,
            "pass_rate": _safe_pct(summary_total_pass, summary_total_iterations),
        },
        "trend": trend,
        "runs": runs,
    })


def run_report(request, run_id):
    """GET /api/reports/run/{run_id} — Full aggregated report for a single run."""
    from apps.test_runner.models import TestRunRecord, TestResult, TaskCard

    try:
        run_record = TestRunRecord.objects.get(run_id=run_id)
    except TestRunRecord.DoesNotExist:
        return JsonResponse({"ok": False, "error": "run not found"}, status=404)

    # ── Fetch linked TaskCard metadata ──
    task_card = None
    if run_record.client_task_id:
        try:
            task_card = TaskCard.objects.get(task_id=run_record.client_task_id)
        except TaskCard.DoesNotExist:
            task_card = None

    # ── Build case breakdown ──
    # TaskCard.case_items is source of truth for aggregate pass/fail counts.
    # TestResult rows provide per-iteration detail (result, duration, error info).
    cases = []
    total_pass = 0
    total_fail = 0

    # Always fetch TestResult for iteration-level details
    results_qs = TestResult.objects.filter(run=run_record).order_by('case_id', 'iteration')

    # Build title lookup from selected_cases snapshot
    title_map = {}
    for sc in (run_record.selected_cases or []):
        cid = sc.get("case_id", "")
        if cid:
            title_map[cid] = sc.get("title", cid)

    # Build iteration map from TestResult: case_id → [iteration_details]
    iter_map = {}
    for r in results_qs:
        cid = r.case_id or "unknown"
        if cid not in iter_map:
            iter_map[cid] = {"iterations": [], "title": title_map.get(cid, cid)}
        iter_map[cid]["iterations"].append({
            "iteration": r.iteration,
            "result": r.result,
            "duration_ms": round(r.duration_ms, 1) if r.duration_ms else 0,
            "detail": r.detail or "",
        })

    if task_card and task_card.case_items:
        # Use TaskCard aggregates + TestResult iteration details
        for ci in task_card.case_items:
            cid = str(ci.get('id', ''))
            p = ci.get('pass', 0) or 0
            f = ci.get('fail', 0) or 0
            it_info = iter_map.get(cid, {})
            cases.append({
                "case_id": cid,
                "case_title": ci.get('title', it_info.get('title', cid)),
                "planned": task_card.loop_count,
                "actual": p + f,
                "pass": p,
                "fail": f,
                "rate": round(p / (p + f) * 100) if (p + f) else 0,
                "iterations": it_info.get("iterations", []),
            })
            total_pass += p
            total_fail += f
    else:
        # Fallback: aggregate everything from TestResult rows
        for cid, it_info in iter_map.items():
            p = sum(1 for it in it_info["iterations"] if it["result"] == "pass")
            f = len(it_info["iterations"]) - p
            planned = run_record.loop_count
            actual = p + f
            cases.append({
                "case_id": cid,
                "case_title": it_info["title"],
                "planned": planned,
                "actual": actual,
                "pass": p,
                "fail": f,
                "rate": round(p / actual * 100) if actual else 0,
                "iterations": it_info["iterations"],
            })
            total_pass += p
            total_fail += f

    # Sort cases: failed first, then by case_id
    cases.sort(key=lambda c: (-c["fail"], c["case_id"]))

    total_iterations = total_pass + total_fail
    pass_rate = round(total_pass / total_iterations * 100, 1) if total_iterations else 0

    # Recent runs for trend chart — use TaskCard data when available
    recent_qs = (
        TestRunRecord.objects
        .annotate(
            total=Count('results'),
            passed=Count('results', filter=PASS_Q),
        )
        .order_by('-id')[:10]
    )
    # Bulk-fetch TaskCards for recent runs too
    recent_task_ids = [r.client_task_id for r in recent_qs if r.client_task_id]
    recent_task_map = {}
    if recent_task_ids:
        recent_tcs = TaskCard.objects.filter(task_id__in=recent_task_ids).only(
            'task_id', 'overall_pass', 'overall_fail',
        )
        recent_task_map = {tc.task_id: tc for tc in recent_tcs}

    recent_runs = []
    for r in reversed(list(recent_qs)):
        rtc = recent_task_map.get(r.client_task_id)
        if rtc and (rtc.overall_pass or rtc.overall_fail):
            t = rtc.overall_pass + rtc.overall_fail
            p = rtc.overall_pass
        else:
            t = r.total or 0
            p = r.passed or 0
        recent_runs.append({
            "run_id": r.run_id,
            "started_at": r.started_at,
            "total": t,
            "passed": p,
            "failed": t - p,
            "rate": round(p / t * 100) if t else 0,
        })

    return JsonResponse({
        "ok": True,
        "run": {
            "run_id": run_record.run_id,
            "status": run_record.status,
            "device_serial": run_record.device_serial,
            "loop_count": run_record.loop_count,
            "selected_cases": run_record.selected_cases,
            "started_at": run_record.started_at,
            "finished_at": run_record.finished_at,
            "duration": _compute_duration(run_record.started_at, run_record.finished_at),
            "total_iterations": total_iterations,
            "total_pass": total_pass,
            "total_fail": total_fail,
            "pass_rate": pass_rate,
            "case_count": len(cases),
            "cases": cases,
            "recent_runs": recent_runs,
            # ── TaskCard metadata (nullable) ──
            "client_task_id": run_record.client_task_id or "",
            "task_name": task_card.name if task_card else None,
            "task_creator": task_card.creator if task_card else None,
            "task_outcome": task_card.outcome if task_card else None,
            "task_conclusion": task_card.conclusion if task_card else None,
            "task_bug_ticket": task_card.bug_ticket if task_card else None,
            "task_failed_steps": task_card.failed_steps if task_card else None,
            "task_round": task_card.round if task_card else None,
        },
    })


# ── Task-level report (TaskCard perspective) ──

def task_report(request, task_id):
    """GET /api/reports/task/{task_id} — Comprehensive report from TaskCard perspective.

    Returns TaskCard metadata, case_items with steps, conclusion, bug analysis,
    and linked TestRunRecord summaries.
    """
    from apps.test_runner.models import TaskCard, TestRunRecord, TestResult

    try:
        tc = TaskCard.objects.get(task_id=task_id)
    except TaskCard.DoesNotExist:
        return JsonResponse({"ok": False, "error": "task not found"}, status=404)

    # ── Linked run summaries (last 10) ──
    run_records = TestRunRecord.objects.filter(
        client_task_id=task_id
    ).order_by('-id')[:10]

    linked_runs = []
    for rr in run_records:
        agg = TestResult.objects.filter(run=rr).aggregate(
            total=Count('id'),
            passed=Count('id', filter=PASS_Q_DIRECT),
        )
        t = agg['total'] or 0
        p = agg['passed'] or 0
        linked_runs.append({
            "run_id": rr.run_id,
            "status": rr.status,
            "device_serial": rr.device_serial,
            "loop_count": rr.loop_count,
            "total": t,
            "passed": p,
            "failed": t - p,
            "rate": round(p / t * 100) if t else 0,
            "started_at": rr.started_at,
            "finished_at": rr.finished_at,
            "duration": _compute_duration(rr.started_at, rr.finished_at),
        })

    case_items = tc.case_items or []
    overall_pass = tc.overall_pass or 0
    overall_fail = tc.overall_fail or 0

    return JsonResponse({
        "ok": True,
        "task": {
            "task_id": tc.task_id,
            "name": tc.name,
            "creator": tc.creator,
            "mode": tc.mode,
            "device_serial": tc.device_serial,
            "loop_count": tc.loop_count,
            "interval_seconds": tc.interval_seconds,
            "status": tc.status,
            "outcome": tc.outcome,
            "round": tc.round,
            "conclusion": tc.conclusion,
            "bug_ticket": tc.bug_ticket,
            "failed_steps": tc.failed_steps,
            "case_ids": tc.case_ids,
            "case_items": case_items,
            "overall_pass": overall_pass,
            "overall_fail": overall_fail,
            "pass_rate": _safe_pct(overall_pass, overall_pass + overall_fail),
            "created_at": str(tc.created_at),
            "updated_at": str(tc.updated_at),
            "linked_runs": linked_runs,
        },
    })


# ── File-based report endpoints (download / inline view) ──

def download_report(request, filename):
    """GET /api/reports/{filename} — Download report file."""
    safe_name = Path(filename).name
    fp = settings.LOG_DIR / safe_name
    if fp.exists():
        suffix = fp.suffix.lower()
        mt = "text/csv" if suffix == ".csv" else "text/markdown" if suffix == ".md" else "text/plain"
        response = FileResponse(open(str(fp), 'rb'), content_type=mt)
        response['Content-Disposition'] = f'attachment; filename="{safe_name}"'
        return response
    return JsonResponse({"ok": False, "error": "not found"}, status=404)


def view_report(request, filename):
    """GET /api/reports/{filename}/content — Return file content for inline viewing."""
    safe_name = Path(filename).name
    fp = settings.LOG_DIR / safe_name
    if not fp.exists():
        return JsonResponse({"ok": False, "error": "not found"}, status=404)

    try:
        content = fp.read_text(encoding="utf-8-sig")
    except Exception:
        try:
            content = fp.read_text(encoding="utf-8")
        except Exception:
            content = fp.read_text(encoding="latin-1")

    suffix = fp.suffix.lower()
    ftype = "csv" if suffix == ".csv" else "md" if suffix == ".md" else "log"

    rows = []
    if suffix == ".csv":
        lines = content.strip().split("\n")
        if lines:
            headers = [h.strip() for h in lines[0].split(",")]
            for line in lines[1:]:
                cols = [c.strip() for c in line.split(",")]
                if len(cols) == len(headers):
                    rows.append(dict(zip(headers, cols)))

    return JsonResponse({
        "ok": True,
        "name": safe_name,
        "type": ftype,
        "size": fp.stat().st_size,
        "content": content,
        "rows": rows,
        "headers": [h.strip() for h in content.split("\n")[0].split(",")] if suffix == ".csv" and content else [],
    })
