"""case-manager HTTP routes — 12 endpoints under /api/cases/*."""

import json
from datetime import datetime
from django.http import JsonResponse, FileResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

from apps.element_locator.api import simple_yaml_dump
from apps.element_locator.models import Element, PageFlow
from .models import TestDefinition, CaseDirectory
from .api import get_directory_tree, create_directory, update_directory, delete_directory, batch_move_items, _parse_datetime


def _resolve_username(user_id):
    """Convert Django user ID to username string. Already-usernames pass through."""
    if not user_id:
        return ""
    s = str(user_id)
    # Already a non-numeric username → return as-is
    if not s.isdigit():
        return s
    # Numeric ID → resolve to username from User model
    try:
        from django.contrib.auth.models import User
        return User.objects.get(id=int(s)).username
    except Exception:
        return s


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
        created_by=_resolve_username(getattr(request, 'user_id', None)),
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
            ok, result = delete_directory(dir_id, deleted_by=_resolve_username(getattr(request, 'user_id', None)))
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

        # Visibility filter: hide non-public cases from unauthorized users
        current_user = _resolve_username(getattr(request, 'user_id', None))
        from django.db.models import Q
        # Build permitted_users filter with exact JSON match (not icontains)
        restricted_q = Q(visibility="public") | Q(created_by=current_user)
        if current_user:
            # Exact username match inside JSON array: "[\"user1\",\"user2\"]" contains "\"username\""
            restricted_q |= Q(visibility="restricted") & Q(permitted_users__icontains=f'"{current_user}"')
        qs = qs.filter(restricted_q)

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

        # ── User tracking ──
        current_user = _resolve_username(getattr(request, 'user_id', None))
        is_new_case = not TestDefinition.objects.filter(id=case_id).exists()

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
            "visibility": data.get("visibility", "public"),
            "permitted_users": json.dumps(data.get("permitted_users", []), ensure_ascii=False),
            "permission": data.get("permission", "edit"),
            "permitted_editors": json.dumps(data.get("permitted_editors", []), ensure_ascii=False),
        }

        # Track user: set created_by on first save, always set updated_by
        if is_new_case and current_user:
            defaults["created_by"] = current_user
        if current_user:
            defaults["updated_by"] = current_user

        # Check for duplicate title in the same directory
        title = defaults["title"]
        title = defaults["title"]
        existing = TestDefinition.objects.filter(
            directory=directory, title=title
        ).exclude(id=case_id).first()
        if existing:
            dir_name = directory.name if directory else "根级（未分类）"
            return JsonResponse({
                "ok": False,
                "error": f"目录「{dir_name}」下已存在同名用例「{title}」（ID: {existing.id}）",
            }, status=409)

        # Optimistic lock: prevent lost updates
        client_updated_at = data.get("updated_at")
        if case_id and client_updated_at:
            current = TestDefinition.objects.filter(id=case_id).only("id", "updated_at").first()
            if current and current.updated_at:
                client_ts = _parse_datetime(client_updated_at)
                db_ts = current.updated_at.replace(microsecond=0)
                if client_ts and client_ts != db_ts:
                    return JsonResponse({
                        "ok": False,
                        "error": f"用例「{title or case_id}」已被他人修改，请刷新后重试",
                    }, status=409)

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

        # Visibility check: hide non-public cases from unauthorized users
        current_user = _resolve_username(getattr(request, 'user_id', None))
        if row.visibility == "hidden" and row.created_by != current_user:
            return JsonResponse({"ok": False, "error": "not found"}, status=404)
        if row.visibility == "restricted":
            permitted = json.loads(row.permitted_users or "[]")
            if row.created_by != current_user and current_user not in permitted:
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


# ═══════════════════════════════════════════════
# 编辑锁（per-case edit locking）
# ═══════════════════════════════════════════════

EDIT_LOCK_TIMEOUT_SECONDS = 1800  # 30 min — release if user is idle


