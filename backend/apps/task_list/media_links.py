from __future__ import annotations

import hmac
import time

from hashlib import sha256

from django.conf import settings

_MIN_TTL = 60
_MAX_TTL = 3600


def _ttl(ttl: int | None) -> int:
    value = int(ttl if ttl is not None else settings.MEDIA_LINK_TTL_SECONDS)
    return max(_MIN_TTL, min(_MAX_TTL, value))


def _digest(task_id: int, media_id: int, expires: int) -> str:
    message = f"{int(task_id)}:{int(media_id)}:{int(expires)}".encode()
    secret = str(settings.MEDIA_LINK_SECRET).encode()
    return hmac.new(secret, message, sha256).hexdigest()


def sign(
    task_id: int, media_id: int, *, now: int | None = None, ttl: int | None = None
) -> tuple[int, str]:
    start = int(now if now is not None else time.time())
    expires = start + _ttl(ttl)
    return expires, _digest(task_id, media_id, expires)


def build_path(task_id: int, media_id: int, expires: int, signature: str) -> str:
    return f"/media/signed/{int(task_id)}/{int(media_id)}/{int(expires)}/{signature}/"


def verify(
    task_id: int,
    media_id: int,
    expires: int,
    signature: str,
    *,
    now: int | None = None,
) -> bool:
    try:
        expires_at = int(expires)
    except (TypeError, ValueError):
        return False
    current = int(now if now is not None else time.time())
    if expires_at < current:
        return False
    return hmac.compare_digest(_digest(task_id, media_id, expires_at), str(signature or ""))
