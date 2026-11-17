"""
文件名: ➡️ discover.py 🏁
路径: ➡️ engines/backend_bridge/models/discover.py 🏁
模块功能：➡️ 用密钥环境变量向厂商查询可用模型 id 🏁
Python 调试：➡️ python -m engines.backend_bridge.models.discover 🏁
时间：➡️ 2026-11-16 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-16 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. discover_models: 读环境变量里的密钥，请求厂商模型名单，只返回 id。
2. 查询失败不抛给页面：返回空名单和 manual，调用方可以改用手填。
3. 密钥明文不出现在返回值里。
🏁
关联模块：➡️
1. engines.backend_bridge.models.catalog: 厂商、密钥名与默认地址。
2. engines.ae_harness.agents.models: 按环境变量名取密钥。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_model_discover.py: 解析 id、失败改手填、密钥不匹配。
🏁
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from engines.ae_harness.agents.models import load_secret

from .catalog import expected_key, models_url

__all__ = ["discover_models"]

_TIMEOUT_SECONDS = 8


def discover_models(provider: str, api_key_env: str, base_url: str = "") -> dict:
    """
    查询该密钥下厂商当前列出的模型 id。

    Args:
        provider: 厂商名，只能是 deepseek、dashscope、govee。
        api_key_env: 密钥所在的环境变量名，必须与厂商成对。
        base_url: 查询地址，不能为空。

    Returns:
        含 models、source、reason 的字典。source 为 remote 或 manual。

    Raises:
        ValueError: 厂商未知，或密钥环境变量与厂商不匹配。
    """
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
