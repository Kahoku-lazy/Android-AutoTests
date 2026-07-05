"""report-generator HTTP routes — 3 endpoints under /api/reports/*."""
from datetime import datetime
from pathlib import Path
from django.http import JsonResponse, FileResponse
from django.conf import settings


def list_reports(request):
    """GET /api/reports — List report files."""
    files = []
    log_dir = settings.LOG_DIR
    if log_dir.exists():
        report_files = list(log_dir.glob("*.csv")) + list(log_dir.glob("*.log")) + list(log_dir.glob("*.md"))
        # dedup
        seen = set()
        uniq = []
        for f in report_files:
            if f.name not in seen:
                seen.add(f.name)
                uniq.append(f)
        for f in sorted(uniq, key=lambda x: x.stat().st_mtime, reverse=True):
            suffix = f.suffix.lower()
            ftype = "csv" if suffix == ".csv" else "md" if suffix == ".md" else "log"
            files.append({
                "name": f.name, "size": f.stat().st_size,
                "time": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                "type": ftype,
            })
    return JsonResponse({"ok": True, "files": files})


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

    # Parse CSV into structured data for table display
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
