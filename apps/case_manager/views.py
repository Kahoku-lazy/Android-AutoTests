"""case-manager HTTP routes — 12 endpoints under /api/cases/*."""

import json
from datetime import datetime
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from apps.element_locator.api import simple_yaml_dump
from apps.element_locator.models import Element, PageFlow
from .models import TestDefinition, TestCaseCache, CaseDirectory
from .api import get_directory_tree, create_directory, update_directory, delete_directory, batch_move_items


# ── Directory Management ──


def directory_list(request):
    """GET /api/cases/directories — Return full directory tree."""
    if request.method == "GET":
        tree = get_directory_tree()
        return JsonResponse({"ok": True, "tree": tree})
    return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)


@csrf_exempt
def directory_create(request):
    """POST /api/cases/directories/create — Create a directory."""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    data = json.loads(request.body)
    ok, result = create_directory(
        name=data.get("name", ""),
        parent_id=data.get("parent_id"),
        sort_order=data.get("sort_order", 0),
    )
    if ok:
        return JsonResponse({"ok": True, "directory": result})
    return JsonResponse({"ok": False, "error": result}, status=400)


@csrf_exempt
def directory_detail(request, dir_id):
    """POST /api/cases/directories/{id}/update or /delete."""
    if request.method == "POST":
        data = json.loads(request.body)
        action = data.get("action", "update")
        if action == "delete":
            ok, result = delete_directory(dir_id)
        else:
            ok, result = update_directory(
                dir_id,
                name=data.get("name"),
                parent_id=data.get("parent_id"),
                sort_order=data.get("sort_order"),
            )
        if ok:
            return JsonResponse({"ok": True, "result": result})
        status = 409 if isinstance(result, dict) else 400
        return JsonResponse(
            {
                "ok": False,
                "error": result if isinstance(result, str) else result.get("message", str(result)),
            },
            status=status,
        )
    return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)


@csrf_exempt
def directory_batch_move(request):
    """POST /api/cases/directories/batch-move — Batch move cases/directories."""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    data = json.loads(request.body)
    items = data.get("items", [])
    target_id = data.get("target_directory_id")
    if not isinstance(items, list) or not items:
        return JsonResponse({"ok": False, "error": "items 必须是非空数组"}, status=400)
    if target_id is None:
        return JsonResponse({"ok": False, "error": "target_directory_id 是必填项"}, status=400)
    result = batch_move_items(items, target_id)
    return JsonResponse({"ok": True, **result})


# ── Test Definition CRUD ──


@csrf_exempt
def definitions_handler(request):
    """GET/POST /api/cases/definitions."""
    if request.method == "GET":
        directory_id = request.GET.get("directory_id")
        qs = TestDefinition.objects.order_by("category", "title")

        if directory_id and directory_id.isdigit():
            # Include cases in this directory AND its subdirectories
            dir_ids = [int(directory_id)]
            sub_ids = CaseDirectory.objects.filter(
                parent_id=int(directory_id),
            ).values_list("id", flat=True)
            dir_ids.extend(sub_ids)
            qs = qs.filter(directory_id__in=dir_ids)

        defs = []
        for row in qs:
            d = _serialize_definition(row)
            defs.append(d)
        return JsonResponse({"ok": True, "definitions": defs})

    elif request.method == "POST":
        data = json.loads(request.body)
        case_id = data.get("id", "").strip()
        if not case_id:
            # Auto-generate: TC-YYYYMMDD-HHMMSS-XXXX
            now = datetime.now()
            import random, string

            suffix = "".join(random.choices(string.digits, k=4))
            case_id = f"TC-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{suffix}"

        steps_data = data.get("steps_data", [])
        steps_json = json.dumps(steps_data, ensure_ascii=False)

        # Auto-generate steps text summary from steps_data
        steps_summary = data.get("steps", "")
        if not steps_summary and isinstance(steps_data, list):
            lines = []
            for i, s in enumerate(steps_data):
                desc = s.get("description", "") or s.get("xpath", "") or ""
                desc_short = desc[:60]
                lines.append(f"{i + 1}. [{s.get('type', '?')}] {desc_short}")
            steps_summary = "\n".join(lines)

        directory = None
        directory_id = data.get("directory_id")
        if directory_id is not None:
            try:
                directory = CaseDirectory.objects.get(id=directory_id)
            except CaseDirectory.DoesNotExist:
                pass

        defaults = {
            "title": data.get("title", ""),
            "category": data.get("category", ""),
            "description": data.get("description", ""),
            "steps": steps_summary,
            "steps_json": steps_json,
            "enabled": bool(data.get("enabled", True)),
            "package_name": data.get("package_name", ""),
            "directory": directory,
            "priority": data.get("priority", "P1"),
            "design_method": data.get("design_method", ""),
            "precondition": data.get("precondition", ""),
            "expected_result": data.get("expected_result", ""),
            "metrics": data.get("metrics", ""),
        }
        TestDefinition.objects.update_or_create(id=case_id, defaults=defaults)
        return JsonResponse({"ok": True, "id": case_id})

    return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)


