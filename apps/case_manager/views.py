"""case-manager HTTP routes — 8 endpoints under /api/cases/*."""
import json
from datetime import datetime
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from apps.element_locator.api import simple_yaml_dump
from apps.element_locator.models import Element, PageFlow
from .models import TestDefinition, TestCaseCache


# ── Test Definition CRUD ──

@csrf_exempt
def definitions_handler(request):
    """GET/POST /api/cases/definitions."""
    if request.method == 'GET':
        defs = []
        for row in TestDefinition.objects.order_by('category', 'title'):
            d = {
                "id": row.id, "title": row.title, "category": row.category,
                "description": row.description, "steps": row.steps,
                "enabled": row.enabled, "package_name": row.package_name,
                "created_at": str(row.created_at), "updated_at": str(row.updated_at),
            }
            try:
                d["steps_data"] = json.loads(row.steps_json or "[]")
            except Exception:
                d["steps_data"] = []
            defs.append(d)
        return JsonResponse({"ok": True, "definitions": defs})

    elif request.method == 'POST':
        data = json.loads(request.body)
        case_id = data.get("id", "").strip()
        if not case_id:
            # Auto-generate: TC-YYYYMMDD-HHMMSS-XXXX
            now = datetime.now()
            import random, string
            suffix = ''.join(random.choices(string.digits, k=4))
            case_id = f"TC-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{suffix}"

        steps_data = data.get("steps_data", [])
        steps_json = json.dumps(steps_data, ensure_ascii=False)

        # Auto-generate steps text summary from steps_data
        steps_summary = data.get("steps", "")
        if not steps_summary and isinstance(steps_data, list):
            lines = []
            for i, s in enumerate(steps_data):
                desc = s.get('description', '') or s.get('xpath', '') or ''
                desc_short = desc[:60]
                lines.append(f"{i+1}. [{s.get('type', '?')}] {desc_short}")
            steps_summary = '\n'.join(lines)

        defaults = {
            "title": data.get("title", ""),
            "category": data.get("category", ""),
            "description": data.get("description", ""),
            "steps": steps_summary,
            "steps_json": steps_json,
            "enabled": bool(data.get("enabled", True)),
            "package_name": data.get("package_name", ""),
        }
        TestDefinition.objects.update_or_create(id=case_id, defaults=defaults)
        return JsonResponse({"ok": True, "id": case_id})

    return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)


def definition_detail(request, case_id):
    """GET/DELETE /api/cases/definitions/{case_id}."""
    if request.method == 'GET':
        try:
            row = TestDefinition.objects.get(id=case_id)
        except TestDefinition.DoesNotExist:
            return JsonResponse({"ok": False, "error": "not found"}, status=404)
        d = {
            "id": row.id, "title": row.title, "category": row.category,
            "description": row.description, "steps": row.steps,
            "enabled": row.enabled, "package_name": row.package_name,
            "created_at": str(row.created_at), "updated_at": str(row.updated_at),
        }
        try:
            d["steps_data"] = json.loads(row.steps_json or "[]")
        except Exception:
            d["steps_data"] = []
        return JsonResponse({"ok": True, "definition": d})

    elif request.method == 'DELETE':
        TestDefinition.objects.filter(id=case_id).delete()
        return JsonResponse({"ok": True})

    return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)


# ── YAML Export ──

@csrf_exempt
def export_yaml(request):
    """POST /api/cases/export/yaml — Export test points as YAML."""
    data = json.loads(request.body)
    qs = Element.objects.filter(is_test_point=True).select_related('page')
    if data.get("page_ids"):
        qs = qs.filter(page_id__in=data["page_ids"])
    qs = qs.order_by('page_id', 'id')

    flows = PageFlow.objects.select_related('from_page', 'to_page').all()

    test_case = {
        "name": data.get("test_case_name", "auto_test"),
        "device": settings.DEVICE_SERIAL,
        "created_at": datetime.now().isoformat(),
        "pages": {}, "flows": [], "steps": [],
    }

    for el in qs:
        plabel = el.page.label or f"page_{el.page_id}"
        if plabel not in test_case["pages"]:
            test_case["pages"][plabel] = []
        test_case["pages"][plabel].append({
            "alias": el.alias or el.text_val or el.resource_id,
            "locator": {
                "resource_id": el.resource_id, "text": el.text_val,
                "content_desc": el.content_desc, "class": el.class_name,
                "bounds": el.bounds,
            },
            "action": "click" if el.clickable else "verify",
        })

    for f in flows:
        test_case["flows"].append({
            "from": f.from_page.label or f"page_{f.from_page_id}",
            "to": f.to_page.label or f"page_{f.to_page_id}",
            "trigger": (f.trigger_element.resource_id or f.trigger_element.text_val) if f.trigger_element else "unknown",
        })

    for plabel, els in test_case["pages"].items():
        test_case["steps"].append({"page": plabel, "actions": [{**e} for e in els]})

    yaml_str = simple_yaml_dump(test_case)

    filename = f"{data.get('test_case_name', 'test')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
    export_dir = settings.EXPORT_DIR
    export_dir.mkdir(parents=True, exist_ok=True)
    filepath = export_dir / filename
    filepath.write_text(yaml_str, encoding='utf-8')

    TestCaseCache.objects.create(
        name=data.get("test_case_name", "auto"), description="",
        yaml_content=yaml_str,
    )

    return JsonResponse({"ok": True, "filename": filename, "yaml": yaml_str})


def list_exports(request):
    """GET /api/cases/exports — List exported YAML files."""
    files = []
    export_dir = settings.EXPORT_DIR
    if export_dir.exists():
        for f in export_dir.glob("*.yaml"):
            files.append({
                "name": f.name, "size": f.stat().st_size,
                "time": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
            })
    files.sort(key=lambda x: x["time"], reverse=True)
    return JsonResponse({"ok": True, "files": files})


def download_export(request, filename):
    """GET /api/cases/exports/{filename} — Download YAML export."""
    fp = settings.EXPORT_DIR / filename
    if fp.exists():
        return FileResponse(fp, content_type="application/x-yaml", filename=filename)
    return JsonResponse({"ok": False, "error": "not found"}, status=404)
