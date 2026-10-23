"""
python -m 调试路径: backend.apps.task_list.media_links

本模块的业务功能如下：
1. sign: 为一张任务截图签发带过期时间的直链路径。
2. verify: 校验直链的过期时间与 HMAC 签名。
"""

from __future__ import annotations

import hmac
import time

from hashlib import sha256

from django.conf import settings

_MIN_TTL = 60
_MAX_TTL = 3600


def _ttl(ttl: int | None) -> int:
    """把有效期限制在 60 秒到 1 小时之间。"""
    value = int(ttl if ttl is not None else settings.MEDIA_LINK_TTL_SECONDS)
    return max(_MIN_TTL, min(_MAX_TTL, value))


def _digest(task_id: int, media_id: int, expires: int) -> str:
    """对 `task:media:expires` 做 HMAC-SHA256。"""
    message = f"{int(task_id)}:{int(media_id)}:{int(expires)}".encode()
    secret = str(settings.MEDIA_LINK_SECRET).encode()
    return hmac.new(secret, message, sha256).hexdigest()


def sign(
    task_id: int, media_id: int, *, now: int | None = None, ttl: int | None = None
) -> tuple[int, str]:
    """
    签发一张截图的直链参数。

    Args:
        task_id: 任务编号。
        media_id: 图片行编号。
        now: 当前 Unix 秒，缺省取系统时间（测试可注入）。
        ttl: 有效期秒数，缺省读 settings，限制在 60–3600。

    Returns:
        (过期时刻, 签名)。
    """
    start = int(now if now is not None else time.time())
    expires = start + _ttl(ttl)
    return expires, _digest(task_id, media_id, expires)


def build_path(task_id: int, media_id: int, expires: int, signature: str) -> str:
    """直链的相对路径。前端按当前 origin 补全。"""
    return f"/media/signed/{int(task_id)}/{int(media_id)}/{int(expires)}/{signature}/"


def verify(
    task_id: int,
    media_id: int,
    expires: int,
    signature: str,
    *,
    now: int | None = None,
) -> bool:
    """
    校验直链的过期时间与签名。

    Args:
        task_id: 任务编号。
        media_id: 图片行编号。
        expires: 链接里的过期时刻（Unix 秒）。
        signature: 链接里的签名。
        now: 当前 Unix 秒，缺省取系统时间（测试可注入）。

    Returns:
        未过期且签名一致时为 True，否则 False。
    """
    try:
        expires_at = int(expires)
    except (TypeError, ValueError):
        return False
    current = int(now if now is not None else time.time())
    if expires_at < current:
        return False
    return hmac.compare_digest(_digest(task_id, media_id, expires_at), str(signature or ""))
