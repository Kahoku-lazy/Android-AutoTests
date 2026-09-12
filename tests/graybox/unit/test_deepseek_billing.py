"""DeepSeek 任务费用纯函数。"""

from datetime import datetime
from types import SimpleNamespace

import pytest

from apps.ai_assistant.deepseek_billing import deepseek_cost, task_deepseek_cost


@pytest.mark.unit
def test_flash_idle_cost_matches_official_rates():
    # 空闲 flash：命中 0.05 / 未命中 1.5 / 输出 4.5（元/百万）
    sunday = datetime(2026, 9, 6, 10, 0, 0)  # 周日
    cost = deepseek_cost(79382, 3264, 38016, "deepseek-v4-flash", sunday)
    miss = 79382 - 38016
    expected = (38016 * 0.05 + miss * 1.5 + 3264 * 4.5) / 1_000_000
    assert round(cost, 6) == round(expected, 6)


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
            "deepseek-v4-flash": {
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
        deepseek_cost(1000, 100, 200, "deepseek-v4-flash", sunday)
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
        deepseek_cost(79382, 3264, 38016, "deepseek-v4-flash", sunday),
        4,
    )
