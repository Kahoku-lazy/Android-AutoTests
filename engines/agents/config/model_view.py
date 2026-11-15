"""
文件名: ➡️ model_view.py 🏁
路径: ➡️ engines/agents/config/model_view.py 🏁
模块功能：➡️ 从已装载模型表按短名只读查看规格，不造实例、不解密 🏁
Python 调试：➡️ python -m engines.agents.config.model_view 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. ModelView: 一条模型规格的只读字段（正式名、族、音色、维度、密钥变量名）。
2. model_view: 按短名从已装载表取视图；未知短名报错并列出可选短名。
🏁
关联模块：➡️
1. engines.agents.config.config: 调用方传入 load_model_config 的表；本模块不读文件。
🏁
测试：➡️
1. tests/config/unit/test_model_view.py: 已知短名、未知短名、缺密钥仍可查看、repr 不含明文
🏁
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any

__all__ = ["ModelView", "model_view"]


@dataclass(frozen=True)
class ModelView:
    """
    一条已装载模型的只读规格。

    只放查看方需要的字段。密钥对象不进本视图，文本表示也不含明文。

    Attributes:
        name: 模型短名。
        model_name: 厂商正式模型名。
        family: 模型族（chat / realtime / embedding / tts）。
        voices: 声明的可选音色；未声明时为空元组。
        dimensions: 向量维度；未声明时为 0。
        api_key_env: 密钥环境变量名；未声明时为空串。
    """

    name: str
    model_name: str
    family: str
    voices: tuple[str, ...] = ()
    dimensions: int = 0
    api_key_env: str = ""


def _as_tuple(value: object) -> tuple[str, ...]:
    """把音色列表收成字符串元组；不是列表时返回空。"""
    if not isinstance(value, list):
        return ()
    return tuple(str(item).strip() for item in value if str(item).strip())


def model_view(catalog: Mapping[str, Any], short_name: str) -> ModelView:
    """
    从已装载模型表按短名取只读规格。

    Args:
        catalog: config 读好的整张模型表。条目里可以带密钥对象，本函数不读取它。
        short_name: 模型短名，如 `deepseek_flash`。

    Returns:
        该短名的只读视图。缺 voices / dimensions / api_key_env 时用空值，不报错。

    Raises:
        ValueError: 短名未登记，或该条目不是映射。
    """
    entry = catalog.get(short_name)
    if not isinstance(entry, Mapping):
        choices = ", ".join(sorted(str(name) for name in catalog))
        raise ValueError(f"未知模型 {short_name!r}；可选：{choices}")
    dimensions = entry.get("dimensions") or 0
    return ModelView(
        name=short_name,
        model_name=str(entry.get("model_name") or "").strip(),
        family=str(entry.get("family") or "").strip(),
        voices=_as_tuple(entry.get("voices")),
        dimensions=int(dimensions) if str(dimensions).isdigit() else 0,
        api_key_env=str(entry.get("api_key_env") or "").strip(),
    )
