"""case-manager UI automation endpoints — definitions CRUD, YAML export."""

import json
import logging
import random
import string

from datetime import datetime

from django.conf import settings
from django.http import FileResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.element_locator.api import simple_yaml_dump
from apps.element_locator.models import Element, PageFlow

from .api import batch_save_definitions
from .models import TestDefinition
from .views_base import (
    handle_batch_definitions,
    handle_definition_detail,
    handle_get_definitions,
    handle_post_definition,
)
from .views_helpers import resolve_username as _resolve_username

logger = logging.getLogger(__name__)


def _serialize_definition(row):
    """Convert a TestDefinition ORM row to a dict for JSON responses."""
    d = {
        "id": row.id,
        "title": row.title,
        "category": row.category,
        "description": row.description,
        "steps": row.steps,
        "enabled": row.enabled,
        "package_name": row.package_name,
        "case_type": getattr(row, "case_type", "ui_automation"),
        "created_at": str(row.created_at),
        "updated_at": str(row.updated_at),
        "created_by": _resolve_username(row.created_by) if row.created_by else "",
        "updated_by": _resolve_username(row.updated_by) if row.updated_by else "",
        "editing_by": _resolve_username(row.editing_by) if row.editing_by else "",
        "editing_since": str(row.editing_since) if row.editing_since else "",
        "locked": row.locked,
        "visibility": row.visibility,
        "permitted_users": json.loads(row.permitted_users or "[]"),
        "permission": row.permission,
        "permitted_editors": json.loads(row.permitted_editors or "[]"),
        "directory_id": row.directory_id,
        "directory_name": row.directory.name if row.directory else None,
        "priority": row.priority,
        "design_method": row.design_method,
        "precondition": row.precondition,
        "expected_result": row.expected_result,
        "metrics": row.metrics,
    }
    try:
        d["steps_data"] = json.loads(row.steps_json or "[]")
    except (json.JSONDecodeError, TypeError):
        d["steps_data"] = []
    try:
        d["watchers"] = (
            row.watchers if isinstance(row.watchers, list) else json.loads(row.watchers or "[]")
        )
    except (json.JSONDecodeError, TypeError):
        d["watchers"] = []
    return d


def _build_steps_summary(steps_data):
    """Auto-generate a human-readable steps text summary from steps_data."""
    lines = []
    for i, s in enumerate(steps_data):
        desc = s.get("description", "") or s.get("xpath", "") or ""
        desc_short = desc[:60]
        lines.append(f"{i + 1}. [{s.get('type', '?')}] {desc_short}")
    return "\n".join(lines)


def _normalize_ui_batch(cases, directory_id):
    """Normalize batch-imported UI cases to a standard format."""
    normalized = []
    for c in cases:
        normalized.append(
            {
                "case_id": c.get("id", c.get("case_id", "")),
                "title": c.get("title", ""),
                "category": c.get("category", c.get("method", "")),
                "description": c.get("description", ""),
                "steps": c.get("steps", ""),
                "steps_data": c.get("steps_data", []),
                "enabled": c.get("enabled", False),
                "package_name": c.get("package_name", ""),
                "directory_id": directory_id,
                "priority": c.get("priority", "P1"),
                "design_method": c.get("design_method", c.get("method", "")),
                "precondition": c.get("precondition", ""),
                "expected_result": c.get("expected_result", ""),
                "metrics": c.get("metrics", ""),
            }
        )
    return normalized


# ══════════════════════════════════════════════════════════════════
# UI Automation definitions CRUD
# ══════════════════════════════════════════════════════════════════