def definition_detail(request, case_id):
    """GET/DELETE /api/cases/definitions/{case_id}."""
    if request.method == "GET":
        try:
            row = TestDefinition.objects.get(id=case_id)
        except TestDefinition.DoesNotExist:
            return JsonResponse({"ok": False, "error": "not found"}, status=404)
        return JsonResponse({"ok": True, "definition": _serialize_definition(row)})

    elif request.method == "DELETE":
        TestDefinition.objects.filter(id=case_id).delete()
        return JsonResponse({"ok": True})

    return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)


@csrf_exempt
def definitions_batch(request):
    """POST /api/cases/definitions/batch — Batch import test definitions.

    Request body:
        {
            "cases": [{"id": "...", "title": "...", ...}, ...],
            "overwrite": false,
            "directory_id": null,
            "package_name": ""
        }
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "无效的 JSON"}, status=400)

    cases = data.get("cases", [])
    if not isinstance(cases, list) or not cases:
        return JsonResponse({"ok": False, "error": "cases 必须是非空数组"}, status=400)
    if len(cases) > 500:
        return JsonResponse({"ok": False, "error": "单次批量导入最多 500 条用例"}, status=400)

    overwrite = data.get("overwrite", False)
    directory_id = data.get("directory_id")
    package_name = data.get("package_name", "")

    # Resolve directory
    directory = None
    if directory_id is not None:
        try:
            directory = CaseDirectory.objects.get(id=directory_id)
        except CaseDirectory.DoesNotExist:
            pass

    from .api import batch_save_definitions

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
                "package_name": c.get("package_name", package_name),
                "directory_id": directory_id,
                "priority": c.get("priority", "P1"),
                "design_method": c.get("design_method", c.get("method", "")),
                "precondition": c.get("precondition", ""),
                "expected_result": c.get("expected_result", ""),
                "metrics": c.get("metrics", ""),
            }
        )

    result = batch_save_definitions(normalized, overwrite=overwrite)
    return JsonResponse({"ok": True, **result})


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
        "created_at": str(row.created_at),
        "updated_at": str(row.updated_at),
        "directory_id": row.directory_id,
        "directory_name": row.directory.name if row.directory else None,
        # IoT PRD fields
        "priority": row.priority,
        "design_method": row.design_method,
        "precondition": row.precondition,
        "expected_result": row.expected_result,
        "metrics": row.metrics,
    }
    try:
        d["steps_data"] = json.loads(row.steps_json or "[]")
    except Exception:
        d["steps_data"] = []
    return d


# ── YAML Export ──


@csrf_exempt
def export_yaml(request):
    """POST /api/cases/export/yaml — Export test points as YAML."""
    data = json.loads(request.body)
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

    TestCaseCache.objects.create(
        name=data.get("test_case_name", "auto"),
        description="",
        yaml_content=yaml_str,
    )

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
