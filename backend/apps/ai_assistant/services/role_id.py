from __future__ import annotations

import secrets
import string

from django.utils import timezone

ROLE_ID_ALPHABET = string.digits + string.ascii_lowercase
ROLE_ID_SUFFIX_LEN = 3
ROLE_ID_MAX_ATTEMPTS = 8


def generate_role_id() -> str:
    now = timezone.now()
    date_prefix = (
        timezone.localtime(now).strftime("%Y%m%d")
        if timezone.is_aware(now)
        else now.strftime("%Y%m%d")
    )
    suffix = "".join(secrets.choice(ROLE_ID_ALPHABET) for _ in range(ROLE_ID_SUFFIX_LEN))
    return date_prefix + suffix


def generate_unique_role_id(is_taken) -> str:
    for _ in range(ROLE_ID_MAX_ATTEMPTS):
        candidate = generate_role_id()
        if not is_taken(candidate):
            return candidate
    raise RuntimeError("角色标识生成失败：当日可用标识已耗尽")
