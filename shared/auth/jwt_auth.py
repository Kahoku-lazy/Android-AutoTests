"""JWT authentication utilities — shared between Django middleware and AgentScope FastAPI."""

import logging
import time
import uuid

from dataclasses import dataclass
from typing import Optional

import jwt

from django.conf import settings

logger = logging.getLogger(__name__)

_BLACKLIST_PREFIX = "jwt:blacklist:"

# Redis client — cached after first successful connection.
# Never caches failures, so it auto-recovers when Redis comes back.
_redis_client = None


class BlacklistUnavailableError(RuntimeError):
    """Raised when a blacklist operation fails because Redis is unavailable.

    This is a deliberate hard-fail: without Redis, we cannot reliably
    persist token revocations.  Accepting a logout and storing the
    revocation in memory would mean revoked tokens become valid again
    after a service restart — a security regression.
    """


@dataclass
class JWTConfig:
    secret: str = ""
    algorithm: str = "HS256"
    access_ttl: int = 3600  # 1 hour
    refresh_ttl: int = 604800  # 7 days

    def __post_init__(self):
        if not self.secret:
            self.secret = getattr(settings, "SECRET_KEY", "") or "change-me"
        if not getattr(settings, "DEBUG", True) and self.secret in ("", "change-me"):
            raise RuntimeError("SECRET_KEY must be set to a non-default value in production")
        self.access_ttl = getattr(settings, "JWT_ACCESS_TTL", 3600)
        self.refresh_ttl = getattr(settings, "JWT_REFRESH_TTL", 604800)


def get_config() -> JWTConfig:
    return JWTConfig()


def _get_redis():
    """Return a Redis client or None if unavailable.

    Successful connections are cached for reuse.  Failures are never
    cached, so the next call will retry — this allows the blacklist to
    recover automatically once Redis is available again.
    """
    global _redis_client
    if _redis_client is not None:
        try:
            _redis_client.ping()
            return _redis_client
        except Exception:
            logger.warning("JWT blacklist: cached Redis connection lost, reconnecting")
            _redis_client = None
    try:
        import redis

        client = redis.from_url(
            getattr(settings, "REDIS_URL", "redis://localhost:6379/0"),
            decode_responses=True,
            socket_connect_timeout=3,
        )
        client.ping()
        _redis_client = client
        return client
    except Exception as exc:
        logger.error(
            "JWT blacklist: Redis 不可用，Token 黑名单操作将失败。"
            "请启动 Redis: redis-server --port %s。错误: %s",
            getattr(settings, "REDIS_PORT", 6379),
            exc,
        )
        return None


def _blacklist_contains(jti: str) -> bool:
    """Check whether *jti* is in the blacklist.

    When Redis is unavailable we log an error and return ``False``
    (allow the token).  This is the safer default: rejecting every
    token when the blacklist is unreachable would lock all users out.
    """
    if not jti:
        return False
    client = _get_redis()
    if client:
        try:
            return bool(client.exists(f"{_BLACKLIST_PREFIX}{jti}"))
        except Exception as exc:
            logger.error("JWT blacklist: exists() 失败: %s", exc)
            return False
    logger.error("JWT blacklist: 无法检查黑名单（Redis 不可用），放行 token")
    return False


def _blacklist_add(jti: str, ttl_seconds: int):
    """Add *jti* to the blacklist with the given TTL.

    Raises :class:`BlacklistUnavailableError` when Redis is
    unavailable — we refuse to perform a logout that would be silently
    undone on the next service restart.
    """
    if not jti:
        return
    ttl_seconds = max(int(ttl_seconds), 1)
    client = _get_redis()
    if client:
        try:
            client.setex(f"{_BLACKLIST_PREFIX}{jti}", ttl_seconds, "1")
        except Exception as exc:
            raise BlacklistUnavailableError(f"Redis 写入黑名单失败: {exc}") from exc
    else:
        raise BlacklistUnavailableError(
            "Redis 不可用，无法将 Token 加入黑名单。请检查 Redis 服务状态后重试登出。"
        )


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
    return jwt.decode(token, cfg.secret, algorithms=[cfg.algorithm], options={"verify_exp": False})


def verify_token(token: str, expected_type: Optional[str] = None) -> dict:
    """Verify and decode a JWT token. Raises on invalid/expired/blacklisted."""
    cfg = get_config()

    try:
        unverified = jwt.decode(
            token, cfg.secret, algorithms=[cfg.algorithm], options={"verify_exp": False}
        )
        jti = unverified.get("jti", "")
        if jti and _blacklist_contains(jti):
            raise jwt.InvalidTokenError("Token has been revoked")
        if expected_type and unverified.get("type") != expected_type:
            raise jwt.InvalidTokenError(f"Invalid token type: expected {expected_type}")
    except jwt.InvalidTokenError:
        raise
    except Exception:
        pass

    payload = jwt.decode(
        token, cfg.secret, algorithms=[cfg.algorithm], options={"verify_exp": True}
    )
    if expected_type and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Invalid token type: expected {expected_type}")
    return payload


def get_user_id_from_token(token: str) -> str:
    """Extract user_id from a verified access token."""
    payload = verify_token(token, expected_type="access")
    return payload["sub"]


def blacklist_token(token: str):
    """Add token to blacklist by jti claim (for logout).

    Raises :class:`BlacklistUnavailableError` if Redis is unavailable.
    The caller (logout view) should catch this and return a 503 response
    so the user knows to retry.
    """
    cfg = get_config()
    payload = jwt.decode(
        token, cfg.secret, algorithms=[cfg.algorithm], options={"verify_exp": False}
    )
    jti = payload.get("jti", "")
    if not jti:
        return
    exp = payload.get("exp", 0)
    ttl = max(exp - int(time.time()), 60)
    _blacklist_add(jti, ttl)


def is_blacklisted(token: str) -> bool:
    """Check if a token's jti is in the blacklist."""
    try:
        payload = decode_token(token)
        return _blacklist_contains(payload.get("jti", ""))
    except Exception:
        return False
