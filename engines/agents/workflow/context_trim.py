"""SOP 上下文裁剪：只留最近几步的截图，更早步骤收成文字结论。"""

from __future__ import annotations

from agentscope.message import UserMsg

# 含当前正要开始的这一步。已在上下文里的步数见 `_existing_to_keep`。
KEEP_SCREENSHOT_STEPS = 3
_EXECUTOR_MARK = "You are running one step of the SOP"
_VERIFIER_MARK = "Judge the work below"
_CONCLUSION_LIMIT = 800


def trim_agent_context(
    agent, upcoming_key: str, *, keep_steps: int = KEEP_SCREENSHOT_STEPS
) -> None:
    """就地裁剪智能体上下文。没有上下文时什么都不做。

    Args:
        agent: 带 `state.context` 的智能体。缺这个属性时跳过。
        upcoming_key: 即将开始的步骤键。与上一段相同表示重试。
        keep_steps: 含当前步在内保留截图的步数。
    """
    state = getattr(agent, "state", None)
    context = getattr(state, "context", None)
    if not isinstance(context, list) or keep_steps < 1:
        return
    trimmed = compress_older_steps(context, upcoming_key=upcoming_key, keep_steps=keep_steps)
    if trimmed is not context:
        context[:] = trimmed


def compress_older_steps(
    messages, *, upcoming_key: str, keep_steps: int = KEEP_SCREENSHOT_STEPS
) -> list:
    """更早步骤换成一条文字结论，最近几步的消息（含截图）原样留下。

    Args:
        messages: 智能体上下文消息。
        upcoming_key: 即将开始的步骤键。
        keep_steps: 含当前步在内保留截图的步数。

    Returns:
        新的消息列表。不需要裁剪时返回原列表。
    """
    prologue, groups = _split_steps(list(messages))
    retain = _existing_to_keep(groups, upcoming_key, keep_steps)
    if len(groups) <= retain:
        return messages
    older = groups[:-retain] if retain else groups
    kept = groups[-retain:] if retain else []
    conclusions = [_conclusion_message(key, segment) for key, segment in older]
    kept_messages = [msg for _, segment in kept for msg in segment]
    return [*prologue, *conclusions, *kept_messages]


def _existing_to_keep(groups: list, upcoming_key: str, keep_steps: int) -> int:
    """当前步还没写进上下文。重试时它已经在最后一组里，新步骤则还要占一个名额。"""
    if groups and groups[-1][0] == upcoming_key:
        return keep_steps
    return max(keep_steps - 1, 0)


def _split_steps(messages: list) -> tuple[list, list[tuple[str, list]]]:
    """按步骤提醒切开。同一键连续出现（重试）并进同一步。"""
    prologue: list = []
    groups: list[tuple[str, list]] = []
    for msg in messages:
        key = _step_key(msg)
        if key is None:
            if groups:
                groups[-1][1].append(msg)
            else:
                prologue.append(msg)
            continue
        if groups and groups[-1][0] == key:
            groups[-1][1].append(msg)
        else:
            groups.append((key, [msg]))
    return prologue, groups


def _step_key(msg) -> str | None:
    """从步骤提醒里取出步骤键。不是步骤开头则返回 None。"""
    text = _message_text(msg)
    if _EXECUTOR_MARK in text:
        return f"exec:{_heading(text)}"
    if _VERIFIER_MARK in text:
        return f"ver:{_verifier_body(text)}"
    return None


def _heading(text: str) -> str:
    """执行提醒里 `## ` 后的那一行。"""
    marker = "## "
    index = text.find(marker)
    if index < 0:
        return ""
    return text[index + len(marker) :].split("\n", 1)[0].strip()


def _verifier_body(text: str) -> str:
    """验收提醒里要核对的结果。"""
    needle = "this step had to prove."
    index = text.find(needle)
    if index < 0:
        return ""
    body = text[index + len(needle) :].replace("</system-reminder>", "")
    return body.strip()


def _conclusion_message(key: str, segment: list):
    """把一步收成不含截图的文字结论。"""
    title = key.split(":", 1)[-1] or "此前步骤"
    body = _conclusion_body(segment)
    return UserMsg(
        name="sop",
        content=f"【此前步骤结论】{title}\n{body}\n（该步截图已省略）",
    )


def _conclusion_body(segment: list) -> str:
    """优先用结构化交接或验收结论，否则用该步最后一段普通文本。"""
    structured = ""
    plain = ""
    for msg in segment:
        found = _structured_conclusion(msg)
        if found:
            structured = found
        for piece in _text_pieces(msg):
            if _EXECUTOR_MARK in piece or _VERIFIER_MARK in piece:
                continue
            cleaned = piece.strip()
            if cleaned:
                plain = cleaned
    body = structured or plain or "本步已结束。"
    if len(body) > _CONCLUSION_LIMIT:
        return body[:_CONCLUSION_LIMIT] + "…"
    return body


def _structured_conclusion(msg) -> str:
    """交接全文，或验收的通过与否加说明。"""
    data = getattr(msg, "structured_output", None)
    if not isinstance(data, dict):
        return ""
    handover = str(data.get("handover") or "").strip()
    if handover:
        return handover
    if "passed" not in data:
        return ""
    verdict = "通过" if data.get("passed") else "不通过"
    message = str(data.get("message") or "").strip()
    return f"{verdict}。{message}" if message else f"{verdict}。"


def _message_text(msg) -> str:
    return "\n".join(_text_pieces(msg))


def _text_pieces(msg) -> list[str]:
    content = getattr(msg, "content", "")
    if isinstance(content, str):
        return [content]
    pieces: list[str] = []
    for block in content or []:
        if isinstance(block, str):
            pieces.append(block)
            continue
        text = getattr(block, "text", None)
        if isinstance(text, str) and text:
            pieces.append(text)
    return pieces


def image_blocks(msg) -> list:
    """一条消息里的图片块，含工具结果里嵌套的。"""
    content = getattr(msg, "content", None)
    if isinstance(content, str) or content is None:
        return []
    found = []
    for block in content:
        found.extend(_images_in(block))
    return found


def _images_in(block) -> list:
    media = str(getattr(getattr(block, "source", None), "media_type", "") or "")
    if media.startswith("image/"):
        return [block]
    nested = getattr(block, "output", None)
    if not isinstance(nested, list):
        nested = getattr(block, "hint", None)
    if not isinstance(nested, list):
        return []
    found = []
    for item in nested:
        found.extend(_images_in(item))
    return found


__all__ = [
    "KEEP_SCREENSHOT_STEPS",
    "compress_older_steps",
    "image_blocks",
    "trim_agent_context",
]
