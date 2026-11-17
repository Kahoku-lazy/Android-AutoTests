"""
python -m 调试路径: backend.apps.ai_assistant.services.role_id

本模块的业务功能如下：
1. generate_role_id: 生成一个「当天日期 + 3 位随机字符」的角色短标识。
2. generate_unique_role_id: 在已占用集合之外生成一个未占用的短标识。
"""

from __future__ import annotations

import secrets
import string

from django.utils import timezone

# 随机字符集：数字与小写字母，共 36 个。
ROLE_ID_ALPHABET = string.digits + string.ascii_lowercase
ROLE_ID_SUFFIX_LEN = 3
# 单次创建最多重试次数；当日空间 46656 个，耗尽时快速失败而不是死循环。
ROLE_ID_MAX_ATTEMPTS = 8


def generate_role_id() -> str:
    """生成一个角色短标识。

    格式为服务器时区当天日期（YYYYMMDD）加 3 位随机字符，总长 11 位。
    本函数不查重，唯一性由调用方与数据库唯一约束保证。

    Returns:
        11 位短标识，例如 20261115a3f。
    """
    now = timezone.now()
    date_prefix = (
        timezone.localtime(now).strftime("%Y%m%d")
        if timezone.is_aware(now)
        else now.strftime("%Y%m%d")
    )
    suffix = "".join(secrets.choice(ROLE_ID_ALPHABET) for _ in range(ROLE_ID_SUFFIX_LEN))
    return date_prefix + suffix


def generate_unique_role_id(is_taken) -> str:
    """生成一个未被占用的角色短标识。

    Args:
        is_taken: 判定函数，入参为候选标识，已被占用时返回真。

    Returns:
        未被占用的 11 位短标识。

    Raises:
        RuntimeError: 重试上限内仍未得到未占用标识（当日空间耗尽）。
    """
    for _ in range(ROLE_ID_MAX_ATTEMPTS):
        candidate = generate_role_id()
        if not is_taken(candidate):
            return candidate
    raise RuntimeError("角色标识生成失败：当日可用标识已耗尽")
