"""Shared helpers for ai-assistant view modules."""
from django.conf import settings
from django.http import JsonResponse


AVATAR_DIR = settings.BASE_DIR / 'data' / 'avatars'


def validation_error(errors: dict, status: int = 400):
    return JsonResponse(
        {"ok": False, "error": "; ".join(f"{k}: {v}" for k, v in errors.items()), "errors": errors},
        status=status,
    )


def agentscope_base_url() -> str:
    return getattr(settings, 'AGENTSCOPE_SERVICE_URL', 'http://127.0.0.1:8000').rstrip('/')


def get_agentscope_token(request):
    """Reuse the current user's JWT token for AgentScope calls."""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return ''


def call_agentscope(path, method, body, token, timeout=10):
    """Make an HTTP request to the AgentScope service."""
    import requests
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {token}',
    }
    url = f'{agentscope_base_url()}{path}'
    try:
        if method == 'GET':
            resp = requests.get(url, headers=headers, timeout=timeout)
        elif method == 'POST':
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        elif method == 'DELETE':
            resp = requests.delete(url, headers=headers, timeout=timeout)
        else:
            return None, 'unsupported method'
        return resp, None
    except requests.ConnectionError:
        return None, 'AgentScope service unavailable'
    except requests.Timeout:
        return None, 'AgentScope service timeout'
    except Exception as e:
        return None, str(e)
