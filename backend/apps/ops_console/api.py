"""运营后台的编排与边界校验。

业务：
1. list_users: 分页列出账号，带身份标签与启用状态。
2. set_active: 停用或启用一个普通账号，写库经 `accounts.api`。
2b. disable_users: 本页批量停用，不可管理的行逐行拒绝，不拖垮整批。
2c. purge_users: 仅超管批量注销，只删账号，任一行不可注销则整批不删。
3. reset_password: 为普通账号生成一次性临时密码并落库，写库经 `accounts.api`。
4. check_manageable: 判定操作者能否管理目标账号，不能则抛 PermissionError。

边界：不能操作自己、不能操作超级管理员、非超管不能操作其他运营。
注销仅超管，且只删账号行，不删业务表。
"""

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
]

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 100

# 临时密码字符集：剔除 0/O/1/l/I 等易混字符，避免运营抄错转述错。
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
    """分页列出账号。

    Args:
        page: 页码，从 1 开始；小于 1 按 1 处理。
        page_size: 每页条数，夹紧到 1..MAX_PAGE_SIZE。
        keyword: 用户名或邮箱的模糊匹配；空串表示不筛选。
        active: True 只看启用、False 只看停用、None 不筛。

    Returns:
        含 users / total / page / page_size 的字典。
    """
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


def set_active(actor_id: int, target_id: int, active: bool) -> dict:
    """停用或启用目标账号，成功后记一条运营日志。

    Args:
        actor_id: 发起操作的账号主键。
        target_id: 目标账号主键。
        active: True 启用、False 停用。

    Returns:
        含 target 最新一行的字典：`{"user": {...}}`。

    Raises:
        LookupError: 目标账号不存在。
        PermissionError: 目标不可被当前操作者管理。
    """
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
    """批量停用。可停用的落库，不可管理的逐行拒绝，已停用的跳过。

    Args:
        actor_id: 发起操作的账号主键。
        user_ids: 已去重的目标主键。

    Returns:
        含逐行结果与计数的字典。

    Raises:
        无。不存在的主键记为 rejected，不中断整批。
    """
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
    """批量注销。仅超管；任一目标不可注销则整批不删。

    Args:
        actor_id: 发起操作的账号主键。
        user_ids: 已去重的目标主键。

    Returns:
        含已删除主键的字典。

    Raises:
        PermissionError: 操作者不是超管，或名单含自己、超管、运营、不存在的账号。
    """
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
    """为目标账号生成一次性临时密码并落库。

    明文只出现在本次返回值里，日志与数据库都不留。

    Args:
        actor_id: 发起操作的账号主键。
        target_id: 目标账号主键。

    Returns:
        含 `username` 与一次性 `password` 的字典。

    Raises:
        LookupError: 目标账号不存在。
        PermissionError: 目标不可被当前操作者管理。
    """
    target = _get_target(target_id)
    check_manageable(actor_id, target)
    password = _generate_password()
    user = set_user_password(target.id, password)
    backend_log.info("ops actor=%s action=reset-password target=%s result=ok", actor_id, target.id)
    return {"username": user.username, "password": password}


def grant_operator(actor_id: int, target_id: int) -> dict:
    """把普通用户设为运营。仅超级管理员可调用。

    Args:
        actor_id: 发起操作的账号主键。
        target_id: 目标账号主键。

    Returns:
        含目标最新一行的字典。

    Raises:
        LookupError: 目标账号不存在。
        PermissionError: 操作者不是超管，或目标是自己、是超管。
    """
    return _set_operator(actor_id, target_id, enabled=True)


def revoke_operator(actor_id: int, target_id: int) -> dict:
    """把运营恢复为普通用户。仅超级管理员可调用。

    Args:
        actor_id: 发起操作的账号主键。
        target_id: 目标账号主键。

    Returns:
        含目标最新一行的字典。

    Raises:
        LookupError: 目标账号不存在。
        PermissionError: 操作者不是超管，或目标是自己、是超管。
    """
    return _set_operator(actor_id, target_id, enabled=False)


def _set_operator(actor_id: int, target_id: int, *, enabled: bool) -> dict:
    """授予与取消共用：校验超管边界后调账号写口。

    Args:
        actor_id: 发起操作的账号主键。
        target_id: 目标账号主键。
        enabled: True 授予、False 取消。

    Returns:
        含目标最新一行的字典。

    Raises:
        LookupError: 目标账号不存在。
        PermissionError: 操作者不是超管，或目标不可被授予。
    """
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
    """判定操作者能否授予或取消目标的运营身份。

    只有超管能授权；谁都不能授给自己，也不能授给超管（超管不靠用户组判定）。

    Args:
        actor_id: 发起操作的账号主键。
        target: 目标账号实例。

    Returns:
        None：通过校验。

    Raises:
        PermissionError: 操作者不是超管，或目标是自己、是超管。
    """
    if not is_superuser(actor_id):
        raise PermissionError("仅超级管理员可授予或取消运营")
    if int(target.id) == _safe_int(actor_id):
        raise PermissionError("不能操作自己的账号")
    if target.is_superuser:
        raise PermissionError("不能对超级管理员授予运营")


def check_manageable(actor_id: int, target) -> None:
    """判定操作者能否停用或重置目标账号。

    规则：超级管理员与运营都不能被停用或重置，谁来操作都一样。
    普通用户可以被运营或超管管理，但不能管理自己。

    Args:
        actor_id: 发起操作的账号主键。
        target: 目标账号实例。

    Returns:
        None：通过校验。

    Raises:
        PermissionError: 目标是自己、是超级管理员，或是运营。
    """
    if int(target.id) == _safe_int(actor_id):
        raise PermissionError("不能操作自己的账号")
    if target.is_superuser:
        raise PermissionError("不能停用超级管理员")
    if _is_operator_user(target):
        raise PermissionError("不能停用运营账号")


def _is_operator_user(user) -> bool:
    """判定账号是否属于运营组（单账号查询，列表场景请用 operator_ids 集合）。

    Args:
        user: 账号实例。

    Returns:
        属于运营组返回 True。
    """
    return user.groups.filter(name=OPERATOR_GROUP).exists()


def _get_target(user_id: int):
    """按主键取目标账号。

    Args:
        user_id: 目标账号主键。

    Returns:
        账号实例。

    Raises:
        LookupError: 主键非法或账号不存在。
    """
    pk = _safe_int(user_id)
    target = get_user_model().objects.filter(pk=pk).first() if pk else None
    if target is None:
        raise LookupError("账号不存在")
    return target


def _serialize_rows(rows) -> list[dict]:
    """把账号查询结果序列化成行列表（运营主键集合只查一次）。

    Args:
        rows: 账号查询集或列表。

    Returns:
        行字典列表。
    """
    return OpsUserRowSerializer(rows, many=True, context=_row_context()).data


def _row_context() -> dict:
    """构造序列化上下文：一次查出运营账号主键集合，避免逐行查组关系。

    Returns:
        含 operator_ids 的上下文字典。
    """
    operator_ids = set(
        get_user_model().objects.filter(groups__name=OPERATOR_GROUP).values_list("id", flat=True)
    )
    return {"operator_ids": operator_ids}


def _generate_password() -> str:
    """生成一次性临时密码。

    Returns:
        16 位随机密码。
    """
    return "".join(secrets.choice(_PASSWORD_ALPHABET) for _ in range(_PASSWORD_LENGTH))


def _safe_int(value) -> int:
    """把入参转成主键；非法值返回 0。

    Args:
        value: 任意入参。

    Returns:
        正整数主键或 0。
    """
    try:
        return int(str(value))
    except (TypeError, ValueError):
        return 0
