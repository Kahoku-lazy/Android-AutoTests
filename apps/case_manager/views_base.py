"""case-manager shared view handlers — eliminate duplicated CRUD across UI/Web/Storage/API views.

Each of the 4 views files (views_ui/web/storage/api) delegates its GET/POST/DELETE/Batch
to the helper functions below, keeping only type-specific serialization and field extraction.
"""

import json
import logging

from django.db.models import Q
from django.http import JsonResponse

from .api_api import save_api_definition
from .api_lock import delete_case
from .api_storage import save_storage_definition
from .api_ui import ConflictError, save_definition
from .api_web import save_web_definition
from .models import CaseDirectory, TestDefinition
from .models_api import ApiTestCase
from .models_storage import StorageTestCase
from .models_web import WebTestCase
from .views_helpers import resolve_username

logger = logging.getLogger(__name__)
BATCH_IMPORT_LIMIT = 500

# Model → save_* 分派映射（写操作收敛到 api 层单一写源）
_SAVE_FN = {
    TestDefinition: save_definition,
    ApiTestCase: save_api_definition,
    StorageTestCase: save_storage_definition,
    WebTestCase: save_web_definition,
}


# ═══════════════════════════════════════════════════════════════
# GET — visibility filter + directory expansion
# ═══════════════════════════════════════════════════════════════


def handle_get_definitions(request, Model, serialize_fn):
    """GET /api/cases/{type}/definitions — shared visibility + directory filter."""
    directory_id = request.GET.get("directory_id")
    qs = Model.objects.order_by("category", "title")

    current_user = resolve_username(getattr(request, "user_id", None))
    restricted_q = Q(visibility="public") | Q(created_by=current_user)
    if current_user:
        restricted_q |= Q(visibility="restricted") & Q(
            permitted_users__contains=f'"{current_user}"'
        )
    qs = qs.filter(restricted_q)

    if directory_id and directory_id.isdigit():
        did = int(directory_id)
        sub_ids = list(CaseDirectory.objects.filter(parent_id=did).values_list("id", flat=True))
        qs = qs.filter(directory_id__in=[did] + sub_ids)

    defs = [serialize_fn(row) for row in qs]
    return JsonResponse({"status": True, "definitions": defs})


# ═══════════════════════════════════════════════════════════════
# POST — shared create/update logic
# ═══════════════════════════════════════════════════════════════


def handle_post_definition(request, case_id, Model, case_type, error_label, fields):
    """POST /api/cases/{type}/definitions — shared create/update logic.

    写操作收敛：注入 created_by/updated_by 后按 Model 类型分派调用 save_*，
    由 api 层统一做乐观锁 + 重复 title 检查 + update_or_create。

    Args:
        request: Django request object.
        case_id: the case ID string (may be new auto-generated ID).
        Model: the ORM model class for this case type.
        case_type: "ui_automation" / "web_automation" / "storage" / "api_testing".
        error_label: "用例" / "Web 用例" / "存储用例" / "API 用例".
        fields: dict of raw fields（directory_id / client_updated_at / steps_data /
            permitted_users list 等），由 save_* 统一构造 defaults。
    """
    current_user = resolve_username(getattr(request, "user_id", None))
    is_new_case = not Model.objects.filter(id=case_id).exists()

    if is_new_case and current_user:
        fields["created_by"] = current_user
    if current_user:
        fields["updated_by"] = current_user

    save_fn = _SAVE_FN[Model]
    try:
        obj = save_fn(case_id, **fields)
    except ConflictError as e:
        return JsonResponse({"status": False, "message": str(e)}, status=409)
    except ValueError as e:
        return JsonResponse({"status": False, "message": str(e)}, status=409)

    resp = {"status": True, "id": case_id}
    if obj and obj.updated_at:
        resp["updated_at"] = obj.updated_at.strftime("%Y-%m-%d %H:%M:%S")
    return JsonResponse(resp)


# ═══════════════════════════════════════════════════════════════
# Detail — GET with visibility + DELETE
# ═══════════════════════════════════════════════════════════════


def handle_definition_detail(request, case_id, Model, serialize_fn):
    """GET/DELETE /api/cases/{type}/definitions/{id} — shared visibility check + delete."""
    if request.method == "GET":
        try:
            row = Model.objects.get(id=case_id)
        except Model.DoesNotExist:
            return JsonResponse({"status": False, "message": "not found"}, status=404)

        current_user = resolve_username(getattr(request, "user_id", None))
        if row.visibility == "hidden" and row.created_by != current_user:
            return JsonResponse({"status": False, "message": "not found"}, status=404)
        if row.visibility == "restricted":
            permitted = json.loads(row.permitted_users or "[]")
            if row.created_by != current_user and current_user not in permitted:
                return JsonResponse({"status": False, "message": "not found"}, status=404)

        return JsonResponse({"status": True, "definition": serialize_fn(row)})

    elif request.method == "DELETE":
        try:
            row = Model.objects.get(id=case_id)
        except Model.DoesNotExist:
            return JsonResponse({"status": False, "message": "not found"}, status=404)

        current_user = resolve_username(getattr(request, "user_id", None))
        if row.visibility == "hidden" and row.created_by != current_user:
            return JsonResponse({"status": False, "message": "not found"}, status=404)
        if row.locked and row.created_by != current_user:
            return JsonResponse({"status": False, "message": "用例已被所有者锁定"}, status=403)
        if row.visibility == "restricted":
            permitted = json.loads(row.permitted_users or "[]")
            if current_user not in permitted:
                return JsonResponse({"status": False, "message": "Forbidden"}, status=403)

        delete_case(case_id)
        return JsonResponse({"status": True})

    return JsonResponse({"status": False, "message": "method not allowed"}, status=405)


# ═══════════════════════════════════════════════════════════════
# Batch — shared JSON parse + validation + delegate to api layer
# ═══════════════════════════════════════════════════════════════


def handle_batch_definitions(request, batch_save_fn, normalize_fn=None):
    """POST /api/cases/{type}/definitions/batch — shared preamble + normalize + save."""
    if request.method != "POST":
        return JsonResponse({"status": False, "message": "method not allowed"}, status=405)
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"status": False, "message": "无效的 JSON"}, status=400)

    cases = data.get("cases", [])
    if not isinstance(cases, list) or not cases:
        return JsonResponse({"status": False, "message": "cases 必须是非空数组"}, status=400)
    if len(cases) > BATCH_IMPORT_LIMIT:
        return JsonResponse(
            {"status": False, "message": f"单次批量导入最多 {BATCH_IMPORT_LIMIT} 条用例"},
            status=400,
        )

    overwrite = data.get("overwrite", False)
    directory_id = data.get("directory_id")

    normalized = normalize_fn(cases, directory_id) if normalize_fn else cases
    result = batch_save_fn(normalized, overwrite=overwrite)
    return JsonResponse({"status": True, **result})
