"""
账号写入与登出吊销。

业务：
1. 创建平台用户，并返回账号编号、用户名和邮箱。
2. 用户名已存在时拒绝创建。
3. 记录吊销（会话级 sid / 单令牌级 jti），供登出后立即失效。
4. 判定某个会话或令牌是否已被吊销，并清理过期记录。
"""

import logging

from datetime import timedelta

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
    "revoke_session",
    "revoke_token",
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
