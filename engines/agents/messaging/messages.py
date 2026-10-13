"""消息与事件层：工具返回 → 可读文本，以及用量、费用与上屏。

负责工具返回文本的提取、脱敏与截断、截图路径解析，一轮回复的用量与费用，
以及流式回复的上屏。只依赖标准库、AgentScope 消息类型与同包 billing，
不 import `engines.agents.role`（避免与角色层形成环）。
"""

from __future__ import annotations

import json

from datetime import datetime
from zoneinfo import ZoneInfo

from agentscope.console import ConsoleRenderer
from agentscope.message import DataBlock, Msg, TextBlock

from ..billing import DeepSeekBilling

_SHANGHAI = ZoneInfo("Asia/Shanghai")

__all__ = [
    "print_result",
    "render_reply_stream",
    "reply_cost",
    "reply_usage",
    "sanitize_tool_output_text",
    "screenshot_path_from_tool_output",
    "tool_output_text_parts",
]


# ── 工具返回 → 可读文本 ──


def screenshot_path_from_tool_output(output) -> str:
    """从 screenshot_page 工具结果里解析 summary.screenshot_path；取不到返回空串。"""
    for text in tool_output_text_parts(output):
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            # 明确忽略：本函数遍历多段文本，非 JSON 片段跳过即可
            continue
        if not isinstance(obj, dict):
            continue
        path = str(obj.get("screenshot_path") or "").replace("\\", "/").strip()
        if path:
            return path
    return ""


def tool_output_text_parts(output) -> list[str]:
    """工具 output → 纯文本片段（忽略 DataBlock 二进制）。"""
    texts: list[str] = []
    if isinstance(output, str):
        if output.strip():
            texts.append(output)
        return texts
    if isinstance(output, list):
        for block in output:
            if isinstance(block, TextBlock) and block.text:
                texts.append(block.text)
            elif isinstance(block, str) and block.strip():
                texts.append(block)
    return texts


def sanitize_tool_output_text(output, *, limit: int = 800) -> str:
    """工具返回 → 可落库短文本：保留 summary 与路径，剔除 base64 等超大字段。

    Args:
        output: 工具返回（字符串或块列表）。
        limit: 返回文本长度上限，超出截断并加省略号。

    Returns:
        清理后的文本。
    """
    parts: list[str] = []
    for text in tool_output_text_parts(output):
        try:
            obj = json.loads(text)
        except json.JSONDecodeError:
            parts.append(text)
            continue
        if not isinstance(obj, dict):
            parts.append(text)
            continue
        # 剔除可能夹带的超大字段
        cleaned = {
            k: v
            for k, v in obj.items()
            if k not in ("base64", "image", "data")
            and not (isinstance(v, str) and len(v) > 500 and k.endswith("_b64"))
        }
        # screenshot_page：只留可读摘要与路径
        if "screenshot_path" in cleaned or "screenshot_name" in cleaned:
            slim = {
                k: cleaned[k]
                for k in (
                    "serial",
                    "package",
                    "activity",
                    "screen_w",
                    "screen_h",
                    "screenshot_path",
                    "screenshot_name",
                )
                if k in cleaned
            }
            parts.append(json.dumps(slim or cleaned, ensure_ascii=False, default=str))
        else:
            parts.append(json.dumps(cleaned, ensure_ascii=False, default=str))
    # DataBlock 只记图片占位（图已由 screenshot_path 落盘）
    if isinstance(output, list) and any(isinstance(b, DataBlock) for b in output):
        if not parts:
            parts.append("[image]")
    text = "\n".join(parts).strip()
    if len(text) > limit:
        return text[:limit] + "…"
    return text


# ── 一轮回复的用量与费用 ──


def reply_usage(result) -> tuple[int, int, int]:
    """一轮回复的 (输入 token, 输出 token, 缓存命中)。取不到时全为 0。"""
    usage = getattr(result, "usage", None)
    if usage is None:
        return 0, 0, 0
    inp = int(getattr(usage, "input_tokens", 0) or 0)
    out = int(getattr(usage, "output_tokens", 0) or 0)
    hit = int(getattr(usage, "cache_input_tokens", 0) or 0)
    return inp, out, hit


def reply_cost(
    provider: str,
    model_name: str,
    result,
    *,
    created_at: datetime | None = None,
) -> tuple[float, float, float]:
    """按提供商与模型计费，返回 (输入费用, 输出费用, 缓存命中费用)（元）。

    Args:
        provider: 模型提供商。只有 deepseek 有计费口径，其余返回全 0。
        model_name: 模型名，交给计费表判定。
        result: 一轮回复。用量取自 reply_usage。
        created_at: 调用时刻。省略时取当前北京时间 —— 高峰期按双倍计价，
            因此不得把 None 直接透传给计费对象。

    Returns:
        三项费用；无对应计费口径时返回 (0.0, 0.0, 0.0)。
    """
    if str(provider or "").strip().lower() != "deepseek":
        return 0.0, 0.0, 0.0
    input_tokens, output_tokens, cache_hit_tokens = reply_usage(result)
    moment = created_at if created_at is not None else datetime.now(_SHANGHAI)
    return DeepSeekBilling().cost(
        model_name,
        input_tokens,
        output_tokens,
        cache_hit_tokens,
        moment,
    )


# ── 回复上屏 ──


def print_result(result) -> None:
    """打印文本、工具调用和工具结果。"""
    if result is None:
        return
    print(result.get_text_content())  # noqa: T201
    for kind in ("tool_call", "tool_result"):
        if result.has_content_blocks(kind):
            print(result.get_content_blocks(kind))  # noqa: T201


async def render_reply_stream(agent, user_msg) -> Msg | None:
    """把一次流式回复的事件实时上屏，并返回最后一条消息。

    Args:
        agent: AgentScope Agent 实例。
        user_msg: 本轮的用户消息。

    Returns:
        事件流末端的最终消息；没有最终消息时取渲染器记录的最后一条。
    """
    renderer = ConsoleRenderer(verbosity="debug")
    final: Msg | None = None
    async for item in agent.reply_stream(user_msg, yield_final_msg=True):
        if isinstance(item, Msg):
            final = item
            continue
        renderer.render(item)
    return final if final is not None else renderer.last_msg
