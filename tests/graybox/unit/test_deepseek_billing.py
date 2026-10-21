"""DeepSeek 任务费用纯函数。"""

from datetime import datetime
from types import SimpleNamespace

import pytest

from backend.apps.task_list.deepseek_billing import deepseek_cost, task_deepseek_cost

# 官方现价（2026-10-08 价目页）：deepseek-flash 空闲命中 0.02 / 未命中 1 / 输出 4（元/百万）
FLASH_HIT, FLASH_MISS, FLASH_OUT = 0.02, 1.0, 4.0


@pytest.mark.unit
def test_flash_idle_cost_matches_official_rates():
    # 空闲 flash：命中 0.02 / 未命中 1 / 输出 4（元/百万）
    sunday = datetime(2026, 9, 6, 10, 0, 0)  # 周日
    cost = deepseek_cost(79382, 3264, 38016, "deepseek-flash", sunday)
    miss = 79382 - 38016
    expected = (38016 * FLASH_HIT + miss * FLASH_MISS + 3264 * FLASH_OUT) / 1_000_000
    assert round(cost, 6) == round(expected, 6)


@pytest.mark.unit
def test_legacy_flash_names_bill_at_flash_rate():
    """厂商口径：旧名仍可调用、按 Flash 计费 —— 三个旧名与正式名同价。"""
    sunday = datetime(2026, 9, 6, 10, 0, 0)
    formal = deepseek_cost(10000, 500, 2000, "deepseek-flash", sunday)
    for legacy in ("deepseek-v4-flash", "deepseek-v4-flash-vision-exp", "deepseek-chat"):
        assert deepseek_cost(10000, 500, 2000, legacy, sunday) == formal, legacy


@pytest.mark.unit
def test_pro_peak_doubles_idle():
    weekday_peak = datetime(2026, 9, 8, 10, 0, 0)  # 周二 10:00
    idle = deepseek_cost(1000, 1000, 0, "deepseek-v4-pro", datetime(2026, 9, 6, 10, 0, 0))
    peak = deepseek_cost(1000, 1000, 0, "deepseek-v4-pro", weekday_peak)
    assert round(peak, 6) == round(idle * 2, 6)


@pytest.mark.unit
def test_task_uses_per_model_then_fallback_flash():
    sunday = datetime(2026, 9, 6, 22, 0, 0)
    split = SimpleNamespace(
        finished_at=sunday,
        created_at=sunday,
        model_usage={
            "deepseek-flash": {
                "input_tokens": 1000,
                "output_tokens": 100,
                "cache_input_tokens": 200,
            },
            "deepseek-v4-pro": {
                "input_tokens": 500,
                "output_tokens": 50,
                "cache_input_tokens": 0,
            },
        },
        input_tokens=0,
        output_tokens=0,
        cache_input_tokens=0,
    )
    per_model = task_deepseek_cost(split)
    expected = round(
        deepseek_cost(1000, 100, 200, "deepseek-flash", sunday)
        + deepseek_cost(500, 50, 0, "deepseek-v4-pro", sunday),
        4,
    )
    assert per_model == expected

    fallback = SimpleNamespace(
        finished_at=sunday,
        created_at=sunday,
        model_usage={},
        input_tokens=79382,
        output_tokens=3264,
        cache_input_tokens=38016,
    )
    assert task_deepseek_cost(fallback) == round(
        deepseek_cost(79382, 3264, 38016, "deepseek-flash", sunday),
        4,
    )
