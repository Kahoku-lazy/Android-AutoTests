"""DeepSeek 模型费用。只计算官方当前两个模型。

价目：https://api-docs.deepseek.com/zh-cn/quick_start/pricing
空闲时段单价（元 / 百万 tokens）；高峰时段 = 空闲 × 2。
高峰：北京时间周一至周五 9:00–12:00、14:00–18:00，法定节假日全天除外。
"""

from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

import chinese_calendar

_SHANGHAI = ZoneInfo("Asia/Shanghai")
_MILLION = Decimal(1_000_000)
_PEAK_MULTIPLIER = Decimal(2)


_FOUR_DECIMAL = Decimal("0.0001")


def _four_decimal_places(amount: Decimal) -> float:
    """金额保留小数点后 4 位，四舍五入。零返回 0.0。"""
    if amount == 0:
        return 0.0
    return float(amount.quantize(_FOUR_DECIMAL, rounding=ROUND_HALF_UP))


class DeepSeekBilling:
    """只计算 deepseek-flash 与 deepseek-v4-pro 的费用。"""

    # 空闲时段单价（元 / 百万 tokens）
    PRICING: dict[str, dict[str, Decimal]] = {
        "deepseek-flash": {
            "input_cache_hit": Decimal("0.02"),
            "input_cache_miss": Decimal("1"),
            "output": Decimal("4"),
        },
        "deepseek-v4-pro": {
            "input_cache_hit": Decimal("0.15"),
            "input_cache_miss": Decimal("4.5"),
            "output": Decimal("13.5"),
        },
    }

    def cost(
        self,
        model_name: str,
        input_tokens: int,
        output_tokens: int,
        cache_hit_tokens: int,
        created_at: datetime | None = None,
    ) -> tuple[float, float, float]:
        """按与用量相同的三项，返回费用（元，各保留小数点后 4 位、四舍五入）。

        Args:
            model_name: 模型名。只认 deepseek-flash、deepseek-v4-pro。
            input_tokens: 输入 token。
            output_tokens: 输出 token。
            cache_hit_tokens: 缓存命中 token。超过输入 token 时按输入 token 计。
            created_at: 调用时刻。None 按空闲时段；带时区则换算到北京时间。

        Returns:
            (输入费用, 输出费用, 缓存命中费用)。
            输入费用只计缓存未命中部分。未登记模型返回 (0.0, 0.0, 0.0)。
        """
        price = self.PRICING.get(str(model_name or "").strip().lower())
        if price is None:
            return 0.0, 0.0, 0.0
        multiplier = _PEAK_MULTIPLIER if self._is_peak_time(created_at) else Decimal(1)
        incoming = max(int(input_tokens or 0), 0)
        outgoing = max(int(output_tokens or 0), 0)
        hit = max(min(int(cache_hit_tokens or 0), incoming), 0)
        miss = incoming - hit
        input_cost = Decimal(miss) * price["input_cache_miss"] / _MILLION * multiplier
        output_cost = Decimal(outgoing) * price["output"] / _MILLION * multiplier
        cache_cost = Decimal(hit) * price["input_cache_hit"] / _MILLION * multiplier
        return (
            _four_decimal_places(input_cost),
            _four_decimal_places(output_cost),
            _four_decimal_places(cache_cost),
        )

    @staticmethod
    def _is_peak_time(created_at: datetime | None) -> bool:
        """北京时间周一至周五 9:00–12:00、14:00–18:00。法定节假日全天不算高峰。"""
        if created_at is None:
            return False
        moment = created_at.astimezone(_SHANGHAI) if created_at.tzinfo else created_at
        if moment.weekday() >= 5:
            return False
        if _is_statutory_holiday(moment):
            return False
        hour = moment.hour
        return (9 <= hour < 12) or (14 <= hour < 18)


def _is_statutory_holiday(moment: datetime) -> bool:
    """该时刻所在日期是否为法定放假日。

    Args:
        moment: 已换算到北京时间的时刻。只在周一至周五调用。

    Returns:
        法定放假日为 True。节假日库未收录该年时为 False，退回工作日规则。
    """
    try:
        on_holiday, _name = chinese_calendar.get_holiday_detail(moment.date())
    except NotImplementedError:
        return False
    return bool(on_holiday)
