"""
python -m 调试路径: backend.apps.case_manager.api_ids

本模块的业务功能如下：
1. next_case_id: 在自动化表与功能表之间分配不重复的用例编号。
"""

from __future__ import annotations

import re

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import AutomationCase, FunctionalCase

_ID_RE = re.compile(r"^TC-(\d{8})-(\d{4})$")
_MODELS = (AutomationCase, FunctionalCase)


def next_case_id(*, max_retries: int = 8) -> str:
    """分配当天不重复的 ``TC-YYYYMMDD-NNNN``。

    Returns:
        新编号。

    Raises:
        RuntimeError: 重试后仍冲突。
    """
    today = timezone.now().strftime("%Y%m%d")
    prefix = f"TC-{today}-"
    for _ in range(max_retries):
        with transaction.atomic():
            last_seq = 0
            for model in _MODELS:
                last = (
                    model.objects.select_for_update()
                    .filter(id__startswith=prefix)
                    .order_by("-id")
                    .values_list("id", flat=True)
                    .first()
                )
                if not last:
                    continue
                matched = _ID_RE.match(last)
                if matched and matched.group(1) == today:
                    last_seq = max(last_seq, int(matched.group(2)))
            case_id = f"{prefix}{last_seq + 1:04d}"
            taken = any(model.objects.filter(id=case_id).exists() for model in _MODELS)
            if not taken:
                return case_id
    raise RuntimeError("无法生成唯一用例 ID，请稍后重试")


def allocate_case_id_on_create(create_fn, *, max_retries: int = 8):
    """用新编号调用 ``create_fn``，主键冲突时重试。

    Raises:
        RuntimeError: 重试后仍冲突。
    """
    last_exc: Exception | None = None
    for _ in range(max_retries):
        case_id = next_case_id(max_retries=1)
        try:
            with transaction.atomic():
                return create_fn(case_id)
        except IntegrityError as exc:
            last_exc = exc
            continue
    raise RuntimeError("无法创建用例，ID 冲突") from last_exc
