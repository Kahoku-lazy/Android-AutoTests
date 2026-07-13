"""Register all active Django agents with AgentScope on startup."""
import os, json, requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django; django.setup()

from apps.ai_assistant.models import AIAgent
from apps.ai_assistant.api import decrypt_key

AGENTSCOPE_URL = "http://127.0.0.1:8000"

for a in AIAgent.objects.filter(status="active"):
    api_key = decrypt_key(a.api_key) if a.api_key else ""
    if not api_key:
        print(f"SKIP agent-{a.id} ({a.name}): no API key configured")
        continue

    # Build base URL
    base_url = a.base_url
    if not base_url:
        if a.model_provider == "dashscope":
            base_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
        elif a.model_provider == "deepseek":
            base_url = "https://api.deepseek.com/v1"
        elif a.model_provider == "openai":
            base_url = "https://api.openai.com/v1"
        else:
            base_url = "https://api.deepseek.com/v1"

    body = {
        "agent_id": f"agent-{a.id}",
        "name": a.name,
        "system_prompt": a.system_prompt or "你是一个AI测试助手",
        "model_provider": a.model_provider or "custom",
        "model_name": a.model_name or "deepseek-v4-flash",
        "api_key": api_key,
        "base_url": base_url,
        "temperature": a.temperature or 0.7,
        "max_tokens": a.max_tokens or 4096,
    }

    try:
        # Get JWT token from Django
        login_resp = requests.post(
            f"http://127.0.0.1:8765/api/ai/auth/login",
            json={"username": os.environ.get("ADMIN_USER", "admin"), "password": os.environ.get("ADMIN_PASSWORD", "")},
            timeout=5,
        )
        token = login_resp.json().get("access_token", "")

        resp = requests.post(
            f"{AGENTSCOPE_URL}/agent/",
            json=body,
            headers={
                "X-User-ID": "system",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {token}",
            },
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"OK agent-{a.id} ({a.name}) registered with {a.model_name}")
        else:
            print(f"FAIL agent-{a.id}: HTTP {resp.status_code} — {resp.text[:200]}")
    except Exception as e:
        print(f"ERR agent-{a.id}: {e}")

print("Done")
