"""平台运行用量入账：幂等键、厂商推断、失败不阻断。

只测 `usage_ledger/api.record_run_usages` 与两个纯函数。不测运行入口。
"""

from __future__ import annotations

import pytest

from backend.apps.usage_ledger import api
from backend.apps.usage_ledger.models import ModelUsage

pytestmark = [pytest.mark.unit]


def _usage(round_index: int = 1, env: str = "GOVEE_API_KEY") -> dict:
    """造一条平台运行产出的用量字典（键与事件层一致）。"""
    return {
        "api_key_env": env,
        "round": round_index,
        "started_at": "2026-11-14_20-08-39.123",
        "ended_at": "2026-11-14_20-08-41.456",
        "input_tokens": 5031,
        "output_tokens": 2,
        "cache_input_tokens": 4736,
        "cache_creation_input_tokens": 0,
    }


def test_provider_inferred_from_env_name():
    """密钥环境变量名决定厂商标签。"""
    assert api._provider_of("DEEPSEEK_API_KEY") == "deepseek"
    assert api._provider_of("DASHSCOPE_API_KEY") == "dashscope"
    assert api._provider_of("GOVEE_API_KEY") == "govee"
    assert api._provider_of("") == ""


def test_usage_moment_parses_and_falls_back():
    """时间戳能解析；非法值退回当前时间且不抛错。"""
    moment = api._usage_moment("2026-11-14_20-08-39.123")
    assert moment.year == 2026
    assert api._usage_moment("not-a-time") is not None


@pytest.mark.integration
@pytest.mark.django_db
def test_record_run_usages_writes_rows():
    """两条用量写入两行账本，模型与来源被带上。"""
    written = api.record_run_usages(
        [_usage(1), _usage(2, "DEEPSEEK_API_KEY")],
        execution_id="run-abc",
        model="deepseek-flash",
    )

    assert written == 2
    rows = ModelUsage.objects.filter(execution_id="run-abc").order_by("event_id")
    assert rows.count() == 2
    assert {row.source for row in rows} == {"agent"}
    assert {row.model for row in rows} == {"deepseek-flash"}
    assert {row.category for row in rows} == {"LLM"}
    assert rows[0].input_tokens == 5031
    assert rows[0].total_tokens == 5033


@pytest.mark.integration
@pytest.mark.django_db
def test_record_run_usages_is_idempotent():
    """同一轮重复写入不新增行，只更新。"""
    api.record_run_usages([_usage(1)], execution_id="run-dup", model="deepseek-flash")
    again = api.record_run_usages([_usage(1)], execution_id="run-dup", model="deepseek-flash")

    assert again == 1
    assert ModelUsage.objects.filter(execution_id="run-dup").count() == 1


@pytest.mark.integration
@pytest.mark.django_db
def test_record_run_usages_skips_bad_items():
    """非字典项被跳过，其余照常写入，不抛异常。"""
    written = api.record_run_usages(
        ["不是字典", _usage(3)], execution_id="run-mixed", model="deepseek-flash"
    )

    assert written == 1
    assert ModelUsage.objects.filter(execution_id="run-mixed").count() == 1
