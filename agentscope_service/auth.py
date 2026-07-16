"""AgentScope FastAPI JWT authentication dependency.

Overrides the default X-User-ID header extraction with JWT bearer token verification,
sharing the same secret key and validation logic as the Django middleware.
"""
from fastapi import Header, HTTPException, status
from shared.auth.jwt_auth import verify_token


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
        return payload["sub"]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid or expired token: {e}",
        )
