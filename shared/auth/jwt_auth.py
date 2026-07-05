"""JWT authentication utilities — shared between Django middleware and AgentScope FastAPI."""
import time
import jwt
from dataclasses import dataclass
from typing import Optional
from django.conf import settings


@dataclass
class JWTConfig:
    secret: str = ""
    algorithm: str = "HS256"
    access_ttl: int = 3600       # 1 hour
    refresh_ttl: int = 604800    # 7 days

    def __post_init__(self):
        if not self.secret:
            self.secret = getattr(settings, 'SECRET_KEY', 'change-me')
        self.access_ttl = getattr(settings, 'JWT_ACCESS_TTL', 3600)
        self.refresh_ttl = getattr(settings, 'JWT_REFRESH_TTL', 604800)


# Shared blacklist — in production, use Redis
_token_blacklist: set[str] = set()


def get_config() -> JWTConfig:
    return JWTConfig()


def create_access_token(user_id: str, extra: Optional[dict] = None) -> str:
    """Create a JWT access token for the given user_id."""
    cfg = get_config()
    now = int(time.time())
    payload = {
        "sub": user_id,
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


def verify_token(token: str) -> dict:
    """Verify and decode a JWT token. Raises on invalid/expired/blacklisted."""
    cfg = get_config()

    # Check blacklist
    try:
        unverified = jwt.decode(token, cfg.secret, algorithms=[cfg.algorithm],
                                options={"verify_exp": False})
        jti = unverified.get("jti", "")
        if jti and jti in _token_blacklist:
            raise jwt.InvalidTokenError("Token has been revoked")
    except jwt.InvalidTokenError:
        raise
    except Exception:
        pass

    # Full verification (includes expiry check)
    payload = jwt.decode(token, cfg.secret, algorithms=[cfg.algorithm],
                         options={"verify_exp": True})
    return payload


def get_user_id_from_token(token: str) -> str:
    """Extract user_id from a verified token."""
    payload = verify_token(token)
    return payload["sub"]


def blacklist_token(token: str):
    """Add token to blacklist by jti claim (for logout)."""
    try:
        cfg = get_config()
        payload = jwt.decode(token, cfg.secret, algorithms=[cfg.algorithm],
                             options={"verify_exp": False})
        jti = payload.get("jti", "")
        if jti:
            _token_blacklist.add(jti)
    except Exception:
        pass


def is_blacklisted(token: str) -> bool:
    """Check if a token's jti is in the blacklist."""
    try:
        cfg = get_config()
        payload = jwt.decode(token, cfg.secret, algorithms=[cfg.algorithm],
                             options={"verify_exp": False})
        return payload.get("jti", "") in _token_blacklist
    except Exception:
        return False