@csrf_exempt
def acquire_edit_lock(request, case_id):
    """POST /api/cases/definitions/{case_id}/lock — 获取用例编辑锁。

    成功 → 200 {ok, editing_by, editing_since}
    已被他人锁定 → 423 Locked {ok, error, editing_by, editing_since}
    用例不存在 → 404
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    current_user = _resolve_username(getattr(request, 'user_id', None))
    if not current_user:
        return JsonResponse({"ok": False, "error": "未登录"}, status=401)

    try:
        case = TestDefinition.objects.only("id", "created_by", "editing_by", "editing_since", "permission", "permitted_editors").get(id=case_id)
    except TestDefinition.DoesNotExist:
        return JsonResponse({"ok": False, "error": "用例不存在"}, status=404)

    now = datetime.now()

    # Permission check: deny non-authorized users
    if case.created_by != current_user:
        if case.permission == "readonly":
            return JsonResponse({"ok": False, "error": "此用例为只读模式，仅创建者可编辑"}, status=423)
        if case.permission == "restricted":
            editors = json.loads(case.permitted_editors or "[]")
            if current_user not in editors:
                return JsonResponse({"ok": False, "error": f"此用例仅限指定用户编辑"}, status=423)

    # Already locked by someone else?
    if case.editing_by and case.editing_by != current_user:
        if case.editing_since:
            elapsed = (now - case.editing_since).total_seconds()
            if elapsed < EDIT_LOCK_TIMEOUT_SECONDS:
                return JsonResponse({
                    "ok": False,
                    "error": f"用例正被 {case.editing_by} 编辑中",
                    "editing_by": case.editing_by,
                    "editing_since": str(case.editing_since),
                }, status=423)
            # Lock expired → fall through and take over
        # Lock expired or no timestamp → take over

    # Acquire or refresh lock
    case.editing_by = current_user
    case.editing_since = now
    case.save(update_fields=["editing_by", "editing_since"])

    return JsonResponse({
        "ok": True,
        "editing_by": current_user,
        "editing_since": now.isoformat(),
        "created_by": case.created_by,
    })


@csrf_exempt
def release_edit_lock(request, case_id):
    """POST /api/cases/definitions/{case_id}/unlock — 释放编辑锁。

    force=true 时：创建者可以强制踢出其他编辑者。
    """
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    current_user = _resolve_username(getattr(request, 'user_id', None))
    if not current_user:
        return JsonResponse({"ok": False, "error": "未登录"}, status=401)

    try:
        case = TestDefinition.objects.only("id", "editing_by", "editing_since", "created_by").get(id=case_id)
    except TestDefinition.DoesNotExist:
        return JsonResponse({"ok": False, "error": "用例不存在"}, status=404)

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    force = body.get("force", False)

    # Force unlock: only creator can do it
    if force:
        if case.created_by and case.created_by != current_user:
            return JsonResponse({
                "ok": False,
                "error": "只有用例创建者可以强制解除编辑锁",
            }, status=403)
        # Creator force-unlock: clear the lock
        case.editing_by = ""
        case.editing_since = None
        case.save(update_fields=["editing_by", "editing_since"])
        return JsonResponse({"ok": True, "force_unlocked": True})

    # Normal unlock: only the lock holder or creator can release
    if case.editing_by and case.editing_by != current_user and case.created_by != current_user:
        return JsonResponse({
            "ok": False,
            "error": "只有编辑者或创建者可以释放编辑锁",
        }, status=403)

    if not case.editing_by:
        return JsonResponse({"ok": True, "already_unlocked": True})

    case.editing_by = ""
    case.editing_since = None
    case.save(update_fields=["editing_by", "editing_since"])
    return JsonResponse({"ok": True, "released": True})


# ═══════════════════════════════════════════════
# 用例持久锁（创建者控制，锁定后他人只读）
# ═══════════════════════════════════════════════

@csrf_exempt
def case_lock(request, case_id):
    """POST /api/cases/definitions/{case_id}/case-lock — 创建者锁定用例（他人只读）。"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    current_user = _resolve_username(getattr(request, 'user_id', None))
    if not current_user:
        return JsonResponse({"ok": False, "error": "未登录"}, status=401)

    try:
        case = TestDefinition.objects.only("id", "created_by", "locked").get(id=case_id)
    except TestDefinition.DoesNotExist:
        return JsonResponse({"ok": False, "error": "用例不存在"}, status=404)

    if case.created_by and case.created_by != current_user:
        return JsonResponse({"ok": False, "error": "只有创建者可以锁定用例"}, status=403)

    case.locked = True
    case.save(update_fields=["locked"])
    return JsonResponse({"ok": True, "locked": True})


