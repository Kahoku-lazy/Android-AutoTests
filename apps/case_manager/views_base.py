"""case-manager shared view handlers — eliminate duplicated CRUD across UI/Web/Storage/API views.

Each of the 4 views files (views_ui/web/storage/api) delegates its GET/POST/DELETE/Batch
to the helper functions below, keeping only type-specific serialization and field extraction.
"""

import json
import logging

from django.db.models import Q
from django.http import JsonResponse

from .api_lock import delete_case
from .api_ui import _parse_datetime
from .models import CaseDirectory
from .views_helpers import resolve_username

logger = logging.getLogger(__name__)
BATCH_IMPORT_LIMIT = 500


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


def resolve_directory(data, case_type_label):
    """Resolve directory_id from POST data to a CaseDirectory instance or None."""
    directory_id = data.get("directory_id")
    if directory_id is not None:
        try:
            return CaseDirectory.objects.get(id=directory_id)
        except CaseDirectory.DoesNotExist:
            logger.warning(
                "Directory %s not found (case_type=%s), saving without directory",
                directory_id,
                case_type_label,
            )
    return None


def assign_user_fields(defaults, is_new_case, current_user):
    """Set created_by (new only) and updated_by (always) on the defaults dict."""
    if is_new_case and current_user:
        defaults["created_by"] = current_user
    if current_user:
        defaults["updated_by"] = current_user


def check_duplicate_title(Model, directory, title, case_id, error_label):
    """Return JsonResponse(409) if duplicate exists, or None."""
    existing = Model.objects.filter(directory=directory, title=title).exclude(id=case_id).first()
    if existing:
        dir_name = directory.name if directory else "根级（未分类）"
        return JsonResponse(
            {
                "status": False,
                "message": f"目录「{dir_name}」下已存在同名{error_label}「{title}」（ID: {existing.id}）",
            },
            status=409,
        )
    return None


def check_optimistic_lock(Model, case_id, client_updated_at, title, error_label):
    """Return JsonResponse(409) on version conflict, or None."""
    if not case_id or not client_updated_at:
        return None
    current = Model.objects.filter(id=case_id).only("id", "updated_at").first()
    if current and current.updated_at:
        client_ts = _parse_datetime(client_updated_at)
        db_ts = current.updated_at.replace(microsecond=0)
        if client_ts and client_ts != db_ts:
            return JsonResponse(
                {
                    "status": False,
                    "message": f"{error_label}「{title or case_id}」已被他人修改，请刷新后重试",
                },
                status=409,
            )
    return None


def do_update_or_create(Model, case_id, defaults):
    """Perform update_or_create and return (ok, id, updated_at_str) dict."""
    Model.objects.update_or_create(id=case_id, defaults=defaults)
    updated = Model.objects.filter(id=case_id).only("id", "updated_at", "title").first()
    resp = {"status": True, "id": case_id}
    if updated and updated.updated_at:
        resp["updated_at"] = updated.updated_at.strftime("%Y-%m-%d %H:%M:%S")
    return resp


def handle_post_definition(request, case_id, Model, case_type, error_label, defaults):
    """POST /api/cases/{type}/definitions — shared create/update logic.

    Args:
        request: Django request object.
        case_id: the case ID string (may be new auto-generated ID).
        Model: the ORM model class for this case type.
        case_type: "ui_automation" / "web_automation" / "storage" / "api_testing".
        error_label: "用例" / "Web 用例" / "存储用例" / "API 用例".
        defaults: dict of all model fields to save. May contain magic keys:
            _directory_id: resolved to a CaseDirectory instance.
            _client_updated_at: used for optimistic lock check.
    """
    # Resolve directory
    directory_id = defaults.pop("_directory_id", None)
    directory = None
    if directory_id is not None:
        try:
            directory = CaseDirectory.objects.get(id=directory_id)
        except CaseDirectory.DoesNotExist:
            logger.warning(
                "Directory %s not found (case_type=%s), saving without directory",
                directory_id,
                case_type,
            )
    defaults["directory"] = directory

    current_user = resolve_username(getattr(request, "user_id", None))
    is_new_case = not Model.objects.filter(id=case_id).exists()

    assign_user_fields(defaults, is_new_case, current_user)

    # Duplicate title check
    title = defaults.get("title", "")
    err = check_duplicate_title(Model, directory, title, case_id, error_label)
    if err:
        return err

    # Optimistic lock
    client_updated_at = defaults.pop("_client_updated_at", None)
    err = check_optimistic_lock(Model, case_id, client_updated_at, title, error_label)
    if err:
        return err

    resp = do_update_or_create(Model, case_id, defaults)
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
