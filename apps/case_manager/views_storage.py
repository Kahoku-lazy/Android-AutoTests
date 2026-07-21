"""case-manager storage test case endpoints — CRUD, batch."""

import json
import random
import string
from datetime import datetime
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

from .models import CaseDirectory
from .models_storage import StorageTestCase
from .api_storage import save_storage_definition, batch_save_storage_definitions
from .api_ui import _parse_datetime
from .views_helpers import resolve_username as _resolve_username


def _serialize_storage(row):
    """Convert a StorageTestCase ORM row to a dict for JSON responses."""
    d = {
        "id": row.id,
        "title": row.title,
        "case_type": row.case_type,
        "category": row.category,
        "description": row.description,
        "enabled": row.enabled,
        "priority": row.priority,
        "precondition": row.precondition,
        "steps": row.steps,
        "expected_result": row.expected_result,
        "custom_columns": row.custom_columns if isinstance(row.custom_columns, list) else [],
        "rows": row.rows if isinstance(row.rows, list) else [],
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
        "design_method": row.design_method,
        "metrics": row.metrics,
    }
    return d


@csrf_exempt
def storage_definitions_handler(request):
    """GET/POST /api/cases/storage/definitions."""
    if request.method == "GET":
        directory_id = request.GET.get("directory_id")
        qs = StorageTestCase.objects.order_by("category", "title")

        current_user = _resolve_username(getattr(request, 'user_id', None))
        restricted_q = Q(visibility="public") | Q(created_by=current_user)
        if current_user:
            restricted_q |= Q(visibility="restricted") & Q(
                permitted_users__icontains=f'"{current_user}"'
            )
        qs = qs.filter(restricted_q)

        if directory_id and directory_id.isdigit():
            dir_ids = [int(directory_id)]
            sub_ids = CaseDirectory.objects.filter(
                parent_id=int(directory_id),
            ).values_list("id", flat=True)
            dir_ids.extend(sub_ids)
            qs = qs.filter(directory_id__in=dir_ids)

        defs = [_serialize_storage(row) for row in qs]
        return JsonResponse({"ok": True, "definitions": defs})

    elif request.method == "POST":
        data = json.loads(request.body)
        case_id = data.get("id", "").strip()
        if not case_id:
            suffix = "".join(random.choices(string.digits, k=4))
            case_id = f"ST-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}-{suffix}"

        directory = None
        directory_id = data.get("directory_id")
        if directory_id is not None:
            try:
                directory = CaseDirectory.objects.get(id=directory_id)
            except CaseDirectory.DoesNotExist:
                pass

        current_user = _resolve_username(getattr(request, 'user_id', None))
        is_new_case = not StorageTestCase.objects.filter(id=case_id).exists()

        defaults = {
            "title": data.get("title", ""),
            "category": data.get("category", ""),
            "description": data.get("description", ""),
            "enabled": bool(data.get("enabled", True)),
            "directory": directory,
            "priority": data.get("priority", "P1"),
            "precondition": data.get("precondition", ""),
            "steps": data.get("steps", ""),
            "expected_result": data.get("expected_result", ""),
            "custom_columns": data.get("custom_columns", []),
            "rows": data.get("rows", []),
            "design_method": data.get("design_method", ""),
            "metrics": data.get("metrics", ""),
            "visibility": data.get("visibility", "public"),
            "permitted_users": json.dumps(data.get("permitted_users", []), ensure_ascii=False),
            "permission": data.get("permission", "edit"),
            "permitted_editors": json.dumps(data.get("permitted_editors", []), ensure_ascii=False),
            "case_type": "storage",
        }

        if is_new_case and current_user:
            defaults["created_by"] = current_user
        if current_user:
            defaults["updated_by"] = current_user

        title = defaults["title"]
        existing = (StorageTestCase.objects.filter(directory=directory, title=title)
                    .exclude(id=case_id).first())
        if existing:
            dir_name = directory.name if directory else "根级（未分类）"
            return JsonResponse({
                "ok": False,
                "error": f"目录「{dir_name}」下已存在同名存储用例「{title}」（ID: {existing.id}）",
            }, status=409)

        client_updated_at = data.get("updated_at")
        if case_id and client_updated_at:
            current = StorageTestCase.objects.filter(id=case_id).only("id", "updated_at").first()
            if current and current.updated_at:
                client_ts = _parse_datetime(client_updated_at)
                db_ts = current.updated_at.replace(microsecond=0)
                if client_ts and client_ts != db_ts:
                    return JsonResponse({
                        "ok": False,
                        "error": f"存储用例「{title or case_id}」已被他人修改，请刷新后重试",
                    }, status=409)

        StorageTestCase.objects.update_or_create(id=case_id, defaults=defaults)
        updated = StorageTestCase.objects.filter(id=case_id).only(
            "id", "updated_at", "title"
        ).first()
        resp = {"ok": True, "id": case_id}
        if updated and updated.updated_at:
            resp["updated_at"] = updated.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        return JsonResponse(resp)

    return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)


def storage_definition_detail(request, case_id):
    """GET/DELETE /api/cases/storage/definitions/{case_id}."""
    if request.method == "GET":
        try:
            row = StorageTestCase.objects.get(id=case_id)
        except StorageTestCase.DoesNotExist:
            return JsonResponse({"ok": False, "error": "not found"}, status=404)

        current_user = _resolve_username(getattr(request, 'user_id', None))
        if row.visibility == "hidden" and row.created_by != current_user:
            return JsonResponse({"ok": False, "error": "not found"}, status=404)
        if row.visibility == "restricted":
            permitted = json.loads(row.permitted_users or "[]")
            if row.created_by != current_user and current_user not in permitted:
                return JsonResponse({"ok": False, "error": "not found"}, status=404)

        return JsonResponse({"ok": True, "definition": _serialize_storage(row)})

    elif request.method == "DELETE":
        StorageTestCase.objects.filter(id=case_id).delete()
        return JsonResponse({"ok": True})

    return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)


@csrf_exempt
def storage_definitions_batch(request):
    """POST /api/cases/storage/definitions/batch — Batch import storage test cases."""
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

    normalized = []
    for c in cases:
        normalized.append({
            "case_id": c.get("id", c.get("case_id", "")),
            "title": c.get("title", ""),
            "category": c.get("category", ""),
            "description": c.get("description", ""),
            "enabled": c.get("enabled", False),
            "directory_id": directory_id,
            "priority": c.get("priority", "P1"),
            "data_schema": c.get("data_schema", {}),
            "operations": c.get("operations", []),
            "validation_rules": c.get("validation_rules", {}),
            "expected_data": c.get("expected_data", {}),
            "design_method": c.get("design_method", ""),
            "precondition": c.get("precondition", ""),
            "expected_result": c.get("expected_result", ""),
            "metrics": c.get("metrics", ""),
        })

    result = batch_save_storage_definitions(normalized, overwrite=overwrite)
    return JsonResponse({"ok": True, **result})
