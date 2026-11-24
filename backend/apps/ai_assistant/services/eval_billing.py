"""
模块功能：➡️ 评测用量入账。一次模型调用一条，失败只记日志 🏁
Python 调试：➡️ python -m backend.apps.ai_assistant.services.eval_billing 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 ai_assistant 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from __future__ import annotations

import logging

log = logging.getLogger(__name__)

SOURCE = "assistant_eval"


def record_eval_usages(events: list[dict], execution_id: str) -> int:
    """
    把评测里的模型调用写入账本。

    Args:
        events: 每项含 round、model、input_tokens、output_tokens。
        execution_id: 本次评测运行编号。

    Returns:
        成功写入的条数。
    """
    from backend.apps.usage_ledger.api import record_usage

    written = 0
    for item in events:
        round_key = str(item.get("round") or "")
        try:
            result = record_usage(
                event_id=f"{SOURCE}:{execution_id}:{round_key}",
                provider=str(item.get("provider") or "deepseek"),
                model=str(item.get("model") or ""),
                occurred_at=item["occurred_at"],
                input_tokens=int(item.get("input_tokens") or 0),
                output_tokens=int(item.get("output_tokens") or 0),
                category="LLM",
                source=SOURCE,
                execution_id=execution_id,
            )
        except Exception:
            log.exception("assistant eval usage write failed execution=%s", execution_id)
            continue
        if result is not None:
            written += 1
    return written
