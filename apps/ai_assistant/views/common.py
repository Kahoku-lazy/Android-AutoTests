"""Shared helpers for ai-assistant view modules."""

from django.conf import settings
from django.http import JsonResponse

AVATAR_DIR = settings.BASE_DIR / "data" / "avatars"


def validation_error(errors: dict, status: int = 400):
    return JsonResponse(
        {"ok": False, "error": "; ".join(f"{k}: {v}" for k, v in errors.items()), "errors": errors},
        status=status,
    )


def agentscope_base_url() -> str:
    return getattr(settings, "AGENTSCOPE_SERVICE_URL", "http://127.0.0.1:8000").rstrip("/")


def get_agentscope_token(request):
    """Reuse the current user's JWT token for AgentScope calls."""
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        return auth_header[7:]
    return ""


def call_agentscope(path, method, body, token, timeout=10):
    """Make an HTTP request to the AgentScope service."""
    import requests

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {token}",
    }
    url = f"{agentscope_base_url()}{path}"
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=timeout)
        elif method == "POST":
            resp = requests.post(url, headers=headers, json=body, timeout=timeout)
        elif method == "DELETE":
            resp = requests.delete(url, headers=headers, timeout=timeout)
        else:
            return None, "unsupported method"
        return resp, None
    except requests.ConnectionError:
        return None, "AgentScope service unavailable"
    except requests.Timeout:
        return None, "AgentScope service timeout"
    except Exception as e:
        return None, str(e)


def create_agentscope_credential(
    provider_cfg: dict, api_key: str, agent_django_id: str, token: str
) -> tuple:
    """Create an AgentScope credential. Returns (credential_id, error)."""
    credential_body = {
        "data": {
            "type": provider_cfg["credential_type"],
            "api_key": api_key,
            "base_url": provider_cfg["base_url"],
            "agent_django_id": agent_django_id,
        },
    }
    resp, err = call_agentscope("/credential/", "POST", credential_body, token)
    if err:
        return "", f"credential creation failed: {err}"
    if resp.status_code not in (200, 201):
        return "", f"credential creation failed: HTTP {resp.status_code} — {resp.text[:200]}"
    return resp.json().get("credential_id", ""), ""
