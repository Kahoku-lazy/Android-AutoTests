"""case-manager lock & visibility helpers — generalized across all case types.

写操作铁律：views 调用本模块写函数写 DB，禁止直接 ORM 写。
"""

__all__ = [
    "find_case_across_types",
    "get_case_for_lock",
    "delete_case",
    "acquire_edit_lock",
    "release_edit_lock",
    "set_case_lock",
    "set_case_visibility",
]

import json

from datetime import datetime

from .models import TestDefinition
from .models_api import ApiTestCase
from .models_storage import StorageTestCase
from .models_web import WebTestCase

_ALL_CASE_MODELS = (TestDefinition, StorageTestCase, ApiTestCase, WebTestCase)

EDIT_LOCK_TIMEOUT_SECONDS = 1800  # 30 min — release if user is idle


def find_case_across_types(case_id):
    """Look up a case ID across all three test case tables.

    Returns (model_instance, model_class) or (None, None).
    """
    for model in _ALL_CASE_MODELS:
        try:
            return model.objects.get(id=case_id), model
        except model.DoesNotExist:
            continue
    return None, None


def get_case_for_lock(case_id):
    """Fetch a case for lock operations — returns minimal fields needed by lock views.

    Returns the model instance (with .only() for efficiency) or None.
    """
    for model in _ALL_CASE_MODELS:
        try:
            return model.objects.only(
                "id",
                "created_by",
                "editing_by",
                "editing_since",
                "permission",
                "permitted_editors",
                "locked",
                "visibility",
                "permitted_users",
            ).get(id=case_id)
        except model.DoesNotExist:
            continue
    return None


def delete_case(case_id):
    """删除用例（跨 4 个 case model）。返回是否删除成功。"""
    case, _ = find_case_across_types(case_id)
    if case is None:
        return False
    case.delete()
    return True


def acquire_edit_lock(case_id, user, force=False):
    """获取用例编辑锁。返回 (ok, data_or_error_dict)。

    force=True 时强制接管他人持有的锁（跳过编辑锁冲突检查）。
    error_dict 含 "code"（HTTP 状态码）和 "message"（中文错误）。
    """
    case = get_case_for_lock(case_id)
    if case is None:
        return False, {"code": 404, "message": "用例不存在"}

    now = datetime.now()

    if case.created_by != user:
        if case.permission == "readonly":
            return False, {"code": 423, "message": "此用例为只读模式，仅创建者可编辑"}
        if case.permission == "restricted":
            editors = json.loads(case.permitted_editors or "[]")
            if user not in editors:
                return False, {"code": 423, "message": "此用例仅限指定用户编辑"}

    if case.locked and case.created_by and case.created_by != user:
        return False, {"code": 423, "message": "用例已被所有者锁定"}

    if case.editing_by and case.editing_by != user and not force:
        if case.editing_since:
            elapsed = (now - case.editing_since).total_seconds()
            if elapsed < EDIT_LOCK_TIMEOUT_SECONDS:
                return False, {
                    "code": 423,
                    "message": f"用例正被 {case.editing_by} 编辑中",
                    "editing_by": case.editing_by,
                    "editing_since": str(case.editing_since),
                }

    case.editing_by = user
    case.editing_since = now
    case.save(update_fields=["editing_by", "editing_since"])
    return True, {
        "editing_by": user,
        "editing_since": now.isoformat(),
        "created_by": case.created_by,
    }


def release_edit_lock(case_id, user, force=False):
    """释放编辑锁。force=True 时创建者可强制踢出。返回 (ok, data_or_error_dict)。"""
    case = get_case_for_lock(case_id)
    if case is None:
        return False, {"code": 404, "message": "用例不存在"}

    if force:
        if case.created_by and case.created_by != user:
            return False, {"code": 403, "message": "只有用例创建者可以强制解除编辑锁"}
        case.editing_by = ""
        case.editing_since = None
        case.save(update_fields=["editing_by", "editing_since"])
        return True, {"force_unlocked": True}

    if case.editing_by and case.editing_by != user and case.created_by != user:
        return False, {"code": 403, "message": "只有编辑者或创建者可以释放编辑锁"}

    if not case.editing_by:
        return True, {"already_unlocked": True}

    case.editing_by = ""
    case.editing_since = None
    case.save(update_fields=["editing_by", "editing_since"])
    return True, {"released": True}


def set_case_lock(case_id, user, locked):
    """硬锁（locked=True）或解除硬锁（locked=False），仅创建者。返回 (ok, data_or_error_dict)。"""
    case = get_case_for_lock(case_id)
    if case is None:
        return False, {"code": 404, "message": "用例不存在"}

    if case.created_by and case.created_by != user:
        verb = "锁定" if locked else "解除锁定"
        return False, {"code": 403, "message": f"只有创建者可以{verb}用例"}

    if bool(case.locked) == locked:
        return True, {"already_locked" if locked else "already_unlocked": True}

    case.locked = locked
    case.save(update_fields=["locked"])
    return True, {"locked": locked}


def set_case_visibility(
    case_id,
    user,
    visibility,
    permitted_users=None,
    permitted_editors=None,
    permission=None,
):
    """更新可见性（仅创建者）。返回 (ok, data_or_error_dict)。"""
    case = get_case_for_lock(case_id)
    if case is None:
        return False, {"code": 404, "message": "用例不存在"}

    if case.created_by and case.created_by != user:
        return False, {"code": 403, "message": "只有创建者可以修改可见性"}

    if visibility not in ("public", "hidden", "restricted"):
        return False, {"code": 400, "message": "无效的可见性值，可选: public / hidden / restricted"}

    update_fields = ["visibility"]
    case.visibility = visibility
    if permitted_users is not None:
        case.permitted_users = (
            json.dumps(permitted_users, ensure_ascii=False)
            if isinstance(permitted_users, (list, dict))
            else permitted_users
        )
        update_fields.append("permitted_users")
    if permitted_editors is not None:
        case.permitted_editors = (
            json.dumps(permitted_editors, ensure_ascii=False)
            if isinstance(permitted_editors, (list, dict))
            else permitted_editors
        )
        update_fields.append("permitted_editors")
    if permission is not None:
        case.permission = permission
        update_fields.append("permission")
    case.save(update_fields=update_fields)
    return True, {"visibility": case.visibility}
