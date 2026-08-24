"""InProcessPlatformTool — calls Django tool handlers directly in-process.

Replaces the HTTP-based PlatformTool in agentscope_service/tools/platform_tool.py.
AgentScope Agent now runs in the Django process, so tools can call handler functions
directly instead of going through HTTP → tool_gateway → handler.
"""

from __future__ import annotations

import asyncio
import json
import logging

from typing import Any

from agentscope.message import TextBlock, ToolResultState
from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.tool import ToolBase, ToolChunk

from .tool_registry import TOOL_SCHEMAS, resolve

logger = logging.getLogger("ai_assistant.tool")


def _build_input_schema(params: list[dict]) -> dict:
    """Build JSON Schema from params list."""
    if not params:
        return {"type": "object", "properties": {}}
    props = {}
    required = []
    for p in params:
        props[p["name"]] = {
            "type": p["type"],
            "description": p.get("desc", ""),
        }
        if p.get("required"):
            required.append(p["name"])
    schema: dict = {"type": "object", "properties": props}
    if required:
        schema["required"] = required
    return schema


def _make_chunk(text: str, state: ToolResultState = ToolResultState.SUCCESS) -> ToolChunk:
    """Build a ToolChunk — AgentScope 2.0 `call()` returns ToolChunk, not ToolResponse.

    The toolkit appends chunks and assembles the final ToolResponse itself.
    """
    return ToolChunk(content=[TextBlock(text=text)], state=state)


_OUTPUT_LIMIT = 4000


def _truncate(text: str) -> str:
    """超长输出截断并带显式标记（不做无提示静默截断）。"""
    if len(text) <= _OUTPUT_LIMIT:
        return text
    return text[:_OUTPUT_LIMIT] + "…(输出截断)"


def _model_to_dict(item) -> dict:
    """Django model instance → 字段 dict（值 stringify，None → ""）。

    关系字段（``attname != name``，如 ForeignKey.parent 的原始列为 parent_id）
    只输出原始外键 id，**绝不访问相关对象**——避免在事件循环线程触发懒加载
    ORM 查询（SynchronousOnlyOperation）。
    """
    data = {}
    for field in item._meta.fields:
        if field.attname != field.name:
            data[field.name] = getattr(item, field.attname, "")
        else:
            val = getattr(item, field.name)
            data[field.name] = str(val) if val is not None else ""
    return data


def _format_result(result) -> ToolChunk:
    """Format tool result into a ToolChunk for the LLM.

    分支顺序：None/str/bool → dict（JSON 序列化）→ 单模型实例（字段 dict）
    → list（模型实例逐项 dict）→ 兜底 str。所有输出截断 4000 字符（带标记）。
    """
    if result is None:
        return _make_chunk("操作完成，无返回数据。")
    if isinstance(result, str):
        return _make_chunk(_truncate(result))
    if isinstance(result, bool):
        return _make_chunk("操作成功。" if result else "操作失败。")
    if isinstance(result, dict):
        return _make_chunk(_truncate(json.dumps(result, ensure_ascii=False, default=str)))
    if hasattr(result, "__dict__") and hasattr(result, "_meta"):
        # 单模型实例（如 get_case 等详情工具）— 序列化为字段 dict
        try:
            return _make_chunk(_truncate(json.dumps(_model_to_dict(result), ensure_ascii=False)))
        except Exception:
            return _make_chunk(_truncate(str(result)))
    if isinstance(result, list):
        if not result:
            return _make_chunk("查询结果为空。")
        # Serialize Django model instances to dicts for clean output
        items = []
        for item in result:
            if hasattr(item, "__dict__") and hasattr(item, "_meta"):
                # Django model instance — extract field values
                try:
                    items.append(_model_to_dict(item))
                except Exception:
                    items.append(str(item))
            elif isinstance(item, dict):
                items.append(item)
            else:
                items.append(str(item))
        return _make_chunk(_truncate(json.dumps(items, ensure_ascii=False, default=str)))
    return _make_chunk(_truncate(str(result)))


