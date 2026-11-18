"""
文件名: ➡️ usage.py 🏁
路径: ➡️ engines/ae_harness/knowledge/usage.py 🏁
模块功能：➡️ 嵌入用量记录代理：透传模型调用并导出 token 用量事件 🏁
Python 调试：➡️ python -m engines.ae_harness.knowledge.usage 🏁
时间：➡️ 2026-11-18 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-18 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. UsageEvent: 一条嵌入用量事件（模型名、密钥环境变量名、token、耗时、阶段、库名）。
2. UsageRecordingEmbedding: 透传 __call__ 的记录代理；零 token 不产事件；不改返回值。
3. tag_events: 给事件批量打上阶段与库名标签，供检索器在索引/检索后标注。
🏁
关联模块：➡️
1. 无 Harness 内依赖：只依赖 agentscope 与标准库，保证本模块可整目录删除。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_knowledge_usage.py: 代理透传、事件字段、零 token 不记与打标
🏁
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime
from typing import Any

from agentscope.embedding import EmbeddingModelBase, EmbeddingResponse
from agentscope.message import DataBlock, TextBlock

__all__ = ["UsageEvent", "UsageRecordingEmbedding", "tag_events"]


@dataclass(frozen=True)
class UsageEvent:
    """
    一条嵌入用量事件。

    密钥只出现环境变量名，不出现明文；阶段与库名由调用方打标。

    Attributes:
        model: 嵌入模型名。
        api_key_env: 密钥所在的环境变量名。
        tokens: 本次调用消耗的 token 数。
        time: 本次调用耗时（秒）。
        phase: 调用阶段；index 或 retrieve，未打标时为空串。
        base: 调用所属库名；未打标时为空串。
        occurred_at: 事件时间，ISO 格式到毫秒。
    """

    model: str
    api_key_env: str
    tokens: int
    time: float
    phase: str = ""
    base: str = ""
    occurred_at: str = ""

    def as_dict(self) -> dict[str, object]:
        """
        转成可直接序列化的字典。

        Returns:
            七个字段组成的字典。
        """
        return {
            "model": self.model,
            "api_key_env": self.api_key_env,
            "tokens": self.tokens,
            "time": self.time,
            "phase": self.phase,
            "base": self.base,
            "occurred_at": self.occurred_at,
        }


class UsageRecordingEmbedding:
    """
    透传并记录用量的嵌入模型代理。

    只委托 KnowledgeBase 用到的成员（__call__ / dimensions / supports_multimodal），
    返回值原样透传；事件经 drain_events() 取出并清空。

    Attributes:
        api_key_env: 密钥所在的环境变量名；只记名字，不记值。
    """

    def __init__(self, model: EmbeddingModelBase, api_key_env: str) -> None:
        """
        包住真实模型；不做任何 IO。

        Args:
            model: 真实嵌入模型实例。
            api_key_env: 密钥所在的环境变量名。
        """
        self._model = model
        self.api_key_env = api_key_env
        self._events: list[UsageEvent] = []

    @property
    def model(self) -> str:
        """
        嵌入模型名。

        Returns:
            真实模型的模型名。
        """
        return self._model.model

    @property
    def dimensions(self) -> int:
        """
        输出向量维度；委托真实模型。

        Returns:
            真实模型的向量维度。
        """
        return self._model.dimensions

    @property
    def supports_multimodal(self) -> bool:
        """
        是否接受多模态输入；委托真实模型。

        Returns:
            真实模型的多模态支持标记。
        """
        return self._model.supports_multimodal

    async def __call__(
        self,
        inputs: list[str | TextBlock | DataBlock],
        **kwargs: Any,
    ) -> EmbeddingResponse:
        """
        透传一次嵌入调用并记录用量；零 token 不产事件。

        Args:
            inputs: 嵌入输入，原样交给真实模型。
            **kwargs: 透传给真实模型的参数。

        Returns:
            真实模型的响应，原样不改。
        """
        response = await self._model(inputs, **kwargs)
        usage = response.usage
        tokens = int(usage.tokens or 0) if usage is not None else 0
        if tokens > 0:
            self._events.append(
                UsageEvent(
                    model=self._model.model,
                    api_key_env=self.api_key_env,
                    tokens=tokens,
                    time=float(usage.time) if usage is not None else 0.0,
                    occurred_at=datetime.now().isoformat(timespec="milliseconds"),
                )
            )
        return response

    def drain_events(self) -> list[UsageEvent]:
        """
        取出并清空累计的用量事件。

        Returns:
            事件列表，按发生顺序；取走后内部清空。
        """
        events = self._events
        self._events = []
        return events


def tag_events(events: list[UsageEvent], *, phase: str, base: str) -> list[UsageEvent]:
    """
    给事件批量打上阶段与库名标签。

    Args:
        events: 待打标的事件。
        phase: 阶段；index 或 retrieve。
        base: 库名。

    Returns:
        打标后的新事件列表；原事件不变。
    """
    return [replace(event, phase=phase, base=base) for event in events]


if __name__ == "__main__":
    print(  # noqa: T201 - 模块自测：确认事件可序列化
        UsageEvent(
            model="text-embedding-v4", api_key_env="DASHSCOPE_API_KEY", tokens=1, time=0.1
        ).as_dict()
    )
