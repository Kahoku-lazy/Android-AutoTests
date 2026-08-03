"""PlatformTool — generic HTTP-based platform tool class.

Every platform business tool is a PlatformTool subclass. Tool behaviour is
defined by the tool registry served by Django at GET /api/tools/schemas.

At call time, PlatformTool POSTs to Django's /api/tools/{module}/{action}
gateway with the JWT token for authentication. AgentScope NEVER imports
Django modules or accesses the database directly.
"""

from __future__ import annotations

# Django backend URL for tool gateway calls.
# Defaults to localhost; override via AGENTSCOPE_DJANGO_URL env or settings.
import os

import httpx

from agentscope.message import TextBlock
from agentscope.tool import ToolBase, ToolChunk

_DJANGO_URL = os.environ.get(
    "AGENTSCOPE_DJANGO_URL",
    "http://127.0.0.1:8765",
).rstrip("/")

_TOOL_TIMEOUT = 30  # seconds — covers slow ops like test execution


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
    schema: dict = {
        "type": "object",
        "properties": props,
    }
    if required:
        schema["required"] = required
    return schema


class PlatformTool(ToolBase):
    """Generic platform tool — routes calls to Django via HTTP.

    Each instance is configured with a tool definition dict (from Django's
    /api/tools/schemas endpoint) containing:
      - name, summary, category, icon
      - module  (e.g. "devices")
      - action  (e.g. "acquire")
      - params  (list of param definitions)
      - read_only (bool)
    """

    def __init__(self, tool_config: dict):
        self._config = tool_config

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
        from .tool_context import check_platform_permission

        return check_platform_permission(self)

    async def call(self, **kwargs):
        """Execute the tool by POSTing to Django's /api/tools/ gateway.

        Args:
            **kwargs: Tool parameters matching the schema.

        Returns:
            ToolChunk with the result text.
        """
        module = self._config["module"]
        action = self._config["action"]
        url = f"{_DJANGO_URL}/api/ai/tools/{module}/{action}"

        ctx = getattr(self, "_ctx", None)
        headers = {}
        jwt = getattr(ctx, "jwt", "") if ctx else ""
        if jwt:
            headers["Authorization"] = f"Bearer {jwt}"

        # Strip internal fields from kwargs
        body = {k: v for k, v in kwargs.items() if k not in ("user_id",)}

        # Inject knowledge_sources into search_knowledge_base calls
        if self._config.get("name") == "search_knowledge_base" and ctx:
            kbs = getattr(ctx, "knowledge_sources", None)
            if kbs:
                body["sources"] = kbs

        try:
            async with httpx.AsyncClient(timeout=_TOOL_TIMEOUT) as client:
                resp = await client.post(url, json=body, headers=headers)
                resp.raise_for_status()
                data = resp.json()
        except httpx.HTTPStatusError as e:
            return ToolChunk(
                content=[
                    TextBlock(text=f"工具执行失败 [{self.name}]: HTTP {e.response.status_code}")
                ]
            )
        except httpx.RequestError as e:
            return ToolChunk(
                content=[TextBlock(text=f"工具执行失败 [{self.name}]: 无法连接后端服务 ({e})")]
            )

        # Extract result from Django's {ok, data/error} envelope
        if isinstance(data, dict):
            if not data.get("ok", True):
                return ToolChunk(
                    content=[
                        TextBlock(
                            text=f"工具执行失败 [{self.name}]: {data.get('error', 'unknown error')}"
                        )
                    ]
                )
            result = data.get("data")
        else:
            result = data

        # Format result for LLM consumption
        return _format_result(result)


def _format_result(result) -> ToolChunk:
    """Format tool result into a ToolChunk for the LLM."""
    if result is None:
        return ToolChunk(content=[TextBlock(text="操作完成，无返回数据。")])
    if isinstance(result, str):
        return ToolChunk(content=[TextBlock(text=result)])
    if isinstance(result, bool):
        return ToolChunk(content=[TextBlock(text="操作成功。" if result else "操作失败。")])
    if isinstance(result, list):
        if not result:
            return ToolChunk(content=[TextBlock(text="查询结果为空。")])
        return ToolChunk(content=[TextBlock(text=str(result)[:4000])])
    return ToolChunk(content=[TextBlock(text=str(result)[:4000])])
