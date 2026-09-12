"""AgentScope 工具包装层 — 把 TaskRequest.tools 的 ToolSpec 包装成 AgentScope FunctionTool。"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging

from agentscope.message import Base64Source, DataBlock, TextBlock
from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.skill import LocalSkillLoader
from agentscope.tool import FunctionTool, ToolChunk, Toolkit

from engines.ai.base import ToolSpec

__all__ = ["PlatformFunctionTool", "build_toolkit"]

logger = logging.getLogger("ai_assistant.tools")


def _safe_log(value) -> str:
    """工具返回值 → 可安全打印的字符串（图片结果脱敏 base64，只留 summary）。"""
    if isinstance(value, str):
        return value
    if isinstance(value, dict) and "image" in value:
        return json.dumps(value.get("summary") or {}, ensure_ascii=False, default=str)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False, default=str)
    return str(value)


def _image_result_to_chunk(result) -> ToolChunk | None:
    """截图工具返回的 image dict → ToolChunk（文本 summary + 图片 DataBlock）。"""
    if isinstance(result, dict) and "image" in result:
        img = result["image"]
        return ToolChunk(
            content=[
                TextBlock(text=json.dumps(result.get("summary") or {}, ensure_ascii=False, default=str)),
                DataBlock(source=Base64Source(data=img["base64"], media_type=img["media_type"])),
            ]
        )
    return None


class PlatformFunctionTool(FunctionTool):
    """平台工具：构造时绑定 user_id，只读/自动放行，其余写操作 ASK。"""

    def __init__(self, spec: ToolSpec, user_id: str = ""):
        # 写工具（read_only=False）串行执行，避免并发破坏设备动作顺序。
        super().__init__(
            spec.handler,
            is_read_only=spec.read_only,
            is_concurrency_safe=spec.read_only,
        )
        self._user_id = user_id
        self._auto_allow = spec.auto_allow
        props = self.input_schema.get("properties", {})
        props.pop("user_id", None)
        required = self.input_schema.get("required", [])
        if "user_id" in required:
            required.remove("user_id")

    async def call(self, **kwargs):
        kwargs.setdefault("user_id", self._user_id)
        logger.info(
            "【工具调用】%s 入参=%s",
            self._func.__name__,
            json.dumps(kwargs, ensure_ascii=False, default=str),
        )
        if inspect.iscoroutinefunction(self._func):
            result = await super().call(**kwargs)
            logger.info("【工具返回】%s 返回=%s", self._func.__name__, _safe_log(result))
            return result
        result = await asyncio.to_thread(self._func, **kwargs)
        logger.info("【工具返回】%s 返回=%s", self._func.__name__, _safe_log(result))
        chunk = _image_result_to_chunk(result)
        if chunk is not None:
            return chunk
        return self._convert_func_result_to_chunk(result)

    async def check_permissions(self, tool_input, context):
        if self.is_read_only:
            return PermissionDecision(PermissionBehavior.ALLOW, "只读工具直接放行")
        if self._auto_allow:
            return PermissionDecision(PermissionBehavior.ALLOW, "平台内部锁，自动放行")
        return PermissionDecision(PermissionBehavior.ASK, "写工具需确认")


def build_toolkit(
    specs: list[ToolSpec], user_id: str = "", skill_dirs: list[str] | None = None
) -> Toolkit:
    """把 ToolSpec 列表包装成 AgentScope Toolkit；skill_dirs 为空则不挂 Skill。"""
    loaders = [
        LocalSkillLoader(directory=d, scan_subdir=False) for d in (skill_dirs or []) if d
    ]
    return Toolkit(
        tools=[PlatformFunctionTool(s, user_id=user_id) for s in specs],
        skills_or_loaders=loaders,
    )
