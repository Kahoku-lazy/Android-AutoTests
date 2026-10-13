"""费用计算包 —— 用量累加（总量 / 按模型 / 按角色）+ 价目与单轮费用。

计费口径仅在 DeepSeek 生效，价目表与后端 `apps/ai_assistant/deepseek_billing.py` 对齐。
"""

from .billing import DEEPSEEK_PRICING, model_cost
from .usage import UsageAccumulator

__all__ = ["DEEPSEEK_PRICING", "UsageAccumulator", "model_cost"]
