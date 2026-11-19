"""ae_harness 用量记录形状与按密钥归组。

只测 `event/usage.py`：字段、按密钥环境变量名归组、四项 token 不互加。
不测事件解析（`record`）与报告渲染（`render`）。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.event.usage import EMPTY_LABEL, TokenUsage, summarize

pytestmark = [pytest.mark.unit]


def _usage(
    *,
    api_key_env: str = "OPENAI_API_KEY",
    round_index: int = 1,
    input_tokens: int = 1000,
    output_tokens: int = 200,
    cache_input_tokens: int = 400,
    cache_creation_input_tokens: int = 0,
) -> TokenUsage:
    """造一条用量记录。"""
    return TokenUsage(
        api_key_env=api_key_env,
        round_index=round_index,
        started_at="2026-11-13_18-00-00.000",
        ended_at="2026-11-13_18-00-00.001",
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_input_tokens=cache_input_tokens,
        cache_creation_input_tokens=cache_creation_input_tokens,
    )


def test_record_has_nine_fields():
    """记录共九项：标签、轮次、两个时刻、四类 token 与模型名（v2.0.0 起按角色记模型名）。"""
    payload = _usage().as_dict()
    assert set(payload) == {
        "api_key_env",
        "round",
        "started_at",
        "ended_at",
        "input_tokens",
        "output_tokens",
        "cache_input_tokens",
        "cache_creation_input_tokens",
        "model",
    }
    assert payload["api_key_env"] == "OPENAI_API_KEY"
    assert payload["model"] == ""


def test_cache_is_not_added_into_input():
    """缓存命中是输入的子集：输入合计不得把缓存再加一遍。"""
    usage = _usage(input_tokens=2_494_048, output_tokens=32_462, cache_input_tokens=2_014_592)
    summary = summarize([usage])
    assert summary.input_tokens == 2_494_048
    assert summary.output_tokens == 32_462
    assert summary.cache_input_tokens == 2_014_592
    assert summary.input_tokens != 2_494_048 + 2_014_592


def test_cache_creation_stays_separate():
    """缓存写入单独统计，不混入其它三项。"""
    usage = _usage(
        input_tokens=10, output_tokens=2, cache_input_tokens=0, cache_creation_input_tokens=7
    )
    summary = summarize([usage]).as_dict()
    assert summary["input"] == 10
    assert summary["output"] == 2
    assert summary["cache_hit"] == 0
    assert summary["cache_creation"] == 7


def test_same_key_calls_grouped():
    """同一把密钥的三次调用归到一组并给出合计。"""
    summary = summarize([_usage(round_index=1), _usage(round_index=2), _usage(round_index=3)])
    assert summary.calls == 3
    assert summary.input_tokens == 3000
    assert summary.by_api_key_env == {"OPENAI_API_KEY": 3}


def test_two_keys_grouped_separately():
    """两把密钥各自成组，不合并。"""
    summary = summarize(
        [_usage(api_key_env="OPENAI_API_KEY"), _usage(api_key_env="DEEPSEEK_API_KEY")]
    )
    assert summary.by_api_key_env == {"OPENAI_API_KEY": 1, "DEEPSEEK_API_KEY": 1}
    assert summary.calls == 2


def test_empty_label_kept_in_its_own_group():
    """没有标签的记录仍被计数，归到可识别的空组，不丢弃。"""
    summary = summarize([_usage(api_key_env=""), _usage(api_key_env="")])
    assert summary.calls == 2
    assert summary.input_tokens == 2000
    assert summary.by_api_key_env == {EMPTY_LABEL: 2}


def test_summarize_empty_gives_zero():
    """空序列返回全零，不报错。"""
    summary = summarize([])
    assert summary.calls == 0
    assert summary.as_dict()["by_api_key_env"] == {}
