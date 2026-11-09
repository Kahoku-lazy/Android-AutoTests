"""JWT authentication utilities — shared between Django middleware and AgentScope FastAPI."""

import logging
import time
import uuid

from dataclasses import dataclass
from typing import Optional

import jwt

from django.conf import settings
from django.db import DatabaseError

logger = logging.getLogger(__name__)

_REVOCATION_KIND_SESSION = "session"
_REVOCATION_KIND_TOKEN = "token"


class BlacklistUnavailableError(RuntimeError):
    """Raised when a revocation record cannot be written (store unavailable).

    This is a deliberate hard-fail: without a durable revocation store we
    cannot promise that a logout sticks.  Accepting a logout and keeping the
    revocation in memory would mean revoked tokens become valid again after a
    service restart — a security regression.
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


def _revocation_store():
    """返回吊销存储的读写口（`apps.accounts.api`）。

    惰性导入：`apps.accounts.views` 会 import 本模块，模块级反向 import 会成环。
    """
    from backend.apps.accounts import api as accounts_api

    return accounts_api


def _is_revoked(jti: str = "", sid: str = "") -> bool:
    """Check whether this token's *jti*, or its session *sid*, has been revoked.

    Both identifiers are resolved in a single query, so session-level revocation
    costs nothing extra on the hot path (``verify_token`` runs on every
    authenticated request).

    When the revocation store is unreachable we log an error and return ``False``
    (allow the token).  This is the safer default: rejecting every
    token when the revocation store hiccups would lock all users out.
    """
    if not jti and not sid:
        return False
    try:
        return _revocation_store().is_revoked(sid=sid, jti=jti)
    except DatabaseError as exc:
        logger.error("JWT 吊销：查询吊销记录失败，放行 token: %s", exc)
        return False


def _revocation_add(kind: str, ref: str, ttl_seconds: int) -> None:
    """Record one revocation entry with the given TTL.

    Raises :class:`BlacklistUnavailableError` when the store is
    unavailable — we refuse to perform a logout that would be silently
    undone on the next service restart.

    Args:
        kind: ``session``（按会话）或 ``token``（按单令牌）。
        ref: 会话标识或令牌标识。
        ttl_seconds: 记录有效期（秒）。
    """
    if not ref:
        return
    store = _revocation_store()
    try:
        if kind == _REVOCATION_KIND_SESSION:
            store.revoke_session(ref, ttl_seconds)
        else:
            store.revoke_token(ref, ttl_seconds)
    except DatabaseError as exc:
        raise BlacklistUnavailableError(f"吊销记录写入失败: {exc}") from exc


def _blacklist_add(jti: str, ttl_seconds: int):
    """按单个令牌（jti）吊销 —— 供没有 sid 的历史令牌兜底。"""
    if not jti:
        return
    _revocation_add(_REVOCATION_KIND_TOKEN, jti, ttl_seconds)


def _session_add(sid: str, ttl_seconds: int):
    """按会话（sid）吊销 —— 同一次登录的 access 与 refresh 一起失效。"""
    if not sid:
        return
    _revocation_add(_REVOCATION_KIND_SESSION, sid, ttl_seconds)


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

    Raises :class:`BlacklistUnavailableError` when the revocation store is unavailable.
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

    Raises :class:`BlacklistUnavailableError` if the revocation store is unavailable.
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
