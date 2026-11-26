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
    pass


def create_user(username: str, password: str, email: str) -> dict:
    try:
        with transaction.atomic():
            user = User.objects.create_user(username=username, password=password, email=email)
    except IntegrityError as exc:
        raise ConflictError("用户名已存在") from exc
    return {"id": user.id, "username": user.username, "email": user.email}


def revoke_session(sid: str, ttl_seconds: int) -> None:
    _revoke(TokenRevocation.KIND_SESSION, sid, ttl_seconds)


def revoke_token(jti: str, ttl_seconds: int) -> None:
    _revoke(TokenRevocation.KIND_TOKEN, jti, ttl_seconds)


def _revoke(kind: str, ref: str, ttl_seconds: int) -> None:
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
    try:
        purge_expired(limit=limit)
    except DatabaseError as exc:
        logger.warning("清理过期吊销记录失败（不影响登出）: %s", exc)


def revoke_user(user_id: int, ttl_seconds: int | None = None) -> None:
    ref = str(int(user_id))
    ttl = getattr(settings, "JWT_REFRESH_TTL", 604800) if ttl_seconds is None else ttl_seconds
    now = timezone.now()
    issued_cutoff = now + timedelta(seconds=1)
    expires_at = now + timedelta(seconds=max(int(ttl), 1))
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
    clauses = Q()
    if sid:
        clauses |= Q(kind=TokenRevocation.KIND_SESSION, ref=sid)
    if jti:
        clauses |= Q(kind=TokenRevocation.KIND_TOKEN, ref=jti)
    if not clauses:
        return False
    return TokenRevocation.objects.filter(clauses, expires_at__gt=timezone.now()).exists()


def purge_expired(limit: int = 100) -> int:
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
    user = _get_user_or_raise(user_id)
    target = bool(active)
    if user.is_active != target:
        user.is_active = target
        user.save(update_fields=["is_active"])
    if not target:
        revoke_user(user.id)
        from backend.apps.ai_assistant.api import revoke_assistant_author

        revoke_assistant_author(user.id)
    return user


def set_user_password(user_id: int, new_password: str) -> User:
    if not str(new_password or ""):
        raise ValueError("新密码不能为空")
    user = _get_user_or_raise(user_id)
    user.set_password(str(new_password))
    user.save(update_fields=["password"])
    return user


def set_operator(user_id: int, enabled: bool) -> User:
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
    try:
        pk = int(str(user_id))
    except (TypeError, ValueError) as exc:
        raise ValueError("账号不存在") from exc
    user = User.objects.filter(pk=pk).first()
    if user is None:
        raise ValueError("账号不存在")
    return user
