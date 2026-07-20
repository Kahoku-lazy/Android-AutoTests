"""AgentScope 2.0 service configuration — shared settings for the FastAPI agent service."""
import logging
import os
from pathlib import Path
from django.conf import settings

logger = logging.getLogger('agentscope.config')

# ── Redis (shared with Django Channels) ──
REDIS_HOST = getattr(settings, 'REDIS_HOST', 'localhost')
REDIS_PORT = getattr(settings, 'REDIS_PORT', 6379)
REDIS_URL = getattr(settings, 'REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/0')
REDIS_DB = int(os.environ.get('AGENTSCOPE_REDIS_DB', '1'))  # separate DB from Channels


def check_redis_connection(host=None, port=None, db=None):
    """Test Redis connectivity with a PING.

    Returns (True, None) on success, (False, error_message) on failure.
    Used by AgentScope startup to fail fast with a clear message
    instead of crashing mid-init.
    """
    import redis
    from redis.exceptions import ConnectionError as RedisConnectionError
    h = host or REDIS_HOST
    p = port or REDIS_PORT
    d = db if db is not None else REDIS_DB
    try:
        r = redis.Redis(host=h, port=p, db=d, socket_connect_timeout=3)
        if r.ping():
            return True, None
        return False, f'Redis PING returned falsy at {h}:{p}/{d}'
    except RedisConnectionError as e:
        msg = f'无法连接到 Redis ({h}:{p}/{d}): {e}'
        logger.error(msg)
        return False, msg
    except Exception as e:
        msg = f'Redis 连接异常 ({h}:{p}/{d}): {type(e).__name__}: {e}'
        logger.error(msg)
        return False, msg

# ── Service ──
HOST = os.environ.get('AGENTSCOPE_HOST', '127.0.0.1')
PORT = getattr(settings, 'AGENTSCOPE_SERVICE_PORT', 8088)
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
