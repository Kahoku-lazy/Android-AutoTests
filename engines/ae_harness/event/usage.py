"""
文件名: ➡️ usage.py 🏁
路径: ➡️ engines/ae_harness/event/usage.py 🏁
模块功能：➡️ 一次模型调用的用量记录形状与按密钥归组：标签 + 轮次 + 时间 + 四类 token 🏁
Python 调试：➡️ python -m engines.ae_harness.event.usage 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 2.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. TokenUsage: 一次模型调用一条的用量记录；标签只有密钥环境变量名，不含明文。
2. UsageSummary: 汇总结果，按密钥环境变量名归组给出次数与四类 token 合计。
3. summarize: 四项 token 分别累加、任何两项互不相加；空标签归到空组不丢弃。
🏁
关联模块：➡️
1. 无本地依赖：只依赖标准库 dataclasses，不导入同包其它模块。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_usage.py: 形状、按密钥归组、缓存不互加、空标签不丢弃
🏁
"""

from __future__ import annotations

from dataclasses import dataclass, field

__all__ = ["EMPTY_LABEL", "TokenUsage", "UsageSummary", "summarize"]

# 没有标签的记录统一归到这个组，避免空串在各处显示成「看起来像漏了」。
EMPTY_LABEL = "-"


@dataclass(frozen=True)
class TokenUsage:
    """
    一次模型调用的用量记录。

    缓存命中 token 是输入 token 的子集，汇总时不得与输入相加；
    缓存写入 token 单独统计，不进入输入、输出或缓存命中任一项。

    Attributes:
        api_key_env: 本次使用的密钥所在的环境变量名；只有名字，没有值。
        round_index: 本次运行中的第几次模型调用，从 1 开始。
        started_at: 起点绝对时刻；运行起点未知时为空串，不伪造。
        ended_at: 终点绝对时刻；运行起点未知时为空串，不伪造。
        input_tokens: 输入 token；已包含缓存命中部分。
        output_tokens: 输出 token。
        cache_input_tokens: 缓存命中 token，是输入 token 的子集。
        cache_creation_input_tokens: 缓存写入 token，不进入其它三项。
    """

    api_key_env: str
    round_index: int
    started_at: str
    ended_at: str
    input_tokens: int
    output_tokens: int
    cache_input_tokens: int
    cache_creation_input_tokens: int

    def as_dict(self) -> dict[str, object]:
        """
        转成可直接落盘或比对的字典。

        Returns:
            字段名到值的映射，字段顺序与数据类一致。
        """
        return {
            "api_key_env": self.api_key_env,
            "round": self.round_index,
            "started_at": self.started_at,
            "ended_at": self.ended_at,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
            "cache_input_tokens": self.cache_input_tokens,
            "cache_creation_input_tokens": self.cache_creation_input_tokens,
        }


@dataclass
class UsageSummary:
    """
    一组用量记录的汇总。

    四项 token 各算各的：缓存命中是输入的子集，缓存写入不进入其它三项。

    Attributes:
        calls: 记录条数，等于模型调用次数。
        input_tokens: 输入 token 合计；已包含缓存命中部分，不额外加缓存。
        output_tokens: 输出 token 合计。
        cache_input_tokens: 缓存命中 token 合计。
        cache_creation_input_tokens: 缓存写入 token 合计。
        by_api_key_env: 密钥环境变量名到该组调用次数的映射；空标签归到 `-`。
    """

    calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    cache_input_tokens: int = 0
    cache_creation_input_tokens: int = 0
    by_api_key_env: dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        """
        转成可直接写进运行汇总的字典。

        Returns:
            与既有汇总 `tokens` 键兼容的字段，外加调用次数与按密钥分布。
        """
        return {
            "calls": self.calls,
            "input": self.input_tokens,
            "output": self.output_tokens,
            "cache_hit": self.cache_input_tokens,
            "cache_creation": self.cache_creation_input_tokens,
            "by_api_key_env": dict(self.by_api_key_env),
        }


def summarize(usages: list[TokenUsage] | tuple[TokenUsage, ...]) -> UsageSummary:
    """
    汇总一组用量记录，按密钥环境变量名归组。

    只做各项独立累加，任何两项之间不相加。

    Args:
        usages: 用量记录序列。

    Returns:
        汇总结果；空序列返回全零。
    """
    result = UsageSummary()
    for item in usages:
        result.calls += 1
        result.input_tokens += item.input_tokens
        result.output_tokens += item.output_tokens
        result.cache_input_tokens += item.cache_input_tokens
        result.cache_creation_input_tokens += item.cache_creation_input_tokens
        key = item.api_key_env or EMPTY_LABEL
        result.by_api_key_env[key] = result.by_api_key_env.get(key, 0) + 1
    return result


if __name__ == "__main__":
    demo = TokenUsage(
        api_key_env="GOVEE_API_KEY",
        round_index=1,
        started_at="2026-11-13_18-00-00.000",
        ended_at="2026-11-13_18-00-03.721",
        input_tokens=5384,
        output_tokens=32,
        cache_input_tokens=4992,
        cache_creation_input_tokens=0,
    )
    print(demo.as_dict())  # noqa: T201 - 模块自测入口
    print(summarize([demo]).as_dict())  # noqa: T201 - 模块自测入口
