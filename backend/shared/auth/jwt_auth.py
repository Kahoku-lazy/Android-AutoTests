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
    pass


@dataclass
class JWTConfig:
    secret: str = ""
    algorithm: str = "HS256"
    access_ttl: int = 3600
    refresh_ttl: int = 604800

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
    from backend.apps.accounts import api as accounts_api

    return accounts_api


def _is_revoked(jti: str = "", sid: str = "", user_id: str = "", issued_at: int = 0) -> bool:
    if not jti and not sid and not user_id:
        return False
    try:
        store = _revocation_store()
        if (jti or sid) and store.is_revoked(sid=sid, jti=jti):
            return True
        if user_id and store.user_revoked_before(int(user_id), int(issued_at or 0)):
            return True
        return False
    except (DatabaseError, TypeError, ValueError) as exc:
        logger.error("JWT 吊销：查询吊销记录失败，放行 token: %s", exc)
        return False


def _revocation_add(kind: str, ref: str, ttl_seconds: int) -> None:
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
    if not jti:
        return
    _revocation_add(_REVOCATION_KIND_TOKEN, jti, ttl_seconds)


def _session_add(sid: str, ttl_seconds: int):
    if not sid:
        return
    _revocation_add(_REVOCATION_KIND_SESSION, sid, ttl_seconds)


def create_access_token(
    user_id: str, extra: Optional[dict] = None, sid: Optional[str] = None
) -> str:
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
    sid = str(uuid.uuid4())
    return {
        "access_token": create_access_token(user_id, sid=sid),
        "refresh_token": create_refresh_token(user_id, sid=sid),
        "token_type": "bearer",
    }


def verify_token(token: str, expected_type: Optional[str] = None) -> dict:
    cfg = get_config()

    unverified = jwt.decode(
        token, cfg.secret, algorithms=[cfg.algorithm], options={"verify_exp": False}
    )
    jti = unverified.get("jti", "")
    sid = unverified.get("sid", "")
    if _is_revoked(jti, sid, unverified.get("sub", ""), unverified.get("iat", 0)):
        raise jwt.InvalidTokenError("Token has been revoked")
    if expected_type and unverified.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Invalid token type: expected {expected_type}")

    payload = jwt.decode(
        token, cfg.secret, algorithms=[cfg.algorithm], options={"verify_exp": True}
    )
    if expected_type and payload.get("type") != expected_type:
        raise jwt.InvalidTokenError(f"Invalid token type: expected {expected_type}")
    if not payload.get("sub"):
        raise jwt.InvalidTokenError("Token missing sub claim")
    return payload


def get_user_id_from_token(token: str) -> str:
    payload = verify_token(token, expected_type="access")
    return payload["sub"]


def revoke_session(sid: str, ttl_seconds: Optional[int] = None):
    if not sid:
        return
    ttl = get_config().refresh_ttl if ttl_seconds is None else ttl_seconds
    _session_add(sid, ttl)


def session_id_of(token: str) -> str:
    cfg = get_config()
    try:
        payload = jwt.decode(
            token, cfg.secret, algorithms=[cfg.algorithm], options={"verify_exp": False}
        )
    except Exception:
        return ""
    return payload.get("sid", "")


def blacklist_token(token: str):
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
