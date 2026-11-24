from __future__ import annotations

from datetime import datetime
from decimal import ROUND_HALF_UP, Decimal
from zoneinfo import ZoneInfo

import chinese_calendar

__all__ = ["DeepSeekBilling"]

_SHANGHAI = ZoneInfo("Asia/Shanghai")
_MILLION = Decimal(1_000_000)
_PEAK_MULTIPLIER = Decimal(2)

_FLASH = "deepseek-flash"
_PRO = "deepseek-v4-pro"

_MODEL_ALIASES = {
    "deepseek-v4-flash": _FLASH,
    "deepseek-v4-flash-vision-exp": _FLASH,
}

_EIGHT_DECIMAL = Decimal("0.00000001")
_ZERO = Decimal("0.00000000")


def _billed_model(model_name: str) -> str:
    name = str(model_name or "").strip().lower()
    return _MODEL_ALIASES.get(name, name)


def _eight_decimal_places(amount: Decimal) -> Decimal:
    return amount.quantize(_EIGHT_DECIMAL, rounding=ROUND_HALF_UP)


class DeepSeekBilling:
    PRICING: dict[str, dict[str, Decimal]] = {
        _FLASH: {
            "input_cache_hit": Decimal("0.02"),
            "input_cache_miss": Decimal("1"),
            "output": Decimal("4"),
        },
        _PRO: {
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
    ) -> tuple[Decimal, Decimal, Decimal]:
        price = self.PRICING.get(_billed_model(model_name))
        if price is None:
            return _ZERO, _ZERO, _ZERO
        multiplier = _PEAK_MULTIPLIER if self._is_peak_time(created_at) else Decimal(1)
        incoming = max(int(input_tokens or 0), 0)
        outgoing = max(int(output_tokens or 0), 0)
        hit = max(min(int(cache_hit_tokens or 0), incoming), 0)
        miss = incoming - hit
        input_cost = Decimal(miss) * price["input_cache_miss"] / _MILLION * multiplier
        output_cost = Decimal(outgoing) * price["output"] / _MILLION * multiplier
        cache_cost = Decimal(hit) * price["input_cache_hit"] / _MILLION * multiplier
        return (
            _eight_decimal_places(input_cost),
            _eight_decimal_places(output_cost),
            _eight_decimal_places(cache_cost),
        )

    def snapshot(
        self,
        model_name: str,
        created_at: datetime | None = None,
    ) -> dict:
        name = _billed_model(model_name)
        price = self.PRICING.get(name)
        peak = self._is_peak_time(created_at)
        multiplier = _PEAK_MULTIPLIER if peak else Decimal(1)
        if price is None:
            hit_price = miss_price = output_price = _ZERO
        else:
            hit_price = price["input_cache_hit"]
            miss_price = price["input_cache_miss"]
            output_price = price["output"]
        return {
            "model": name,
            "hit_price": hit_price,
            "miss_price": miss_price,
            "output_price": output_price,
            "multiplier": multiplier,
            "peak": peak,
        }

    @staticmethod
    def _is_peak_time(created_at: datetime | None) -> bool:
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
    try:
        on_holiday, _name = chinese_calendar.get_holiday_detail(moment.date())
    except NotImplementedError:
        return False
    return bool(on_holiday)
