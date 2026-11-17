"""平台侧模型费用计算：8 位小数、未知模型免费、旧名归档、高峰倍率与快照。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

import pytest

from engines.backend_bridge.model_billing import DeepSeekBilling

pytestmark = [pytest.mark.unit]

_ZERO = Decimal("0.00000000")
_IDLE = datetime.fromisoformat("2026-10-18T10:00:00+08:00")  # 周日，按空闲时段
_PEAK = datetime.fromisoformat("2026-10-19T10:00:00+08:00")  # 周一 10:00，高峰


def _cost(incoming: int, outgoing: int, hit: int, model: str = "deepseek-flash"):
    return DeepSeekBilling().cost(model, incoming, outgoing, hit, _IDLE)


def test_small_input_keeps_eight_decimals():
    incoming, outgoing, cache = _cost(12345, 0, 0)
    assert incoming == Decimal("0.01234500")
    assert outgoing == _ZERO
    assert cache == _ZERO


def test_amount_that_used_to_round_up_at_four_decimals_stays_exact():
    incoming, outgoing, cache = _cost(4670, 0, 0)
    assert incoming == Decimal("0.00467000")
    assert outgoing == _ZERO
    assert cache == _ZERO


def test_amount_that_used_to_round_down_at_four_decimals_stays_exact():
    incoming, _outgoing, _cache = _cost(4630, 0, 0)
    assert incoming == Decimal("0.00463000")


def test_halfway_at_the_fifth_decimal_is_not_rounded_to_four_places():
    incoming, _outgoing, _cache = _cost(4650, 0, 0)
    assert incoming == Decimal("0.00465000")


def test_tiny_cache_hit_keeps_eight_decimals():
    incoming, outgoing, cache = _cost(2560, 972, 2560)
    assert incoming == _ZERO
    assert outgoing == Decimal("0.00388800")
    assert cache == Decimal("0.00005120")


def test_cache_hit_that_four_decimals_would_zero_is_kept():
    incoming, outgoing, cache = _cost(1000, 0, 1000)
    assert incoming == _ZERO
    assert outgoing == _ZERO
    assert cache == Decimal("0.00002000")


def test_unknown_model_is_free():
    assert _cost(1000, 1000, 1000, model="deepseek-chat") == (_ZERO, _ZERO, _ZERO)


def test_cache_hit_above_input_makes_input_cost_zero():
    incoming, _outgoing, _cache = _cost(10, 0, 50)
    assert incoming == _ZERO


def test_snapshot_carries_prices_and_peak_flag():
    snap = DeepSeekBilling().snapshot("deepseek-flash", _IDLE)
    assert snap["model"] == "deepseek-flash"
    assert snap["hit_price"] == Decimal("0.02")
    assert snap["miss_price"] == Decimal("1")
    assert snap["output_price"] == Decimal("4")
    assert snap["multiplier"] == Decimal(1)
    assert snap["peak"] is False


def test_old_model_name_is_billed_as_flash():
    """官方旧名按 Flash 价计费，快照里的 model 显示成归一后的计费档。"""
    billing = DeepSeekBilling()
    for old_name in ("deepseek-v4-flash", "deepseek-v4-flash-vision-exp"):
        assert billing.cost(old_name, 12345, 0, 0, _IDLE) == billing.cost(
            "deepseek-flash", 12345, 0, 0, _IDLE
        )
        assert billing.snapshot(old_name, _IDLE)["model"] == "deepseek-flash"


def test_peak_time_doubles_all_three_items():
    incoming, outgoing, cache = DeepSeekBilling().cost("deepseek-flash", 12345, 1000, 0, _PEAK)
    assert incoming == Decimal("0.02469000")
    assert outgoing == Decimal("0.00800000")
    assert cache == _ZERO


def test_peak_flag_is_set_in_snapshot():
    snap = DeepSeekBilling().snapshot("deepseek-flash", _PEAK)
    assert snap["peak"] is True
    assert snap["multiplier"] == Decimal(2)


def test_timezone_is_converted_to_shanghai_before_peak_check():
    """UTC 02:00 等于北京时间 10:00，应判为高峰。"""
    utc_peak = datetime.fromisoformat("2026-10-19T02:00:00+00:00")
    assert DeepSeekBilling().snapshot("deepseek-flash", utc_peak)["peak"] is True


def test_weekend_is_not_peak():
    weekend = datetime.fromisoformat("2026-10-18T10:00:00+08:00")
    assert DeepSeekBilling().snapshot("deepseek-flash", weekend)["peak"] is False


def test_unknown_model_snapshot_has_zero_prices():
    snap = DeepSeekBilling().snapshot("deepseek-chat", _IDLE)
    assert snap["model"] == "deepseek-chat"
    assert snap["hit_price"] == _ZERO
    assert snap["miss_price"] == _ZERO
    assert snap["output_price"] == _ZERO
