"""消息与事件层：把 AgentScope 的回复读成语义化记录（引擎侧唯一解析归属）。

本包只负责「智能体说了什么、调了什么、返回了什么」：

- 消息块 → 语义记录：思考、工具调用、工具返回、图片、截图路径；
- 输入文本提取与上下文摘要（供任务详情页展示「输入 / 思考 / 工具 / 文本」）；
- 工具返回的脱敏与截断（剔除 base64，只留可读摘要与路径）；
- ``RoleResult``：一次角色执行的任务报告（输出 / 思考 / 工具 / 截图 / 用量 / 费用）。

边界（见变更设计 D1/D4）：

- 本包是叶子：只依赖标准库与 AgentScope 的消息类型，MUST NOT import ``engines.ai.agents``
  （否则与智能体包成环）；用量累加与计价在 ``billing``，点击与日志证据在 ``workflow``。
- ``RoleResult.cost`` 由调用方（智能体包，转为费用）填值，本包不依赖计价。

后续变更将把这里「事后翻上下文」的读法换成消费 AgentScope 的事件流（``reply_stream``）——
届时本包是唯一替换面。
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
    "count_tool_results",
    "extract_screenshot",
    "extract_screenshot_path",
    "prompt_to_input_text",
    "sanitize_tool_output_text",
    "screenshot_path_from_tool_output",
    "tool_output_text_parts",
]


# ── 工具返回 → 可读文本 ──


def screenshot_path_from_tool_output(output) -> str:
    """从 screenshot_page 工具结果里解析 summary.screenshot_path（工具真相，非模型编造）。"""
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
    """工具返回 → 可落库短文本：保留 summary/路径，剔除 base64。"""
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
        # 去掉可能夹带的超大字段
        cleaned = {
            k: v
            for k, v in obj.items()
            if k not in ("base64", "image", "data")
            and not (isinstance(v, str) and len(v) > 500 and k.endswith("_b64"))
        }
        # screenshot_page：优先只留可读摘要 + 路径
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
    # DataBlock 仅记占位（图已由 screenshot_path / 验收证据落盘）
    if isinstance(output, list) and any(isinstance(b, DataBlock) for b in output):
        if not parts:
            parts.append("[image]")
    text = "\n".join(parts).strip()
    if len(text) > limit:
        return text[:limit] + "…"
    return text


def prompt_to_input_text(content: str | list) -> str:
    """发给 Agent 的 content → 可展示的输入文本（忽略图片块）。"""
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
    """一次任务执行的任务报告（角色执行任务的完整产出）。

    把 AgentScope 的原始 reply（消息块 + usage）解析成语义化字段，屏蔽框架差异。
    供用户了解结果（output/screenshot/cost），供开发者调试（thinking/tool_usage/usage）。
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
    """从一组消息内容块收集思考 + 工具（脱敏）。"""
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
    """从 agent 完整上下文收集思考 + 工具调用/返回（脱敏，无 base64）。"""
    thinking: list[str] = []
    tool_usage: list[dict] = []
    for msg in context or []:
        t, u = collect_from_blocks(getattr(msg, "content", None) or [])
        thinking.extend(t)
        tool_usage.extend(u)
    return thinking, tool_usage


def count_tool_results(context) -> int:
    """上下文里已有的工具返回条数。

    上下文是**整个任务累积**的，工作流用这个数字切出「本步新增」的工具返回，
    否则本步的动作发出时刻会取到上一步的值（真机验证时踩到过）。
    """
    _, rows = collect_trace(context)
    return sum(1 for row in rows if row.get("type") == "result")


def context_summary(context) -> list[dict]:
    """上下文摘要：每条消息只留 role + 截断 500 字文本（脱敏图片）。"""
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
    """从本轮 agent 上下文里取最后一次 screenshot_page 的落盘相对路径。

    扫完整 context（工具结果在中间消息，不在最终 reply），路径来自工具 summary。
    """
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
