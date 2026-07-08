"""report-generator HTTP routes — endpoints under /api/reports/*."""
from datetime import datetime
from pathlib import Path
from django.http import JsonResponse, FileResponse
from django.conf import settings
from django.db.models import Count, Q


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
    """GET /api/reports — List execution runs as report entries."""
    from apps.test_runner.models import TestRunRecord

    rows = (
        TestRunRecord.objects
        .annotate(
            total=Count('results'),
            passed=Count('results', filter=Q(results__result='pass')),
        )
        .order_by('-id')[:50]
    )
    runs = []
    for r in rows:
        case_count = len(r.selected_cases) if r.selected_cases else 0
        total = r.total or 0
        passed = r.passed or 0
        failed = total - passed
        rate = round(passed / total * 100) if total else 0
        runs.append({
            "run_id": r.run_id,
            "status": r.status,
            "device_serial": r.device_serial,
            "loop_count": r.loop_count,
            "case_count": case_count,
            "total": total,
            "passed": passed,
            "failed": failed,
            "rate": rate,
            "duration": _compute_duration(r.started_at, r.finished_at),
            "started_at": r.started_at,
            "finished_at": r.finished_at,
        })
    return JsonResponse({"ok": True, "runs": runs})


def run_report(request, run_id):
    """GET /api/reports/run/{run_id} — Full aggregated report for a single run."""
    from apps.test_runner.models import TestRunRecord, TestResult

    try:
        run_record = TestRunRecord.objects.get(run_id=run_id)
    except TestRunRecord.DoesNotExist:
        return JsonResponse({"ok": False, "error": "run not found"}, status=404)

    results_qs = TestResult.objects.filter(run=run_record).order_by('case_id', 'iteration')

    # Build case title lookup from selected_cases snapshot
    title_map = {}
    for sc in (run_record.selected_cases or []):
        cid = sc.get("case_id", "")
        if cid:
            title_map[cid] = sc.get("title", cid)

    # Group results by case
    cases_map = {}
    total_pass = 0
    total_fail = 0

    for r in results_qs:
        cid = r.case_id or "unknown"
        if cid not in cases_map:
            cases_map[cid] = {
                "case_id": cid,
                "case_title": title_map.get(cid, cid),
                "iterations": [],
                "pass": 0,
                "fail": 0,
            }
        cases_map[cid]["iterations"].append({
            "iteration": r.iteration,
            "result": r.result,
            "duration_ms": round(r.duration_ms, 1) if r.duration_ms else 0,
            "detail": r.detail or "",
        })
        if r.result == 'pass':
            cases_map[cid]["pass"] += 1
            total_pass += 1
        else:
            cases_map[cid]["fail"] += 1
            total_fail += 1

    # Build case list with rates
    cases = []
    for cid, cd in cases_map.items():
        planned = run_record.loop_count
        actual = cd["pass"] + cd["fail"]
        cd["planned"] = planned
        cd["actual"] = actual
        cd["rate"] = round(cd["pass"] / actual * 100) if actual else 0
        cases.append(cd)

    # Sort cases: failed first, then by case_id
    cases.sort(key=lambda c: (-c["fail"], c["case_id"]))

    total_iterations = total_pass + total_fail
    pass_rate = round(total_pass / total_iterations * 100, 1) if total_iterations else 0

    # Recent runs for trend chart — last 10 runs
    recent_qs = (
        TestRunRecord.objects
        .annotate(
            total=Count('results'),
            passed=Count('results', filter=Q(results__result='pass')),
        )
        .order_by('-id')[:10]
    )
    recent_runs = []
    for r in reversed(list(recent_qs)):
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