@csrf_exempt
def case_unlock(request, case_id):
    """POST /api/cases/definitions/{case_id}/case-unlock — 创建者解除用例锁。"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    current_user = _resolve_username(getattr(request, 'user_id', None))
    if not current_user:
        return JsonResponse({"ok": False, "error": "未登录"}, status=401)

    try:
        case = TestDefinition.objects.only("id", "created_by", "locked").get(id=case_id)
    except TestDefinition.DoesNotExist:
        return JsonResponse({"ok": False, "error": "用例不存在"}, status=404)

    if case.created_by and case.created_by != current_user:
        return JsonResponse({"ok": False, "error": "只有创建者可以解除锁定"}, status=403)

    if not case.locked:
        return JsonResponse({"ok": True, "already_unlocked": True})

    case.locked = False
    case.save(update_fields=["locked"])
    return JsonResponse({"ok": True, "unlocked": True})


# ═══════════════════════════════════════════════
# 用例可见性
# ═══════════════════════════════════════════════

@csrf_exempt
def set_visibility(request, case_id):
    """POST /api/cases/definitions/{case_id}/visibility — 更新可见性（仅创建者）。"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    current_user = _resolve_username(getattr(request, 'user_id', None))
    if not current_user:
        return JsonResponse({"ok": False, "error": "未登录"}, status=401)

    try:
        case = TestDefinition.objects.only("id", "created_by", "visibility", "permitted_users").get(id=case_id)
    except TestDefinition.DoesNotExist:
        return JsonResponse({"ok": False, "error": "用例不存在"}, status=404)

    if case.created_by and case.created_by != current_user:
        return JsonResponse({"ok": False, "error": "只有创建者可以修改可见性"}, status=403)

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    case.visibility = body.get("visibility", "public")
    case.permitted_users = json.dumps(body.get("permitted_users", []), ensure_ascii=False)
    case.save(update_fields=["visibility", "permitted_users"])
    return JsonResponse({"ok": True, "visibility": case.visibility})


# ═══════════════════════════════════════════════
# 目录权限
# ═══════════════════════════════════════════════

@csrf_exempt
def directory_permission(request, dir_id):
    """POST /api/cases/directories/{dir_id}/permission — 更新目录权限（仅创建者）。"""
    if request.method != "POST":
        return JsonResponse({"ok": False, "error": "method not allowed"}, status=405)

    current_user = _resolve_username(getattr(request, 'user_id', None))
    if not current_user:
        return JsonResponse({"ok": False, "error": "未登录"}, status=401)

    try:
        d = CaseDirectory.objects.only("id", "created_by").get(id=dir_id)
    except CaseDirectory.DoesNotExist:
        return JsonResponse({"ok": False, "error": "目录不存在"}, status=404)

    if d.created_by and d.created_by != current_user:
        return JsonResponse({"ok": False, "error": "只有目录创建者可以修改权限"}, status=403)

    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        body = {}

    d.allow_create = body.get("allow_create", True)
    d.allow_delete = body.get("allow_delete", False)
    d.save(update_fields=["allow_create", "allow_delete"])
    return JsonResponse({"ok": True})


def download_export(request, filename):
    """GET /api/cases/exports/{filename} — Download YAML export."""
    fp = settings.EXPORT_DIR / filename
    if fp.exists():
        return FileResponse(fp, content_type="application/x-yaml", filename=filename)
    return JsonResponse({"ok": False, "error": "not found"}, status=404)
