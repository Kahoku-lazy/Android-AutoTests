"""JWT authentication utilities — shared between Django middleware and AgentScope FastAPI."""
import logging
import time
import uuid
import jwt
from dataclasses import dataclass
from typing import Optional
from django.conf import settings

logger = logging.getLogger(__name__)

_BLACKLIST_PREFIX = "jwt:blacklist:"

# Fallback when Redis is unavailable (dev only)
_memory_blacklist: set[str] = set()
_redis_client = None
_redis_checked = False


@dataclass
class JWTConfig:
    secret: str = ""
    algorithm: str = "HS256"
    access_ttl: int = 3600       # 1 hour
    refresh_ttl: int = 604800    # 7 days

    def __post_init__(self):
        if not self.secret:
            self.secret = getattr(settings, 'SECRET_KEY', '') or 'change-me'
        if not getattr(settings, 'DEBUG', True) and self.secret in ('', 'change-me'):
            raise RuntimeError('SECRET_KEY must be set to a non-default value in production')
        self.access_ttl = getattr(settings, 'JWT_ACCESS_TTL', 3600)
        self.refresh_ttl = getattr(settings, 'JWT_REFRESH_TTL', 604800)


def get_config() -> JWTConfig:
    return JWTConfig()


def _get_redis():
    """Return a Redis client or None if unavailable."""
    global _redis_client, _redis_checked
    if _redis_checked:
        return _redis_client or None
    _redis_checked = True
    try:
        import redis
        client = redis.from_url(getattr(settings, 'REDIS_URL', 'redis://localhost:6379/0'),
                                decode_responses=True)
        client.ping()
        _redis_client = client
    except Exception as exc:
        logger.warning('JWT blacklist Redis unavailable, using in-memory fallback: %s', exc)
        _redis_client = None
    return _redis_client


def _blacklist_contains(jti: str) -> bool:
    if not jti:
        return False
    client = _get_redis()
    if client:
        return bool(client.exists(f"{_BLACKLIST_PREFIX}{jti}"))
    return jti in _memory_blacklist


def _blacklist_add(jti: str, ttl_seconds: int):
    if not jti:
        return
    ttl_seconds = max(int(ttl_seconds), 1)
    client = _get_redis()
    if client:
        client.setex(f"{_BLACKLIST_PREFIX}{jti}", ttl_seconds, "1")
    else:
        _memory_blacklist.add(jti)


def create_access_token(user_id: str, extra: Optional[dict] = None) -> str:
    """Create a JWT access token for the given user_id."""
    cfg = get_config()
    now = int(time.time())
    payload = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + cfg.access_ttl,
        "type": "access",
    }
    if extra:
        payload.update(extra)
    return jwt.encode(payload, cfg.secret, algorithm=cfg.algorithm)


def create_refresh_token(user_id: str) -> str:
    """Create a JWT refresh token for the given user_id."""
    cfg = get_config()
    now = int(time.time())
    payload = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + cfg.refresh_ttl,
        "type": "refresh",
    }
    return jwt.encode(payload, cfg.secret, algorithm=cfg.algorithm)


def create_token_pair(user_id: str) -> dict:
    """Generate both access and refresh tokens."""
    return {
        "access_token": create_access_token(user_id),
        "refresh_token": create_refresh_token(user_id),
        "token_type": "bearer",
    }


def decode_token(token: str) -> dict:
    """Decode and return the payload without verifying expiry (for inspection)."""
    cfg = get_config()
    return jwt.decode(token, cfg.secret, algorithms=[cfg.algorithm],
                      options={"verify_exp": False})


def verify_token(token: str, expected_type: Optional[str] = None) -> dict:
    """Verify and decode a JWT token. Raises on invalid/expired/blacklisted."""
    cfg = get_config()

    try:
        unverified = jwt.decode(token, cfg.secret, algorithms=[cfg.algorithm],
                                options={"verify_exp": False})
        jti = unverified.get("jti", "")
        if jti and _blacklist_contains(jti):
            raise jwt.InvalidTokenError("Token has been revoked")
        if expected_type and unverified.get("type") != expected_type:
            raise jwt.InvalidTokenError(f"Invalid token type: expected {expected_type}")
    except jwt.InvalidTokenError:
        raise
    except Exception:
        pass

    payload = jwt.decode(token, cfg.secret, algorithms=[cfg.algorithm],
                         options={"verify_exp": True})
    if expected_type and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Invalid token type: expected {expected_type}")
    return payload


def get_user_id_from_token(token: str) -> str:
    """Extract user_id from a verified access token."""
    payload = verify_token(token, expected_type="access")
    return payload["sub"]


def blacklist_token(token: str):
    """Add token to blacklist by jti claim (for logout)."""
    try:
        cfg = get_config()
        payload = jwt.decode(token, cfg.secret, algorithms=[cfg.algorithm],
                             options={"verify_exp": False})
        jti = payload.get("jti", "")
        if not jti:
            return
        exp = payload.get("exp", 0)
        ttl = max(exp - int(time.time()), 60)
        _blacklist_add(jti, ttl)
    except Exception:
        pass


def is_blacklisted(token: str) -> bool:
    """Check if a token's jti is in the blacklist."""
    try:
        payload = decode_token(token)
        return _blacklist_contains(payload.get("jti", ""))
    except Exception:
        return False
