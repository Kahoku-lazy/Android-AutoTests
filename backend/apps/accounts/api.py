"""
账号写入与登出吊销。

业务：
1. 创建平台用户，并返回账号编号、用户名和邮箱。
2. 用户名已存在时拒绝创建。
3. 记录吊销（会话级 sid / 单令牌级 jti），供登出后立即失效。
4. 判定某个会话、令牌或停用账号是否已被吊销，并清理过期记录。
5. 停用时按账号主键作废旧令牌；启用不撤该档，新令牌靠更晚的签发时间放行。
6. 批量注销只删除账号行及其组、权限关系，不碰其它业务表。
"""

import logging

from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import User
from django.db import DatabaseError, IntegrityError, transaction
from django.db.models import Q
from django.utils import timezone

from .models import TokenRevocation

logger = logging.getLogger(__name__)

__all__ = [
    "ConflictError",
    "create_user",
    "is_revoked",
    "purge_expired",
    "purge_users",
    "revoke_session",
    "revoke_token",
    "revoke_user",
    "user_revoked_before",
    "set_user_active",
    "set_user_password",
    "set_operator",
]


class ConflictError(Exception):
    """写入与既有数据冲突（当前唯一来源：用户名已存在）。"""


def create_user(username: str, password: str, email: str) -> dict:
    """创建平台用户。

    Raises:
        ConflictError: 用户名已存在（由数据库唯一约束判定）。

    Returns:
        dict: {"id": int, "username": str, "email": str}
    """
    try:
        # savepoint：IntegrityError 之后外层事务仍可用，否则调用方（含用例事务）
        # 的后续查询会抛 TransactionManagementError
        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password, email=email)
    except IntegrityError as exc:
        raise ConflictError("用户名已存在") from exc
    return {"id": user.id, "username": user.username, "email": user.email}


def revoke_session(sid: str, ttl_seconds: int) -> None:
    """吊销一次登录会话（access 与 refresh 一起失效）。

    Args:
        sid: 会话标识。
        ttl_seconds: 记录有效期；必须覆盖 refresh 的剩余寿命。
    """
    _revoke(TokenRevocation.KIND_SESSION, sid, ttl_seconds)


def revoke_token(jti: str, ttl_seconds: int) -> None:
    """吊销单个令牌（用于没有 sid 的旧令牌兜底）。

    Args:
        jti: 令牌标识。
        ttl_seconds: 记录有效期；通常为令牌剩余寿命。
    """
    _revoke(TokenRevocation.KIND_TOKEN, jti, ttl_seconds)


def _revoke(kind: str, ref: str, ttl_seconds: int) -> None:
    """写一条吊销记录：同 (kind, ref) 幂等覆盖，并顺手清理一批过期行。

    Args:
        kind: 吊销粒度。
        ref: 会话标识或令牌标识；空值直接忽略。
        ttl_seconds: 记录有效期（秒），至少 1 秒。
    """
    if not ref:
        return
    expires_at = timezone.now() + timedelta(seconds=max(int(ttl_seconds), 1))
    with transaction.atomic():
        TokenRevocation.objects.update_or_create(
            kind=kind,
            ref=ref,
            defaults={"expires_at": expires_at},
        )
    _purge_expired_quietly(limit=100)


def _purge_expired_quietly(limit: int) -> None:
    """尽力清理过期行：失败只告警，不阻断登出（登出成功与否只取决于写入）。"""
    try:
        purge_expired(limit=limit)
    except DatabaseError as exc:
        logger.warning("清理过期吊销记录失败（不影响登出）: %s", exc)


def revoke_user(user_id: int, ttl_seconds: int | None = None) -> None:
    """按账号主键作废停用前签发的全部令牌。

    同一账号只留一行：重复停用覆盖 `created_at`，以最后一次停用为准。
    有效期默认覆盖 refresh 的最长寿命，避免记录先过期、旧令牌复活。

    Args:
        user_id: 目标账号主键。
        ttl_seconds: 记录有效期（秒）；缺省取 `JWT_REFRESH_TTL`。
    """
    ref = str(int(user_id))
    ttl = getattr(settings, "JWT_REFRESH_TTL", 604800) if ttl_seconds is None else ttl_seconds
    now = timezone.now()
    # 分界取停用时刻的下一秒：同一秒内先签发再停用的旧令牌作废，
    # 启用后新登录的 iat 至少晚这一秒，不会被自己刚写入的记录误伤。
    issued_cutoff = now + timedelta(seconds=1)
    expires_at = now + timedelta(seconds=max(int(ttl), 1))
    # update_or_create 不刷新 auto_now_add 的 created_at；重复停用必须以最后一次为准。
    with transaction.atomic():
        TokenRevocation.objects.update_or_create(
            kind=TokenRevocation.KIND_USER,
            ref=ref,
            defaults={"expires_at": expires_at},
        )
        TokenRevocation.objects.filter(kind=TokenRevocation.KIND_USER, ref=ref).update(
            created_at=issued_cutoff
        )


def user_revoked_before(user_id: int, issued_at: int) -> bool:
    """判定该账号的这张令牌是否早于最近一次停用。

    Args:
        user_id: 令牌 `sub`。
        issued_at: 令牌 `iat`（Unix 秒）。无 `iat` 时只要停用档还在就视为作废。

    Returns:
        存在未过期的账号档，且令牌签发不晚于该档 `created_at` 时为 True。
        分界比停用时刻晚 1 秒，同一秒内先签发再停用的令牌也算作废。
    """
    row = (
        TokenRevocation.objects.filter(
            kind=TokenRevocation.KIND_USER,
            ref=str(int(user_id)),
            expires_at__gt=timezone.now(),
        )
        .only("created_at")
        .first()
    )
    if row is None:
        return False
    if not issued_at:
        return True
    return int(issued_at) <= int(row.created_at.timestamp())


