"""InProcessPlatformTool — calls Django tool handlers directly in-process.

Replaces the HTTP-based PlatformTool in agentscope_service/tools/platform_tool.py.
AgentScope Agent now runs in the Django process, so tools can call handler functions
directly instead of going through HTTP → tool_gateway → handler.
"""

from __future__ import annotations

import asyncio
import logging

from typing import Any

from agentscope.tool import ToolBase, ToolResponse

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


def _format_result(result) -> ToolResponse:
    """Format tool result into a ToolResponse for the LLM."""
    if result is None:
        return ToolResponse(content="操作完成，无返回数据。")
    if isinstance(result, str):
        return ToolResponse(content=result)
    if isinstance(result, bool):
        return ToolResponse(content="操作成功。" if result else "操作失败。")
    if isinstance(result, list):
        if not result:
            return ToolResponse(content="查询结果为空。")
        # Serialize Django model instances to dicts for clean output
        items = []
        for item in result:
            if hasattr(item, "__dict__") and hasattr(item, "_meta"):
                # Django model instance — extract field values
                try:
                    data = {}
                    for field in item._meta.fields:
                        val = getattr(item, field.name)
                        data[field.name] = str(val) if val is not None else ""
                    items.append(data)
                except Exception:
                    items.append(str(item))
            elif isinstance(item, dict):
                items.append(item)
            else:
                items.append(str(item))
        import json

        return ToolResponse(content=json.dumps(items, ensure_ascii=False, default=str)[:4000])
    return ToolResponse(content=str(result)[:4000])


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
        """Read-only tools always allowed; write tools require authenticated user."""
        if self.is_read_only:
            return True
        return bool(self._user_id)

    async def call(self, **kwargs) -> ToolResponse:
        """Execute the tool by calling the Django handler directly.

        Since handlers in tool_registry.py are synchronous (ORM access),
        we run them in a thread to avoid blocking the async event loop.
        """
        module = self._config["module"]
        action = self._config["action"]
        handler = resolve(module, action)

        if handler is None:
            return ToolResponse(
                content=f"工具执行失败 [{self.name}]: 未找到处理器 {module}/{action}",
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
            return ToolResponse(content=f"工具参数错误 [{self.name}]: {e}")
        except Exception as e:
            logger.exception("Tool %s failed", self.name)
            return ToolResponse(content=f"工具执行失败 [{self.name}]: {e}")

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