class InProcessPlatformTool(ToolBase):
    """Platform tool that calls Django handler functions directly in-process.

    Each instance wraps a single tool definition from tool_registry.TOOL_SCHEMAS.
    At call time, it resolves the handler via tool_registry.resolve() and
    calls it directly — no HTTP round-trip needed.
    """

    def __init__(
        self, tool_config: dict[str, Any], user_id: str = "", knowledge_sources: list | None = None
    ):
        self._config = tool_config
        self._user_id = user_id
        self._knowledge_sources = knowledge_sources or []

    @property
    def name(self) -> str:
        return self._config["name"]

    @property
    def description(self) -> str:
        return self._config.get("summary", "")

    @property
    def input_schema(self) -> dict:
        return _build_input_schema(self._config.get("params", []))

    @property
    def is_read_only(self) -> bool:
        return self._config.get("read_only", True)

    @property
    def is_concurrency_safe(self) -> bool:
        return self._config.get("read_only", True)

    async def check_permissions(self, tool_input, context):
        """Read-only tools always allowed; write tools require authenticated user.

        AgentScope 2.0 expects a :class:`PermissionDecision` with a
        ``behavior`` field — returning a bare bool crashes the agent loop
        with ``AttributeError: 'bool' object has no attribute 'behavior'``.
        """
        if self.is_read_only:
            return PermissionDecision(
                behavior=PermissionBehavior.ALLOW,
                message="只读平台工具，直接放行",
            )
        if self._user_id:
            return PermissionDecision(
                behavior=PermissionBehavior.ALLOW,
                message=f"已认证用户 {self._user_id}",
            )
        return PermissionDecision(
            behavior=PermissionBehavior.DENY,
            message="写工具需要已认证用户",
        )

    async def call(self, **kwargs) -> ToolChunk:
        """Execute the tool by calling the Django handler directly.

        Since handlers in tool_registry.py are synchronous (ORM access),
        we run them in a thread to avoid blocking the async event loop.
        """
        module = self._config["module"]
        action = self._config["action"]
        handler = resolve(module, action)

        if handler is None:
            return _make_chunk(
                f"工具执行失败 [{self.name}]: 未找到处理器 {module}/{action}",
                state=ToolResultState.ERROR,
            )

        # Strip internal fields
        params = {k: v for k, v in kwargs.items() if k not in ("user_id",)}

        # Inject knowledge_sources for search_knowledge_base
        if self._config.get("name") == "search_knowledge_base" and self._knowledge_sources:
            params["sources"] = self._knowledge_sources

        try:
            # Run sync handler in thread to avoid blocking the event loop
            result = await asyncio.to_thread(handler, self._user_id, **params)
        except ValueError as e:
            return _make_chunk(
                f"工具参数错误 [{self.name}]: {e}",
                state=ToolResultState.ERROR,
            )
        except Exception as e:
            logger.exception("Tool %s failed", self.name)
            return _make_chunk(
                f"工具执行失败 [{self.name}]: {e}",
                state=ToolResultState.ERROR,
            )

        return _format_result(result)


def build_platform_tools(
    user_id: str = "",
    enabled_names: set[str] | None = None,
    knowledge_sources: list | None = None,
) -> list[InProcessPlatformTool]:
    """Build InProcessPlatformTool instances for enabled platform tools.

    Args:
        user_id: The authenticated user ID for permission checks.
        enabled_names: Set of tool names to enable. If None, all tools are built
                       (caller should filter with capability flags first).
        knowledge_sources: List of enabled document IDs for RAG filtering.

    Returns:
        List of InProcessPlatformTool instances.
    """
    tools = []
    for schema in TOOL_SCHEMAS:
        if enabled_names is not None and schema["name"] not in enabled_names:
            continue
        tool = InProcessPlatformTool(
            tool_config=schema,
            user_id=user_id,
            knowledge_sources=knowledge_sources,
        )
        tools.append(tool)
    return tools
