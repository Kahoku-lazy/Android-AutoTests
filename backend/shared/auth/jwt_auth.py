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
# 会话级吊销：一次登录签发的 access 与 refresh 共享一个 sid，登出按 sid 整组作废
_SESSION_PREFIX = "jwt:session_revoked:"

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


def _is_revoked(jti: str = "", sid: str = "") -> bool:
    """Check whether this token's *jti*, or its session *sid*, has been revoked.

    Both keys go into a single ``EXISTS`` round trip, so session-level revocation
    costs nothing extra on the hot path (``verify_token`` runs on every
    authenticated request).

    When Redis is unavailable we log an error and return ``False``
    (allow the token).  This is the safer default: rejecting every
    token when the revocation store is unreachable would lock all users out.
    """
    keys = []
    if jti:
        keys.append(f"{_BLACKLIST_PREFIX}{jti}")
    if sid:
        keys.append(f"{_SESSION_PREFIX}{sid}")
    if not keys:
        return False
    client = _get_redis()
    if client:
        try:
            return bool(client.exists(*keys))
        except Exception as exc:
            logger.error("JWT blacklist: exists() 失败: %s", exc)
            return False
    logger.error("JWT blacklist: 无法检查黑名单（Redis 不可用），放行 token")
    return False


def _revocation_add(key: str, ttl_seconds: int):
    """Record one revocation entry with the given TTL.

    Raises :class:`BlacklistUnavailableError` when Redis is
    unavailable — we refuse to perform a logout that would be silently
    undone on the next service restart.
    """
    if not key:
        return
    ttl_seconds = max(int(ttl_seconds), 1)
    client = _get_redis()
    if client:
        try:
            # set(..., ex=) 取代已废弃的 setex（redis-py 标记 deprecated 起）
            client.set(key, "1", ex=ttl_seconds)
        except Exception as exc:
            raise BlacklistUnavailableError(f"Redis 写入黑名单失败: {exc}") from exc
    else:
        raise BlacklistUnavailableError(
            "Redis 不可用，无法将 Token 加入黑名单。请检查 Redis 服务状态后重试登出。"
        )


def _blacklist_add(jti: str, ttl_seconds: int):
    """按单个令牌（jti）吊销 —— 供没有 sid 的历史令牌兜底。"""
    if not jti:
        return
    _revocation_add(f"{_BLACKLIST_PREFIX}{jti}", ttl_seconds)


def _session_add(sid: str, ttl_seconds: int):
    """按会话（sid）吊销 —— 同一次登录的 access 与 refresh 一起失效。"""
    if not sid:
        return
    _revocation_add(f"{_SESSION_PREFIX}{sid}", ttl_seconds)


def create_access_token(
    user_id: str, extra: Optional[dict] = None, sid: Optional[str] = None
) -> str:
    """Create a JWT access token for the given user_id.

    *sid* is the session id: when present, this token is revoked together with
    the rest of its session (see :func:`revoke_session`).
    """
    cfg = get_config()
    now = int(time.time())
    payload = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + cfg.access_ttl,
        "type": "access",
    }
    if sid:
        payload["sid"] = sid
    if extra:
        payload.update(extra)
    return jwt.encode(payload, cfg.secret, algorithm=cfg.algorithm)


def create_refresh_token(user_id: str, sid: Optional[str] = None) -> str:
    """Create a JWT refresh token for the given user_id, sharing its session *sid*."""
    cfg = get_config()
    now = int(time.time())
    payload = {
        "sub": user_id,
        "jti": str(uuid.uuid4()),
        "iat": now,
        "exp": now + cfg.refresh_ttl,
        "type": "refresh",
    }
    if sid:
        payload["sid"] = sid
    return jwt.encode(payload, cfg.secret, algorithm=cfg.algorithm)


def create_token_pair(user_id: str) -> dict:
    """Generate both access and refresh tokens sharing one session id.

    The returned keys are deliberately unchanged: *sid* lives inside the tokens
    only, so the API response shape (and the frontend) stay untouched.
    """
    sid = str(uuid.uuid4())
    return {
        "access_token": create_access_token(user_id, sid=sid),
        "refresh_token": create_refresh_token(user_id, sid=sid),
        "token_type": "bearer",
    }


def verify_token(token: str, expected_type: Optional[str] = None) -> dict:
    """Verify and decode a JWT token. Raises on invalid/expired/blacklisted."""
    cfg = get_config()

    # 预检：吊销（jti 单令牌 / sid 整会话）与类型。此处**不再兜底吞异常**——任何意外异常都上抛，
    # 由上游（gateway 中间件 / DRF 认证类）统一转 401（fail-closed）。
    unverified = jwt.decode(
        token, cfg.secret, algorithms=[cfg.algorithm], options={"verify_exp": False}
    )
    jti = unverified.get("jti", "")
    sid = unverified.get("sid", "")
    if _is_revoked(jti, sid):
        raise jwt.InvalidTokenError("Token has been revoked")
    if expected_type and unverified.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Invalid token type: expected {expected_type}")

    payload = jwt.decode(
        token, cfg.secret, algorithms=[cfg.algorithm], options={"verify_exp": True}
    )
    if expected_type and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Invalid token type: expected {expected_type}")
    if not payload.get("sub"):
        # 不变量：通过校验的令牌必有 sub —— 四个调用点（中间件 / DRF 认证 / RefreshView /
        # get_user_id_from_token）都用 payload["sub"] 取值，缺 sub 必须 401 而不是 500
        raise jwt.InvalidTokenError("Token missing sub claim")
    return payload


def get_user_id_from_token(token: str) -> str:
    """Extract user_id from a verified access token."""
    payload = verify_token(token, expected_type="access")
    return payload["sub"]


def revoke_session(sid: str, ttl_seconds: Optional[int] = None):
    """Revoke a whole login session: its access *and* its refresh token.

    The TTL defaults to ``JWT_REFRESH_TTL`` rather than the access token's
    remaining life.  Logout is called with an access token (1h), but the same
    session's refresh token lives up to ``refresh_ttl`` (7d); a shorter TTL would
    let the refresh token become usable again once the entry expires.

    Raises :class:`BlacklistUnavailableError` when Redis is unavailable.
    """
    if not sid:
        return
    ttl = get_config().refresh_ttl if ttl_seconds is None else ttl_seconds
    _session_add(sid, ttl)


def session_id_of(token: str) -> str:
    """Read the ``sid`` claim without verifying signature or expiry.

    Callers (logout) sit behind an authentication layer that already verified
    the token; this only needs to extract the session id, and returns "" when
    the token is unreadable or predates session ids.
    """
    cfg = get_config()
    try:
        payload = jwt.decode(
            token, cfg.secret, algorithms=[cfg.algorithm], options={"verify_exp": False}
        )
    except Exception:
        return ""
    return payload.get("sid", "")


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
