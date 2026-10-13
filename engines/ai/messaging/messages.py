"""消息与事件层：把 AgentScope 的回复与上下文读成语义化记录。

负责消息块 → 语义记录（思考 / 工具调用 / 工具返回 / 图片 / 截图路径）、输入文本提取、
上下文摘要、工具返回的脱敏与截断，以及一次角色执行的任务报告 `RoleResult`。
只依赖标准库与 AgentScope 消息类型，不 import `engines.ai.agents`。
"""

from __future__ import annotations

import json

from typing import Any

from agentscope.message import (
    DataBlock,
    TextBlock,
    ThinkingBlock,
    ToolCallBlock,
    ToolResultBlock,
)
from pydantic import BaseModel, Field

__all__ = [
    "RoleResult",
    "collect_from_blocks",
    "collect_trace",
    "context_summary",
    "extract_screenshot",
    "extract_screenshot_path",
    "prompt_to_input_text",
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


def prompt_to_input_text(content: str | list) -> str:
    """发给 Agent 的 content → 输入文本（忽略图片块）。"""
    if isinstance(content, str):
        return content.strip()
    parts: list[str] = []
    for block in content or []:
        if isinstance(block, TextBlock) and block.text:
            parts.append(block.text)
        elif isinstance(block, str) and block.strip():
            parts.append(block)
    return "\n".join(parts).strip()


# ── 数据模型 ──


class RoleResult(BaseModel):
    """一次角色执行的任务报告：把 AgentScope 的原始 reply 解析成语义化字段。

    字段含义见各 `Field` 的 description；`cost` 由调用方按用量填入。
    """

    role: str = Field(default="", description="本角色：planner / executor / verifier")
    model_name: str = Field(default="", description="底层模型名（用量按此聚合）")
    output: str = Field(default="", description="输出结果文本（TextBlock 拼接，供 JSON 解析）")
    input_text: str = Field(
        default="", description="本轮发给 Agent 的用户输入文本（详情页「输入」）"
    )
    thinking: list[str] = Field(default_factory=list, description="思考过程（ThinkingBlock 逐个）")
    tool_usage: list[dict] = Field(
        default_factory=list,
        description="工具使用记录（type=call/result/image + name/入参/返回/状态）",
    )
    context: list[dict] = Field(
        default_factory=list,
        description="自己上下文摘要（每条仅 role + 截断文本，脱敏图片）",
    )
    screenshot: Any = Field(
        default=None,
        description="最后一张截图 DataBlock（executor 产出 → 传给 verifier）",
    )
    screenshot_path: str = Field(
        default="",
        description="本轮最后一次 screenshot_page 落盘相对 MEDIA 路径（验收证据用）",
    )
    usage: dict = Field(
        default_factory=dict,
        description="本轮用量（input_tokens/output_tokens/cache_input_tokens/cache_creation_input_tokens）",
    )
    cost: float = Field(default=0.0, description="本轮费用（元，仅 DeepSeek 计费，其余 0）")


# ── 上下文 → 语义记录 ──


def collect_from_blocks(blocks) -> tuple[list[str], list[dict]]:
    """从一组消息内容块收集思考与工具记录（工具返回已脱敏）。

    Args:
        blocks: 消息内容块列表。

    Returns:
        (思考文本列表, 工具记录列表)。
    """
    thinking: list[str] = []
    tool_usage: list[dict] = []
    for block in blocks:
        if isinstance(block, ThinkingBlock) and block.thinking:
            thinking.append(block.thinking)
        elif isinstance(block, ToolCallBlock):
            tool_usage.append({"type": "call", "name": block.name, "input": block.input})
        elif isinstance(block, ToolResultBlock):
            row: dict = {
                "type": "result",
                "name": block.name,
                "state": getattr(block, "state", ""),
            }
            out_text = sanitize_tool_output_text(block.output)
            if out_text:
                row["output"] = out_text
            path = screenshot_path_from_tool_output(block.output)
            if path:
                row["screenshot_path"] = path
            tool_usage.append(row)
        elif isinstance(block, DataBlock):
            tool_usage.append(
                {
                    "type": "image",
                    "media_type": getattr(block.source, "media_type", ""),
                }
            )
    return thinking, tool_usage


def collect_trace(context) -> tuple[list[str], list[dict]]:
    """从 agent 完整上下文收集思考与工具记录（脱敏，无 base64）。

    Args:
        context: agent 的消息列表。

    Returns:
        (思考文本列表, 工具记录列表)。
    """
    thinking: list[str] = []
    tool_usage: list[dict] = []
    for msg in context or []:
        t, u = collect_from_blocks(getattr(msg, "content", None) or [])
        thinking.extend(t)
        tool_usage.extend(u)
    return thinking, tool_usage


def context_summary(context) -> list[dict]:
    """上下文摘要：每条消息只留 role 与截断 500 字的文本（图片脱敏）。

    Args:
        context: agent 的消息列表。

    Returns:
        [{"role": str, "text": str}]。
    """
    summary = []
    for m in context or []:
        content = getattr(m, "content", "")
        text = (
            content
            if isinstance(content, str)
            else "".join(getattr(b, "text", "") for b in (content or []) if hasattr(b, "text"))
        )
        summary.append({"role": getattr(m, "role", ""), "text": text[:500]})
    return summary


# ── 截图 ──


def extract_screenshot(content) -> Any:
    """从 reply 内容块里取最后一张截图 DataBlock（倒序找，返回最后一个）。"""
    for block in reversed(content or []):
        if isinstance(block, DataBlock):
            return block
        if isinstance(block, ToolResultBlock):
            out = block.output
            if isinstance(out, DataBlock):
                return out
            if isinstance(out, list):
                for b in reversed(out):
                    if isinstance(b, DataBlock):
                        return b
    return None


def extract_screenshot_path(context) -> str:
    """从本轮 agent 上下文里取最后一次 screenshot_page 的落盘相对路径；取不到返回空串。"""
    last = ""
    for msg in context or []:
        for block in getattr(msg, "content", None) or []:
            if not isinstance(block, ToolResultBlock):
                continue
            if getattr(block, "name", "") != "screenshot_page":
                continue
            path = screenshot_path_from_tool_output(block.output)
            if path:
                last = path
    return last
