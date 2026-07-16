"""AgentScope 2.0 service configuration — shared settings for the FastAPI agent service."""
import os
from pathlib import Path
from django.conf import settings

# ── Redis (shared with Django Channels) ──
REDIS_HOST = getattr(settings, 'REDIS_HOST', 'localhost')
REDIS_PORT = getattr(settings, 'REDIS_PORT', 6379)
REDIS_URL = getattr(settings, 'REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
REDIS_DB = int(os.environ.get('AGENTSCOPE_REDIS_DB', '1'))  # separate DB from Channels

# ── Service ──
HOST = os.environ.get('AGENTSCOPE_HOST', '127.0.0.1')
PORT = getattr(settings, 'AGENTSCOPE_SERVICE_PORT', 8000)
TITLE = getattr(settings, 'AGENTSCOPE_SERVICE_TITLE', 'Android-AutoTests Agent Service')
VERSION = getattr(settings, 'AGENTSCOPE_SERVICE_VERSION', '2.0.0')

# ── Workspace ──
WORKSPACE_DIR = Path(getattr(settings, 'AGENTSCOPE_WORKSPACE_DIR', 'data/agentscope_workspaces'))
WORKSPACE_TTL = float(os.environ.get('AGENTSCOPE_WORKSPACE_TTL', '3600'))  # 1 hour idle timeout

# JWT: use shared.auth.jwt_auth (verify_token / get_config) — do not duplicate secrets here.

# ── Tools ──
# Additional skill / MCP directories to pre-load into workspaces
SKILL_PATHS = [
    str(Path(__file__).resolve().parent.parent / 'agentscope_service' / 'skills'),
]
