"""LLM 语义提交校验 — 页面结构分析的语义增强层（纯校验，不调 LLM）。

语义命名由 Agent 的 ReAct 循环自然产生（工具入参），本模块只负责：
resource_id 真实性校验（防幻觉）+ metrics 枚举清洗 + 结构归一。

对齐 `save_case` 的 `validate_steps` 模式：松 input_schema + handler 深度校验。
"""

from __future__ import annotations

import logging

logger = logging.getLogger("ai_assistant.llm_semantic")

# 指标枚举（与 algorithms.layout.metrics 口径一致）
_METRICS = {"可点击", "可滚动", "可勾选"}


def validate_semantic(semantic: dict, input_elements: list) -> dict:
    """校验并清洗语义命名提交，返回归一化结构。

    Args:
        semantic: Agent 提交的语义 dict，形如
            {"page_summary": str, "sections": list,
             "elements": [{"resource_id", "func_name", "metrics"}], "cards": list}
        input_elements: 快照的元素列表（含 resource_id），用于防幻觉校验。

    Returns:
        归一化 dict。resource_id 不属于 input_elements 的条目 func_name 置空；
        metrics 只保留枚举内取值；缺失字段给安全默认值。
    """
    semantic = semantic or {}
    input_rids = {e.get("resource_id", "") for e in input_elements if e.get("resource_id")}

    elements = []
    for el in semantic.get("elements") or []:
        if not isinstance(el, dict):
            continue
        rid = el.get("resource_id", "") or ""
        if rid not in input_rids:
            func_name = ""  # 幻觉 rid → 置空，不产生虚假命名
        else:
            func_name = str(el.get("func_name", "") or "").strip()
        metrics = [m for m in (el.get("metrics") or []) if m in _METRICS]
        elements.append({"resource_id": rid, "func_name": func_name, "metrics": metrics})

    return {
        "page_summary": str(semantic.get("page_summary", "") or "").strip(),
        "sections": semantic.get("sections") or [],
        "elements": elements,
        "cards": semantic.get("cards") or [],
    }
