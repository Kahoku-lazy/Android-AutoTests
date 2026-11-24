"""
模块功能：➡️ 生成助手 ID：随机生成并按库内唯一性查重 🏁
Python 调试：➡️ python -m backend.apps.ai_assistant.services.assistant_id 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 ai_assistant 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from __future__ import annotations

import secrets
import string

from django.utils import timezone

# 随机字符集：数字与大写字母，共 36 个。与运营 role_id 的小写集分开。
ASSISTANT_ID_ALPHABET = string.digits + string.ascii_uppercase
ASSISTANT_ID_SUFFIX_LEN = 3
# 单次创建最多重试次数；当日空间 46656 个，耗尽时快速失败而不是死循环。
ASSISTANT_ID_MAX_ATTEMPTS = 8


def generate_assistant_id() -> str:
    """生成一个助手编号。

    格式为服务器时区当天日期（YYYYMMDD）、一个下划线、3 位大写随机字符，总长 12 位。
    本函数不查重，唯一性由调用方与数据库唯一约束保证。

    Returns:
        12 位编号，例如 20261116_K3M。
    """
    now = timezone.now()
    date_prefix = (
        timezone.localtime(now).strftime("%Y%m%d")
        if timezone.is_aware(now)
        else now.strftime("%Y%m%d")
    )
    suffix = "".join(secrets.choice(ASSISTANT_ID_ALPHABET) for _ in range(ASSISTANT_ID_SUFFIX_LEN))
    return f"{date_prefix}_{suffix}"


def generate_unique_assistant_id(is_taken) -> str:
    """生成一个未被占用的助手编号。

    Args:
        is_taken: 判定函数，入参为候选编号，已被占用时返回真。

    Returns:
        未被占用的 12 位编号。

    Raises:
        RuntimeError: 重试上限内仍未得到未占用编号（当日空间耗尽）。
    """
    for _ in range(ASSISTANT_ID_MAX_ATTEMPTS):
        candidate = generate_assistant_id()
        if not is_taken(candidate):
            return candidate
    raise RuntimeError("助手编号生成失败：当日可用编号已耗尽")
