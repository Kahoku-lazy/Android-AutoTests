"""
文件名: ➡️ catalog.py 🏁
路径: ➡️ engines/backend_bridge/models/catalog.py 🏁
模块功能：➡️ 厂商、密钥环境变量名与默认查询地址的对应关系 🏁
Python 调试：➡️ python -m engines.backend_bridge.models.catalog 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-16 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. KEY_BY_PROVIDER: 三个厂商各自只允许一个密钥环境变量名。
2. default_models_url: 给出查询模型名单的默认地址；dashscope 没有默认地址。
3. 本模块不读密钥、不发请求、不写库。
🏁
关联模块：➡️
1. engines.backend_bridge.models.discover: 按本表发查询请求。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

KEY_BY_PROVIDER = {
    "deepseek": "DEEPSEEK_API_KEY",
    "dashscope": "DASHSCOPE_API_KEY",
    "openai": "OPENAI_API_KEY",
}

# 当前引擎真实支持的三种客户端协议。
API_PROTOCOLS = ("deepseek", "dashscope", "openai")

# 空地址时用来查模型名单。dashscope 必须带业务空间 ID，这里不给默认。
_DEFAULT_BASE = {
    "deepseek": "https://api.deepseek.com",
    "openai": "https://test-llm.lanjingerp.com/v1",
}


def expected_key(provider: str) -> str:
    """
    返回厂商对应的密钥环境变量名。

    Args:
        provider: 厂商名。

    Returns:
        环境变量名。

    Raises:
        ValueError: 厂商不在三家之内。
    """
    key = KEY_BY_PROVIDER.get(str(provider or "").strip())
    if not key:
        raise ValueError("厂商只允许 deepseek、dashscope、openai")
    return key


def models_url(provider: str, base_url: str = "") -> str:
    """
    拼出模型名单地址。地址必须由调用方传入，不再偷偷补默认地址。

    Args:
        provider: 厂商名，仅用于兼容旧调用。
        base_url: 调用方填写的地址。

    Returns:
        可请求的 URL；地址为空时返回空串。
    """
    del provider
    raw = str(base_url or "").strip().rstrip("/")
    if not raw:
        return ""
    if raw.endswith("/models"):
        return raw
    return f"{raw}/models"
