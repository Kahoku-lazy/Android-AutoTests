from __future__ import annotations

import secrets

from django.contrib.auth import get_user_model
from django.db.models import Q

from backend.apps.accounts.api import (
    purge_users as purge_account_users,
)
from backend.apps.accounts.api import (
    set_operator,
    set_user_active,
    set_user_password,
)
from backend.apps.ai_assistant.api import (
    grant_assistant_author,
    grant_model_use,
    revoke_assistant_author,
    revoke_model_use,
)
from backend.shared.users import OPERATOR_GROUP, is_superuser
from utils.logs import backend_log

from .serializers import OpsUserRowSerializer

__all__ = [
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "check_manageable",
    "disable_users",
    "grant_operator",
    "list_users",
    "purge_users",
    "reset_password",
    "revoke_operator",
    "set_active",
    "set_assistant_author",
    "set_model_use",
]

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

_PASSWORD_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789"
_PASSWORD_LENGTH = 16

IDENTITY_LABELS = {"superuser": "超级管理员", "operator": "运营", "user": "普通用户"}


def list_users(
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    keyword: str = "",
    active: bool | None = None,
) -> dict:
    user_model = get_user_model()
    queryset = user_model.objects.all()

    text = (keyword or "").strip()
    if text:
        queryset = queryset.filter(Q(username__icontains=text) | Q(email__icontains=text))
    if active is not None:
        queryset = queryset.filter(is_active=bool(active))

    total = queryset.count()
    safe_page = max(int(page or 1), 1)
    safe_size = min(max(int(page_size or DEFAULT_PAGE_SIZE), 1), MAX_PAGE_SIZE)
    start = (safe_page - 1) * safe_size
    rows = queryset.order_by("-date_joined", "-id")[start : start + safe_size]

    return {
        "users": _serialize_rows(rows),
        "total": total,
        "page": safe_page,
        "page_size": safe_size,
    }


def set_model_use(actor_id: int, target_id: int, model_config_id: int, enabled: bool) -> dict:
    if not is_superuser(actor_id):
        raise PermissionError("只有超级管理员可以修改模型名单")
    user = get_user_model().objects.filter(pk=target_id).first()
    if user is None:
        raise LookupError("账号不存在")
    if enabled:
        grant_model_use(user.id, int(model_config_id))
    else:
        revoke_model_use(user.id, int(model_config_id))
    return {
        "user_id": user.id,
        "model_config_id": int(model_config_id),
        "enabled": bool(enabled),
    }


def set_assistant_author(actor_id: int, target_id: int, enabled: bool) -> dict:
    if not is_superuser(actor_id):
        raise PermissionError("只有超级管理员可以授予助手作者")
    if int(actor_id) == int(target_id):
        raise PermissionError("不能授予自己")
    user = get_user_model().objects.filter(pk=target_id).first()
    if user is None:
        raise LookupError("账号不存在")
    if enabled:
        grant_assistant_author(user.id)
    else:
        revoke_assistant_author(user.id)
    return {"user_id": user.id, "is_assistant_author": bool(enabled)}


def set_active(actor_id: int, target_id: int, active: bool) -> dict:
    target = _get_target(target_id)
    check_manageable(actor_id, target)
    user = set_user_active(target.id, active)
    backend_log.info(
        "ops actor=%s action=%s target=%s result=ok",
        actor_id,
        "enable" if active else "disable",
        target.id,
    )
    return {"user": OpsUserRowSerializer(user, context=_row_context()).data}


