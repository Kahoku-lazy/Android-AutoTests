"""Generate unique document case IDs: TC-YYYYMMDD-NNNN."""

from __future__ import annotations

import re

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import TestDefinition

_ID_RE = re.compile(r"^TC-(\d{8})-(\d{4})$")


def next_case_id(*, max_retries: int = 8) -> str:
    """Allocate ``TC-YYYYMMDD-NNNN`` with same-day uniqueness and retry on race.

    Raises:
        RuntimeError: if allocation fails after retries.
    """
    today = timezone.now().strftime("%Y%m%d")
    prefix = f"TC-{today}-"
    for _ in range(max_retries):
        with transaction.atomic():
            last = (
                TestDefinition.objects.select_for_update()
                .filter(id__startswith=prefix)
                .order_by("-id")
                .values_list("id", flat=True)
                .first()
            )
            seq = 1
            if last:
                m = _ID_RE.match(last)
                if m and m.group(1) == today:
                    seq = int(m.group(2)) + 1
            case_id = f"{prefix}{seq:04d}"
            if not TestDefinition.objects.filter(id=case_id).exists():
                return case_id
    raise RuntimeError("无法生成唯一用例 ID，请稍后重试")


def allocate_case_id_on_create(create_fn, *, max_retries: int = 8):
    """Run ``create_fn(case_id)`` retrying when primary-key IntegrityError occurs."""
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
