"""AgentScope 工具包装层 — 把 TaskRequest.tools 的 ToolSpec 包装成 AgentScope FunctionTool。"""

from __future__ import annotations

import asyncio
import inspect
import json
import logging

from agentscope.exception import DeveloperOrientedException
from agentscope.message import Base64Source, DataBlock, TextBlock
from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.skill import LocalSkillLoader
from agentscope.tool import FunctionTool, ToolChunk, ToolGroup, Toolkit

from engines.ai.base import ToolSpec

from .tool_serial import LOG_EMPTY

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
                TextBlock(
                    text=json.dumps(result.get("summary") or {}, ensure_ascii=False, default=str)
                ),
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
        # 只对**声明了** user_id 的工具注入归属：引擎自带设备工具没有用户概念，
        # 无条件注入会让它们每次调用都抛 TypeError（真机跑测实测踩到）。
        try:
            self._accepts_user_id = "user_id" in inspect.signature(spec.handler).parameters
        except (TypeError, ValueError):
            self._accepts_user_id = False
        props = self.input_schema.get("properties", {})
        props.pop("user_id", None)
        required = self.input_schema.get("required", [])
        if "user_id" in required:
            required.remove("user_id")

    async def call(self, **kwargs):
        """执行工具：注入 user_id、记调用日志、把返回值转成 ToolChunk。

        Args:
            **kwargs: 工具入参。

        Returns:
            工具返回值转换出的 ToolChunk。

        Raises:
            DeveloperOrientedException: 工具返回值为 `LOG_EMPTY`（日志为空）时，
                转成开发者可见异常而不是普通参数错误。
        """
        if self._accepts_user_id:
            kwargs.setdefault("user_id", self._user_id)
        logger.info(
            "【工具调用】%s 入参=%s",
            self._func.__name__,
            json.dumps(kwargs, ensure_ascii=False, default=str),
        )
        try:
            if inspect.iscoroutinefunction(self._func):
                result = await super().call(**kwargs)
            else:
                result = await asyncio.to_thread(self._func, **kwargs)
        except ValueError as exc:
            if str(exc) == LOG_EMPTY:
                raise DeveloperOrientedException(LOG_EMPTY) from exc
            raise
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
    specs: list[ToolSpec],
    user_id: str = "",
    skill_dirs: list[str] | None = None,
    *,
    scan_subdir: bool = False,
    tool_groups: list[ToolGroup] | None = None,
) -> Toolkit:
    """把常驻工具包装成 Toolkit，可开关组另挂。

    Args:
        specs: 进入常驻组的工具。
        user_id: 注入给声明了 user_id 的工具。
        skill_dirs: 进入常驻组的技能目录。空则不挂。
        scan_subdir: 是否扫描技能目录的子目录。
        tool_groups: 可开关工具组。空则不注册组开关。

    Returns:
        Toolkit。
    """
    loaders = [
        LocalSkillLoader(directory=d, scan_subdir=scan_subdir) for d in (skill_dirs or []) if d
    ]
    return Toolkit(
        tools=[PlatformFunctionTool(s, user_id=user_id) for s in specs],
        skills_or_loaders=loaders,
        tool_groups=tool_groups,
    )
