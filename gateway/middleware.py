"""Gateway middleware — JWT authentication, logging, CORS."""
import logging
from django.http import JsonResponse
from shared.auth.jwt_auth import verify_token, get_user_id_from_token

logger = logging.getLogger('gateway')

# Paths that do NOT require authentication
PUBLIC_PREFIXES = [
    '/api/ai/auth/',
    '/admin/',
    '/static/',
    '/api/docs',
]


def _is_public(path: str) -> bool:
    """Check if a request path is publicly accessible without JWT."""
    for prefix in PUBLIC_PREFIXES:
        if path.startswith(prefix):
            return True
    return False


class JWTAuthenticationMiddleware:
    """Django middleware that validates JWT tokens on protected /api/ routes.

    Extracts user_id from Authorization: Bearer <token> header and attaches
    it to request.user_id.  Public paths (auth, admin, static) are skipped.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path

        # Skip public paths
        if _is_public(path):
            return self.get_response(request)

        # Only protect /api/ paths
        if not path.startswith('/api/'):
            return self.get_response(request)

        # Extract and verify token
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            try:
                payload = verify_token(token)
                request.user_id = payload['sub']
            except Exception as e:
                logger.warning(f'JWT verify failed for {path}: {e}')
                return JsonResponse(
                    {'ok': False, 'error': 'Invalid or expired token'},
                    status=401,
                )
        else:
            # No token — still allow for dev convenience (backward compat)
            # In production, uncomment the lines below:
            # return JsonResponse(
            #     {'ok': False, 'error': 'Authorization header required'},
            #     status=401,
            # )
            request.user_id = None

        return self.get_response(request)
