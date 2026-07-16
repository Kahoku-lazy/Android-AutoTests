"""Auth endpoints — login, register, refresh, logout, me."""
import json

from django.contrib.auth import authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from shared.auth.jwt_auth import (
    blacklist_token,
    create_access_token,
    create_token_pair,
    verify_token,
)

from ..decorators import require_auth


@csrf_exempt
def login(request):
    """POST /api/ai/auth/login — authenticate and return JWT token pair."""
    data = json.loads(request.body)
    username = data.get('username', '')
    password = data.get('password', '')
    user = authenticate(username=username, password=password)
    if user is None:
        return JsonResponse({'ok': False, 'error': 'Invalid credentials'}, status=401)
    tokens = create_token_pair(str(user.id))
    return JsonResponse({
        'ok': True,
        **tokens,
        'user': {'id': user.id, 'username': user.username},
    })


@csrf_exempt
def register(request):
    """POST /api/ai/auth/register — create a new user."""
    from django.contrib.auth.models import User
    data = json.loads(request.body)
    username = data.get('username', '').strip()
    password = data.get('password', '').strip()
    if not username or not password:
        return JsonResponse({'ok': False, 'error': 'username and password required'}, status=400)
    if User.objects.filter(username=username).exists():
        return JsonResponse({'ok': False, 'error': 'username already exists'}, status=409)
    user = User.objects.create_user(username=username, password=password)
    tokens = create_token_pair(str(user.id))
    return JsonResponse({
        'ok': True,
        **tokens,
        'user': {'id': user.id, 'username': user.username},
    })


@csrf_exempt
def refresh_token(request):
    """POST /api/ai/auth/refresh — refresh access token using refresh token."""
    data = json.loads(request.body)
    token = data.get('refresh_token', '')
    try:
        payload = verify_token(token, expected_type='refresh')
        if payload.get('type') != 'refresh':
            return JsonResponse({'ok': False, 'error': 'Not a refresh token'}, status=401)
        new_access = create_access_token(payload['sub'])
        return JsonResponse({'ok': True, 'access_token': new_access, 'token_type': 'bearer'})
    except Exception as e:
        return JsonResponse({'ok': False, 'error': str(e)}, status=401)


@csrf_exempt
@require_auth
def logout(request):
    """POST /api/ai/auth/logout — blacklist the current token."""
    auth_header = request.META.get('HTTP_AUTHORIZATION', '')
    if auth_header.startswith('Bearer '):
        blacklist_token(auth_header[7:])
    return JsonResponse({'ok': True})


def me(request):
    """GET /api/ai/auth/me — return current user info from JWT."""
    user_id = getattr(request, 'user_id', None)
    if not user_id:
        return JsonResponse({'ok': False, 'error': 'Not authenticated'}, status=401)
    from django.contrib.auth.models import User
    try:
        user = User.objects.get(id=user_id)
        return JsonResponse({'ok': True, 'user': {'id': user.id, 'username': user.username}})
    except User.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'User not found'}, status=404)
