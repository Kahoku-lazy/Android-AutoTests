"""
python -m 调试路径: engines.agents.config.models

本模块的业务功能如下：
1. DeepSeekModelConfig: DeepSeek 连接参数（provider / base_url）与可选模型名（FLASH / PRO）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import ClassVar


@dataclass(frozen=True)
class DeepSeekModelConfig:
    """
    DeepSeek 连接参数与可选模型。

    类常量直接取用（`DeepSeekModelConfig.FLASH`、`DeepSeekModelConfig.provider`）；
    `DeepSeekModelConfig(model_name=DeepSeekModelConfig.PRO)`。

    Attributes:
        provider: 模型提供商，固定 deepseek。
        base_url: OpenAI 兼容入口；官方 /v1 只是兼容前缀，与模型版本无关。

    Raises:
        FrozenInstanceError: 配置不可变。
    """

    # 可选模型名。新增模型时在此登记，并在 billing.PRICING 加同名的键。
    FLASH: ClassVar[str] = "deepseek-flash"
    PRO: ClassVar[str] = "deepseek-v4-pro"
    MODELS: ClassVar[tuple[str, ...]] = (FLASH, PRO)

    provider: str = "deepseek"
    base_url: str = "https://api.deepseek.com/v1"
    model_name: str = FLASH
