from __future__ import annotations

import json
import urllib.error
import urllib.request

from engines.ae_harness.agents.models import load_secret

from .catalog import expected_key, models_url

__all__ = ["discover_models"]

_TIMEOUT_SECONDS = 8


def discover_models(provider: str, api_key_env: str, base_url: str = "") -> dict:
    expected = expected_key(provider)
    if str(api_key_env or "").strip() != expected:
        raise ValueError(f"{provider} 的密钥必须是 {expected}")

    url = models_url(provider, base_url)
    if not url:
        return {"models": [], "source": "manual", "reason": "模型加载失败：请先填写 API 地址"}

    secret = load_secret(expected)
    if not secret:
        return {
            "models": [],
            "source": "manual",
            "reason": f"模型加载失败：环境变量 {expected} 未配置",
        }

    request = urllib.request.Request(url, headers={"Authorization": f"Bearer {secret}"})
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, UnicodeError):
        return {"models": [], "source": "manual", "reason": "模型加载失败"}

    names = []
    for item in payload.get("data") or []:
        model_id = str((item or {}).get("id") or "").strip()
        if model_id and model_id not in names:
            names.append(model_id)
    if not names:
        return {"models": [], "source": "manual", "reason": "模型列表为空"}
    return {"models": names, "source": "remote", "reason": ""}