def is_revoked(sid: str = "", jti: str = "") -> bool:
    """判定该会话或令牌是否处于吊销状态（只看未过期记录）。

    Args:
        sid: 会话标识。
        jti: 令牌标识。

    Returns:
        bool: 任一标识命中未过期记录即为 True；两者皆空时为 False。
    """
    clauses = Q()
    if sid:
        clauses |= Q(kind=TokenRevocation.KIND_SESSION, ref=sid)
    if jti:
        clauses |= Q(kind=TokenRevocation.KIND_TOKEN, ref=jti)
    if not clauses:
        return False
    return TokenRevocation.objects.filter(clauses, expires_at__gt=timezone.now()).exists()


def purge_expired(limit: int = 100) -> int:
    """删除已过期的吊销记录（判定本就不看它们，这里只为控制表大小）。

    Args:
        limit: 单次最多删除的条数。

    Returns:
        int: 实际删除的条数。
    """
    expired_ids = list(
        TokenRevocation.objects.filter(expires_at__lte=timezone.now())
        .order_by("expires_at")
        .values_list("id", flat=True)[:limit]
    )
    if not expired_ids:
        return 0
    deleted, _ = TokenRevocation.objects.filter(id__in=expired_ids).delete()
    return deleted


def set_user_active(user_id: int, active: bool) -> User:
    """启用或停用一个账号（运营后台的唯一停用写口）。

    已是目标状态时不写库：运营后台的停用/启用按幂等语义对外承诺。

    Args:
        user_id: 目标账号主键。
        active: True 启用、False 停用。

    Returns:
        User: 更新后的账号实例。

    Raises:
        ValueError: 账号不存在。
    """
    user = _get_user_or_raise(user_id)
    target = bool(active)
    if user.is_active != target:
        user.is_active = target
        user.save(update_fields=["is_active"])
    if not target:
        # 重复停用也重写账号档：以最后一次停用时刻作废此前签发的令牌。
        revoke_user(user.id)
        # 停用同时失去助手作者。重新启用后不恢复，要超级管理员再授一次。
        from backend.apps.ai_assistant.api import revoke_assistant_author

        revoke_assistant_author(user.id)
    return user


def set_user_password(user_id: int, new_password: str) -> User:
    """直接设定账号密码（运营后台重置密码的唯一写口）。

    走 `set_password` 落哈希，明文不入库；不校验密码强度——调用方负责生成
    随机密码或保证强度。

    Args:
        user_id: 目标账号主键。
        new_password: 新明文密码，只在这次调用里存在。

    Returns:
        User: 更新后的账号实例。

    Raises:
        ValueError: 账号不存在，或新密码为空。
    """
    if not str(new_password or ""):
        raise ValueError("新密码不能为空")
    user = _get_user_or_raise(user_id)
    user.set_password(str(new_password))
    user.save(update_fields=["password"])
    return user


def set_operator(user_id: int, enabled: bool) -> User:
    """把账号加入或移出运营组（运营后台授予/取消的唯一写口）。

    组不存在时顺手建出来，避免「还没在后台建组」导致授予失败。已是目标状态时
    不写库，供调用方按幂等对外承诺。本函数不判权限，谁能调用由运营后台决定。

    Args:
        user_id: 目标账号主键。
        enabled: True 加入运营组、False 移出。

    Returns:
        User: 更新后的账号实例。

    Raises:
        ValueError: 账号不存在。
    """
    from django.contrib.auth.models import Group

    from backend.shared.users import OPERATOR_GROUP

    user = _get_user_or_raise(user_id)
    group, _ = Group.objects.get_or_create(name=OPERATOR_GROUP)
    already = user.groups.filter(pk=group.pk).exists()
    if enabled and not already:
        user.groups.add(group)
    elif not enabled and already:
        user.groups.remove(group)
    return user


def purge_users(user_ids: list[int]) -> list[int]:
    """删除一批账号本身，不碰其它 App 的业务表。

    Django 删除用户时会连带删除组关系与权限关系。项目、任务、缺陷、设备锁
    用字符串记创建者，不挂用户外键，因此不受影响。调用方负责权限校验；
    本函数不判断谁能删谁。任一删除失败则整批回滚。

    Args:
        user_ids: 待注销的账号主键，须已去重且全部存在。

    Returns:
        已删除的主键列表，顺序与入参一致。

    Raises:
        ValueError: 名单为空，或其中有主键对不上账号。
    """
    ids = [int(item) for item in user_ids]
    if not ids:
        raise ValueError("没有可注销的账号")
    found = set(User.objects.filter(pk__in=ids).values_list("pk", flat=True))
    missing = [item for item in ids if item not in found]
    if missing:
        raise ValueError("账号不存在")
    with transaction.atomic():
        User.objects.filter(pk__in=ids).delete()
    return ids


def _get_user_or_raise(user_id: int) -> User:
    """按主键取账号，取不到即抛 ValueError（供两个写口共用）。

    Args:
        user_id: 目标账号主键。

    Returns:
        User: 命中的账号实例。

    Raises:
        ValueError: 主键非法或账号不存在。
    """
    try:
        pk = int(str(user_id))
    except (TypeError, ValueError) as exc:
        raise ValueError("账号不存在") from exc
    user = User.objects.filter(pk=pk).first()
    if user is None:
        raise ValueError("账号不存在")
    return user
