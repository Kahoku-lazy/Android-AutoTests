"""Tool factory — builds the tool list for AgentScope sessions via HTTP.

At startup, fetches tool schemas from Django GET /api/tools/schemas.
At session creation, fetches per-agent config from Django and filters tools.

AgentScope NEVER imports Django modules or accesses the database directly.
All platform data comes through the /api/tools/ HTTP gateway.
"""

from __future__ import annotations

import logging
import os

import httpx

from ..auth import get_stored_jwt
from .platform_tool import PlatformTool
from .tool_context import ToolContext

logger = logging.getLogger("agentscope.factory")

_DJANGO_URL = os.environ.get(
    "AGENTSCOPE_DJANGO_URL",
    "http://127.0.0.1:8765",
).rstrip("/")

# ── Schema cache (fetched once, reused across all sessions) ──

_schemas_cache: list[dict] | None = None
_categories_cache: list[dict] | None = None


async def _fetch_schemas() -> list[dict]:
    """Fetch tool schemas from Django. Cached in memory after first call."""
    global _schemas_cache, _categories_cache
    if _schemas_cache is not None:
        return _schemas_cache
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get(f"{_DJANGO_URL}/api/ai/tools/schemas")
            resp.raise_for_status()
            data = resp.json()
            tools = data.get("data", {}).get("tools", [])
            _categories_cache = data.get("data", {}).get("categories", [])
            _schemas_cache = tools
            logger.info("Fetched %d tool schemas from Django", len(tools))
            return tools
    except Exception as e:
        logger.error("Failed to fetch tool schemas from Django: %s", e)
        # Fallback: empty tool list — AgentScope still works, just no business tools
        return []


# ── Dynamic tool class creation ──


def _make_tool_class(config: dict) -> type[PlatformTool]:
    """Create a PlatformTool subclass with the given config baked in."""
    tool_config = dict(config)

    class _Tool(PlatformTool):
        def __init__(self, _c=tool_config):
            super().__init__(_c)

    _Tool.__name__ = f"PlatformTool_{config['name']}"
    _Tool.__qualname__ = _Tool.__name__
    return _Tool


# ── Per-agent config (fetched from Django on each session creation) ──


async def _fetch_agent_config(agent_id: str, session_id: str, jwt: str) -> dict:
    """Fetch agent-specific tool configuration from Django.

    Returns dict with: enabled_tools, disabled_skills, knowledge_sources.
    """
    if not agent_id:
        return {}
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            headers = {"Authorization": f"Bearer {jwt}"} if jwt else {}
            resp = await client.get(
                f"{_DJANGO_URL}/api/ai/tools/agent-config/{agent_id}",
                params={"session_id": session_id},
                headers=headers,
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("data", {})
    except Exception as e:
        logger.debug("Failed to fetch agent config for %s: %s", agent_id, e)
    return {}


# ── Main entry point — called by AgentScope on each session creation ──


async def build_business_tools(user_id: str, agent_id: str, session_id: str) -> list:
    """Build the filtered tool list for the current session.

    Called by AgentScope framework on each new conversation session.
    Returns a list of PlatformTool instances ready for LLM use.
    """
    schemas = await _fetch_schemas()
    jwt = get_stored_jwt()

    # Fetch per-agent enabled/disabled configuration from Django
    agent_config = await _fetch_agent_config(agent_id, session_id, jwt)

    # Determine which tools are enabled
    enabled_names = set(agent_config.get("enabled_tools", [t["name"] for t in schemas]))
    if not enabled_names:
        # No config → expose read-only tools as safety fallback
        enabled_names = {t["name"] for t in schemas if t.get("read_only", True)}

    # Build ToolContext with JWT for downstream HTTP calls
    ctx = ToolContext(
        user_id=str(user_id or ""),
        agent_id=str(agent_id or ""),
        session_id=str(session_id or ""),
        jwt=jwt,
        knowledge_sources=agent_config.get("knowledge_sources", []) or [],
    )

    # Instantiate filtered tools
    tools = []
    for schema in schemas:
        if schema["name"] not in enabled_names:
            continue
        cls = _make_tool_class(schema)
        tool = cls()
        tool._ctx = ctx
        tools.append(tool)

    logger.debug(
        "Built %d tools for agent=%s session=%s (enabled=%d of %d schemas)",
        len(tools),
        agent_id,
        session_id,
        len(enabled_names),
        len(schemas),
    )
    return tools
