"""
模块功能：➡️ 向厂商查询模型名。视图不直接调用引擎 🏁
Python 调试：➡️ python -m backend.apps.ai_assistant.services.discover 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 ai_assistant 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from engines.backend_bridge.models import discover_models
from engines.backend_bridge.models.catalog import expected_key


def discover_model_names(provider: str, api_key_env: str, base_url: str = "") -> dict:
    """查询厂商当前列出的模型名。不写库。

    Args:
        provider: 厂商名。
        api_key_env: 密钥环境变量名。
        base_url: 查询地址。

    Returns:
        含 models、source、reason 的字典。

    Raises:
        ValueError: 厂商与密钥名不匹配。
    """
    expected_key(provider)
    return discover_models(provider, api_key_env, base_url)