def disable_users(actor_id: int, user_ids: list[int]) -> dict:
    rows = []
    counts = {"disabled": 0, "skipped": 0, "rejected": 0}
    for target_id in user_ids:
        target = get_user_model().objects.filter(pk=target_id).first()
        if target is None:
            rows.append({"user_id": target_id, "outcome": "rejected", "reason": "账号不存在"})
            counts["rejected"] += 1
            continue
        try:
            check_manageable(actor_id, target)
        except PermissionError as exc:
            rows.append({"user_id": target.id, "outcome": "rejected", "reason": str(exc)})
            counts["rejected"] += 1
            continue
        if not target.is_active:
            rows.append({"user_id": target.id, "outcome": "skipped", "reason": "已停用"})
            counts["skipped"] += 1
            continue
        set_user_active(target.id, False)
        rows.append({"user_id": target.id, "outcome": "disabled", "reason": ""})
        counts["disabled"] += 1
        backend_log.info("ops actor=%s action=disable target=%s result=ok", actor_id, target.id)
    return {"results": rows, "counts": counts}


def purge_users(actor_id: int, user_ids: list[int]) -> dict:
    if not is_superuser(actor_id):
        raise PermissionError("仅超级管理员可注销账号")
    user_model = get_user_model()
    targets = list(user_model.objects.filter(pk__in=user_ids))
    found = {item.id for item in targets}
    if found != set(user_ids):
        raise PermissionError("名单含不存在的账号，已整批取消")
    actor = _safe_int(actor_id)
    for target in targets:
        if int(target.id) == actor:
            raise PermissionError("不能注销自己的账号")
        if target.is_superuser:
            raise PermissionError("不能注销超级管理员")
        if _is_operator_user(target):
            raise PermissionError("不能注销运营账号")
    deleted = purge_account_users(user_ids)
    for target_id in deleted:
        backend_log.info("ops actor=%s action=purge target=%s result=ok", actor_id, target_id)
    return {"deleted": deleted}


def reset_password(actor_id: int, target_id: int) -> dict:
    target = _get_target(target_id)
    check_manageable(actor_id, target)
    password = _generate_password()
    user = set_user_password(target.id, password)
    backend_log.info("ops actor=%s action=reset-password target=%s result=ok", actor_id, target.id)
    return {"username": user.username, "password": password}


def grant_operator(actor_id: int, target_id: int) -> dict:
    return _set_operator(actor_id, target_id, enabled=True)


def revoke_operator(actor_id: int, target_id: int) -> dict:
    return _set_operator(actor_id, target_id, enabled=False)


def _set_operator(actor_id: int, target_id: int, *, enabled: bool) -> dict:
    target = _get_target(target_id)
    _check_grantable(actor_id, target)
    user = set_operator(target.id, enabled)
    backend_log.info(
        "ops actor=%s action=%s target=%s result=ok",
        actor_id,
        "grant-operator" if enabled else "revoke-operator",
        target.id,
    )
    return {"user": OpsUserRowSerializer(user, context=_row_context()).data}


def _check_grantable(actor_id: int, target) -> None:
    if not is_superuser(actor_id):
        raise PermissionError("仅超级管理员可授予或取消运营")
    if int(target.id) == _safe_int(actor_id):
        raise PermissionError("不能操作自己的账号")
    if target.is_superuser:
        raise PermissionError("不能对超级管理员授予运营")


def check_manageable(actor_id: int, target) -> None:
    if int(target.id) == _safe_int(actor_id):
        raise PermissionError("不能操作自己的账号")
    if target.is_superuser:
        raise PermissionError("不能停用超级管理员")
    if _is_operator_user(target):
        raise PermissionError("不能停用运营账号")


def _is_operator_user(user) -> bool:
    return user.groups.filter(name=OPERATOR_GROUP).exists()


def _get_target(user_id: int):
    pk = _safe_int(user_id)
    target = get_user_model().objects.filter(pk=pk).first() if pk else None
    if target is None:
        raise LookupError("账号不存在")
    return target


def _serialize_rows(rows) -> list[dict]:
    return OpsUserRowSerializer(rows, many=True, context=_row_context()).data


def _row_context() -> dict:
    operator_ids = set(
        get_user_model().objects.filter(groups__name=OPERATOR_GROUP).values_list("id", flat=True)
    )
    return {"operator_ids": operator_ids}


def _generate_password() -> str:
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(_PASSWORD_LENGTH))


def _safe_int(value) -> int:
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0
