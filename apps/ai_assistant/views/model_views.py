"""Model connectivity — test connection, list models."""

import json
import logging

from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from apps.ai_assistant.agent_scope.provider_registry import get_provider_config

from ..api import decrypt_key
from ..decorators import require_auth
from ..models import AIAgent
from ..permissions import check_agent_owner
from ..serializers import validate_model_detect_input
from .common import validation_error

logger = logging.getLogger("ai_assistant")

_MODEL_LIST_PATHS = ["/models", "/v1/models"]


def _extract_model_ids(resp_json: dict) -> list:
    """Extract model ID strings from a /models-style API response."""
    if "data" in resp_json:
        return [m.get("id", "") for m in resp_json["data"] if m.get("id")]
    if "models" in resp_json:
        return [m.get("id", "") for m in resp_json["models"] if m.get("id")]
    return []


def call_model_api(agent, path, method="GET", body=None):
    """Call the model provider's API with the agent's credentials."""
    import requests

    api_key = decrypt_key(agent.api_key) if agent.api_key else ""
    provider_cfg = get_provider_config(agent.model_provider, agent.base_url)
    base = provider_cfg["base_url"]
    if not base:
        return None, "No base_url configured"
    url = f"{base}{path}"
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    try:
        if method == "GET":
            resp = requests.get(url, headers=headers, timeout=15)
        else:
            resp = requests.post(url, headers=headers, json=body or {}, timeout=15)
        return resp, None
    except requests.RequestException as e:
        return None, str(e)


@csrf_exempt
@require_auth
def test_agent_connection(request, agent_id):
    """POST /api/ai/agents/{id}/test — test API connectivity and fetch models."""
    if not check_agent_owner(request.user_id, agent_id):
        return JsonResponse({"status": False, "message": "Forbidden"}, status=403)
    try:
        a = AIAgent.objects.get(id=agent_id)
    except AIAgent.DoesNotExist:
        return JsonResponse({"status": False, "message": "not found"}, status=404)

    available_models = []
    connected = False
    last_error = ""

    for path in _MODEL_LIST_PATHS:
        resp, err = call_model_api(a, path)
        if err:
            last_error = err
            continue
        if resp is not None and 200 <= resp.status_code < 300:
            connected = True
            data = resp.json()
            available_models = _extract_model_ids(data)
            if available_models:
                cur = a.model_name
                available_models.sort(key=lambda x: (x != cur, x))
            break
        else:
            last_error = f"HTTP {resp.status_code}"

    if not connected and not last_error:
        chat_body = {
            "model": a.model_name,
            "messages": [{"role": "user", "content": "hi"}],
            "max_tokens": 5,
        }
        resp, err = call_model_api(a, "/chat/completions", "POST", chat_body)
        if err:
            last_error = err
        elif resp and 200 <= resp.status_code < 300:
            connected = True
        elif resp:
            last_error = f"HTTP {resp.status_code}: {resp.text[:200]}"

    a.is_connected = connected
    a.last_checked_at = datetime.now()
    if available_models:
        a.available_models = json.dumps(available_models)
    a.save()

    return JsonResponse(
        {
            "status": True,
            "connected": connected,
            "available_models": available_models,
            "message": last_error if not connected else "",
        }
    )


@csrf_exempt
@require_auth
def list_available_models(request, agent_id=None):
    """GET cached models for an agent, or POST to detect from API config."""
    if request.method == "POST":
        data = json.loads(request.body)
        ok, errors, cleaned = validate_model_detect_input(data)
        if not ok:
            return validation_error(errors)
        provider = cleaned.get("model_provider", "")
        api_key = cleaned.get("api_key", "")
        provider_cfg = get_provider_config(provider, cleaned.get("base_url", ""))
        base_url = provider_cfg["base_url"]
        import requests

        models = []
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        for path in _MODEL_LIST_PATHS:
            try:
                resp = requests.get(f"{base_url.rstrip('/')}{path}", headers=headers, timeout=15)
                if 200 <= resp.status_code < 300:
                    data_json = resp.json()
                    models = _extract_model_ids(data_json)
                    if models:
                        break
            except Exception:
                logger.warning("model detection request failed for %s", base_url)
                continue
        return JsonResponse({"status": True, "models": models})

    if agent_id:
        try:
            a = AIAgent.objects.get(id=agent_id)
            models = json.loads(a.available_models) if a.available_models else []
            return JsonResponse(
                {
                    "status": True,
                    "models": models,
                    "is_connected": a.is_connected,
                    "last_checked": str(a.last_checked_at) if a.last_checked_at else None,
                }
            )
        except AIAgent.DoesNotExist:
            return JsonResponse({"status": False, "message": "not found"}, status=404)
    return JsonResponse({"status": False, "message": "agent_id required"}, status=400)
