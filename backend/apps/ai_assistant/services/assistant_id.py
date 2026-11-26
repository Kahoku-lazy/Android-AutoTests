from __future__ import annotations

import secrets
import string

from django.utils import timezone

ASSISTANT_ID_ALPHABET = string.digits + string.ascii_uppercase
ASSISTANT_ID_SUFFIX_LEN = 3
ASSISTANT_ID_MAX_ATTEMPTS = 8


def generate_assistant_id() -> str:
    now = timezone.now()
    date_prefix = (
        timezone.localtime(now).strftime("%Y%m%d")
        if timezone.is_aware(now)
        else now.strftime("%Y%m%d")
    )
    suffix = "".join(secrets.choice(ASSISTANT_ID_ALPHABET) for _ in range(ASSISTANT_ID_SUFFIX_LEN))
    return f"{date_prefix}_{suffix}"


def generate_unique_assistant_id(is_taken) -> str:
    for _ in range(ASSISTANT_ID_MAX_ATTEMPTS):
        candidate = generate_assistant_id()
        if not is_taken(candidate):
            return candidate
    raise RuntimeError("助手编号生成失败：当日可用编号已耗尽")
