"""AgentScope FastAPI application — main entry point for the Agent Service.

Creates a FastAPI app via agentscope.create_app() with:
- Redis storage + message bus
- Local workspace manager
- JWT authentication via dependency override
- Custom business tools via extra_agent_tools factory
- Sub-agent team templates
"""
import logging
from pathlib import Path

from agentscope.app import create_app
from agentscope.app.storage import RedisStorage
from agentscope.app.message_bus import RedisMessageBus
from agentscope.app.workspace_manager import LocalWorkspaceManager

from config.agentscope_config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB,
    TITLE, VERSION,
    WORKSPACE_DIR, WORKSPACE_TTL,
    SKILL_PATHS,
)
from .auth import get_current_user_id
from .tools.factory import build_business_tools
from .teams.templates import SUB_AGENT_TEMPLATES

logger = logging.getLogger('agentscope')


def create_agentscope_app():
    """Create and return the AgentScope FastAPI application."""

    # ── Storage (Redis) ──
    storage = RedisStorage(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
    )

    # ── Message Bus (Redis) ──
    message_bus = RedisMessageBus(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
    )

    # ── Workspace Manager (Local filesystem) ──
    WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
    workspace_manager = LocalWorkspaceManager(
        basedir=str(WORKSPACE_DIR),
        skill_paths=SKILL_PATHS,
        ttl=WORKSPACE_TTL,
    )

    # ── Build the app ──
    app = create_app(
        storage=storage,
        message_bus=message_bus,
        workspace_manager=workspace_manager,
        extra_agent_tools=build_business_tools,
        custom_subagent_templates=SUB_AGENT_TEMPLATES,
        title=TITLE,
        version=VERSION,
    )

    # ── Override authentication ──
    # Replace AgentScope's default X-User-ID dependency with JWT verification
    from agentscope.app.deps import get_current_user_id as default_dep
    app.dependency_overrides[default_dep] = get_current_user_id

    logger.info(f'AgentScope app created: {TITLE} v{VERSION}')
    logger.info(f'  Redis: {REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}')
    logger.info(f'  Workspace: {WORKSPACE_DIR}')
    logger.info(f'  Sub-agent templates: {[t.type for t in SUB_AGENT_TEMPLATES]}')

    return app
