"""DeepSeek 费用保留小数点后 8 位。"""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from engines.agents.messaging.billing import DeepSeekBilling

_ZERO = Decimal("0.00000000")
_IDLE = datetime.fromisoformat("2026-10-18T10:00:00+08:00")


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
