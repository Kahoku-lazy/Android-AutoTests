"""
文件名: ➡️ step_brief.py 🏁
路径: ➡️ engines/agents/workflow/step_brief.py 🏁
模块功能：➡️ 把一步的结构化字段拼成给执行者与验收者的步骤提示 🏁
Python 调试：➡️ python -m engines.agents.workflow.step_brief 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. executor_brief: 动作 + 【本步页面锚点】，只给执行者
2. verifier_brief: 要核对的结果 + 【本步日志证据】 + 【本步关键词表】，只给验收者
3. with_context: 把开场上下文（如设备 serial）重放到每一步，因为每步都是新角色实例
4. 两份简报互不串味：执行者简报不含要核对的结果，验收简报不含动作与锚点
🏁
关联模块：➡️
1. engines.agents.workflow.case_file: 导入 CaseStep，读本步的 anchor / log 字段
🏁
测试：➡️
1. tests/graybox/unit/test_step_brief.py: 锚点只进执行者、证据只进验收者、缺字段时与旧行为一致
🏁
"""

from __future__ import annotations

from typing import Final

from engines.agents.workflow.case_file import CaseStep

ANCHOR_LABELS: Final[dict[str, str]] = {
    "page": "页面",
    "entry": "入口",
    "target": "目标",
}

ANCHOR_HEADER: Final[str] = "【本步页面锚点】"
EVIDENCE_HEADER: Final[str] = "【本步日志证据】"
KEYWORDS_HEADER: Final[str] = "【本步关键词表】"
MISSING_KEYWORDS: Final[str] = "该型号关键词目录缺失，请退回截图核对页面；不要连续盲试关键词。"

__all__ = ["executor_brief", "verifier_brief", "with_context"]


def with_context(text: str, context: str) -> str:
    """把开场上下文放在步骤提示最前面。

    每个步骤都用新角色实例，历史里没有开场输入；设备 serial、轮次要求这类
    只在开场出现过一次的信息必须由这里逐步重放，否则新实例只能靠猜。

    Args:
        text: 步骤提示正文（动作简报或验收简报）。
        context: 开场上下文；空串时原样返回正文。

    Returns:
        带上下文的提示；上下文为空时与传入正文一致。
    """
    head = str(context or "").strip()
    return f"{head}\n\n{text}" if head else text


def executor_brief(step: CaseStep) -> str:
    """拼出执行角色这一步要做的事。

    有锚点时在动作后面补一段【本步页面锚点】；没有锚点时原样返回动作，
    与不支持结构化字段时的提示逐字一致。

    Args:
        step: 一步的结构化输入。

    Returns:
        给执行角色的步骤提示，不含该步要核对的结果。
    """
    if not step.anchor:
        return step.action
    lines = [
        f"- {ANCHOR_LABELS[key]}：{step.anchor[key]}"
        for key in ("page", "entry", "target")
        if step.anchor.get(key)
    ]
    if not lines:
        return step.action
    return f"{step.action}\n\n{ANCHOR_HEADER}\n" + "\n".join(lines)


def verifier_brief(step: CaseStep, keywords: str = "") -> str:
    """拼出验收角色这一步要核对的事。

    有 `log` 时补【本步日志证据】与【本步关键词表】；没有 `log` 但有该型号关键词表时
    只补【本步关键词表】，让验收按功能点选词。关键词表为空说明该型号目录缺失，
    提示里写明缺失并让验收退回截图核对，避免它连续盲试关键词。

    Args:
        step: 一步的结构化输入。
        keywords: 该型号的关键词目录正文；空串表示目录缺失。

    Returns:
        给验收角色的步骤提示，不含该步的动作与锚点。
    """
    parts = [step.expected]
    text = str(keywords or "").strip()
    if step.log is not None:
        parts.append(
            f"{EVIDENCE_HEADER}sku={step.log.sku} port={step.log.port} keyword={step.log.keyword}"
        )
        if text:
            parts.append(f"{KEYWORDS_HEADER}\n{text}")
        else:
            parts.append(f"{KEYWORDS_HEADER}{step.log.sku} {MISSING_KEYWORDS}")
    elif text:
        # 用例没写 log（旧资产）：仍然把该型号的关键词表给验收，让它按功能点选词，而不是盲试
        parts.append(f"{KEYWORDS_HEADER}\n{text}")
    return "\n\n".join(parts)
