"""AgentScope FastAPI JWT authentication dependency.

Overrides the default X-User-ID header extraction with JWT bearer token verification,
sharing the same secret key and validation logic as the Django middleware.

Also stores the raw JWT token in a context variable so build_business_tools()
can inject it into ToolContext for HTTP calls to Django.
"""

from contextvars import ContextVar

from fastapi import Header, HTTPException, status

from shared.auth.jwt_auth import verify_token

# Context variable to share the raw JWT with tool factories.
# Set by get_current_user_id on each request; read by factory.py.
_current_jwt: ContextVar[str] = ContextVar("agentscope_jwt", default="")


def get_stored_jwt() -> str:
    """Return the JWT token for the current request context."""
    return _current_jwt.get()


async def get_current_user_id(
    authorization: str = Header(default="", description="Bearer <JWT token>"),
) -> str:
    """FastAPI dependency — extract user_id from JWT bearer token.

    Replaces AgentScope's default X-User-ID dependency via app.dependency_overrides.
    """
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header is required.",
        )

    if authorization.startswith("Bearer "):
        token = authorization[7:]
    else:
        token = authorization

    try:
        payload = verify_token(token, expected_type="access")
        # Store raw token so tool factories can forward it to Django
        _current_jwt.set(token)
        return payload["sub"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
        )
