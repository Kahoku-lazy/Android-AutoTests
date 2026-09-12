"""report-generator HTTP routes — endpoints under /api/reports/*.

Execution-engine tables are gone; list/detail endpoints return empty shells.
File download/view still read LOG_DIR if files exist.
"""

from datetime import date, timedelta
from pathlib import Path

from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


def _empty_trend(range_days=30):
    end = date.today()
    start = end - timedelta(days=range_days - 1)
    dates = []
    labels = []
    zeros = []
    d = start
    while d <= end:
        dates.append(d.isoformat())
        labels.append(f"{d.month:02d}-{d.day:02d}")
        zeros.append(0)
        d += timedelta(days=1)
    return {
        "range_days": range_days,
        "dates": dates,
        "labels": labels,
        "pass": list(zeros),
        "fail": list(zeros),
        "rate": list(zeros),
    }


def list_reports(request):
    """GET /api/reports — empty list after execution engine removal."""
    chart_range = request.GET.get("chart_range", "30").strip()
    try:
        range_days = int(chart_range)
    except ValueError:
        range_days = 30
    if range_days not in (7, 30, 90):
        range_days = 30
    return JsonResponse(
        {
            "status": True,
            "summary": {
                "total_runs": 0,
                "total_iterations": 0,
                "total_pass": 0,
                "total_fail": 0,
                "pass_rate": 0.0,
            },
            "bug_summary": {},
            "trend": _empty_trend(range_days),
            "runs": [],
        }
    )


@csrf_exempt
def case_breakdown(request):
    """GET /api/reports/cases — empty groups after execution engine removal."""
    result_type = request.GET.get("result", "").strip().lower()
    if result_type not in ("pass", "fail"):
        return JsonResponse({"status": False, "message": "result 必须为 pass 或 fail"}, status=400)

    payload = {
        "status": True,
        "result_type": result_type,
        "total": 0,
        "case_count": 0,
        "groups": [],
    }
    if result_type == "fail":
        payload["bug_summary"] = {}
    return JsonResponse(payload)


@csrf_exempt
def run_report(request, run_id):
    """GET /api/reports/run/{run_id} — runs no longer exist."""
    return JsonResponse({"status": False, "message": "run not found"}, status=404)


@csrf_exempt
def task_report(request, task_id):
    """GET /api/reports/task/{task_id} — task cards no longer exist."""
    return JsonResponse({"status": False, "message": "task not found"}, status=404)


@csrf_exempt
def download_report(request, filename):
    """GET /api/reports/{filename} — Download report file."""
    safe_name = Path(filename).name
    fp = settings.LOG_DIR / safe_name
    if fp.exists():
        suffix = fp.suffix.lower()
        mt = (
            "text/csv" if suffix == ".csv" else "text/markdown" if suffix == ".md" else "text/plain"
        )
        response = FileResponse(open(str(fp), "rb"), content_type=mt)
        response["Content-Disposition"] = f'attachment; filename="{safe_name}"'
        return response
    return JsonResponse({"status": False, "message": "not found"}, status=404)


@csrf_exempt
def view_report(request, filename):
    """GET /api/reports/{filename}/content — Return file content for inline viewing."""
    safe_name = Path(filename).name
    fp = settings.LOG_DIR / safe_name
    if not fp.exists():
        return JsonResponse({"status": False, "message": "not found"}, status=404)

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

    return JsonResponse(
        {
            "status": True,
            "name": safe_name,
            "type": ftype,
            "size": fp.stat().st_size,
            "content": content,
            "rows": rows,
            "headers": [h.strip() for h in content.split("\n")[0].split(",")]
            if suffix == ".csv" and content
            else [],
        }
    )