@csrf_exempt
def definitions_handler(request):
    """GET/POST /api/cases/definitions — UI automation case list and create/update."""
    if request.method == "GET":
        return handle_get_definitions(request, TestDefinition, _serialize_definition)

    elif request.method == "POST":
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse({"ok": False, "error": "无效的 JSON"}, status=400)

        case_id = data.get("id", "").strip()
        if not case_id:
            now = datetime.now()
            suffix = "".join(random.choices(string.digits, k=4))
            case_id = f"TC-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{suffix}"

        # UI-specific: auto-generate steps text summary from steps_data
        steps_data = data.get("steps_data", [])
        if not data.get("steps") and isinstance(steps_data, list):
            steps_summary = _build_steps_summary(steps_data)
        else:
            steps_summary = data.get("steps", "")

        defaults = {
            "title": data.get("title", ""),
            "category": data.get("category", ""),
            "description": data.get("description", ""),
            "steps": steps_summary,
            "steps_json": json.dumps(steps_data, ensure_ascii=False),
            "enabled": bool(data.get("enabled", True)),
            "package_name": data.get("package_name", ""),
            "priority": data.get("priority", "P1"),
            "design_method": data.get("design_method", ""),
            "precondition": data.get("precondition", ""),
            "expected_result": data.get("expected_result", ""),
            "metrics": data.get("metrics", ""),
            "visibility": data.get("visibility", "public"),
            "permitted_users": json.dumps(data.get("permitted_users", []), ensure_ascii=False),
            "permission": data.get("permission", "edit"),
            "permitted_editors": json.dumps(data.get("permitted_editors", []), ensure_ascii=False),
            "watchers": data.get("watchers", []),
            "case_type": "ui_automation",
            "_directory_id": data.get("directory_id"),
            "_client_updated_at": data.get("updated_at"),
        }

        return handle_post_definition(
            request,
            case_id,
            TestDefinition,
            "ui_automation",
            "用例",
            defaults,
        )

    return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)


def definition_detail(request, case_id):
    """GET/DELETE /api/cases/definitions/{case_id} — UI automation single case."""
    return handle_definition_detail(request, case_id, TestDefinition, _serialize_definition)


@csrf_exempt
def definitions_batch(request):
    """POST /api/cases/definitions/batch — Batch import UI automation test definitions."""
    return handle_batch_definitions(request, batch_save_definitions, _normalize_ui_batch)


# ══════════════════════════════════════════════════════════════════
# YAML Export (UI automation only)
# ══════════════════════════════════════════════════════════════════


@csrf_exempt
def export_yaml(request):
    """POST /api/cases/export/yaml — Export test points as YAML."""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "无效的 JSON"}, status=400)
    qs = Element.objects.filter(is_test_point=True).select_related("page")
    if data.get("page_ids"):
        qs = qs.filter(page_id__in=data["page_ids"])
    qs = qs.order_by("page_id", "id")

    flows = PageFlow.objects.select_related("from_page", "to_page").all()

    test_case = {
        "name": data.get("test_case_name", "auto_test"),
        "device": settings.DEVICE_SERIAL,
        "created_at": datetime.now().isoformat(),
        "pages": {},
        "flows": [],
        "steps": [],
    }

    for el in qs:
        plabel = el.page.label or f"page_{el.page_id}"
        if plabel not in test_case["pages"]:
            test_case["pages"][plabel] = []
        test_case["pages"][plabel].append(
            {
                "alias": el.alias or el.text_val or el.resource_id,
                "locator": {
                    "resource_id": el.resource_id,
                    "text": el.text_val,
                    "content_desc": el.content_desc,
                    "class": el.class_name,
                    "bounds": el.bounds,
                },
                "action": "click" if el.clickable else "verify",
            }
        )

    for f in flows:
        test_case["flows"].append(
            {
                "from": f.from_page.label or f"page_{f.from_page_id}",
                "to": f.to_page.label or f"page_{f.to_page_id}",
                "trigger": (f.trigger_element.resource_id or f.trigger_element.text_val)
                if f.trigger_element
                else "unknown",
            }
        )

    for plabel, els in test_case["pages"].items():
        test_case["steps"].append({"page": plabel, "actions": [{**e} for e in els]})

    yaml_str = simple_yaml_dump(test_case)

    filename = (
        f"{data.get('test_case_name', 'test')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.yaml"
    )
    export_dir = settings.EXPORT_DIR
    export_dir.mkdir(parents=True, exist_ok=True)
    filepath = export_dir / filename
    filepath.write_text(yaml_str, encoding="utf-8")

    return JsonResponse({"ok": True, "filename": filename, "yaml": yaml_str})


def list_exports(request):
    """GET /api/cases/exports — List exported YAML files."""
    files = []
    export_dir = settings.EXPORT_DIR
    if export_dir.exists():
        for f in export_dir.glob("*.yaml"):
            files.append(
                {
                    "name": f.name,
                    "size": f.stat().st_size,
                    "time": datetime.fromtimestamp(f.stat().st_mtime).isoformat(),
                }
            )
    files.sort(key=lambda x: x["time"], reverse=True)
    return JsonResponse({"ok": True, "files": files})


def download_export(request, filename):
    """GET /api/cases/exports/{filename} — Download YAML export."""
    fp = settings.EXPORT_DIR / filename
    if fp.exists():
        return FileResponse(fp, content_type="application/x-yaml", filename=filename)
    return JsonResponse({"ok": False, "error": "not found"}, status=404)
