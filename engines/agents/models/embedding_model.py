"""
文件名: ➡️ embedding_model.py 🏁
路径: ➡️ engines/agents/models/embedding_model.py 🏁
模块功能：➡️ 嵌入模型：唯一的构造实现，并旁路记录 embedding token 用量 🏁
Python 调试：➡️ python -m engines.agents.models.embedding_model 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. build_embedding_model: 按密钥 / 模型名 / 维度造 DashScope 嵌入模型，可带用量回调
2. _UsageEmbeddingModel: 调用完成后把 token 用量交给回调，失败不打断检索
🏁
关联模块：➡️
1. engines.agents.models.catalog: 导入 get_embedding，取默认模型名与维度
🏁
测试：➡️
1. tests/graybox/unit/test_rag_store.py: 向量库与上下文格式化（不联网）
🏁
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from agentscope.credential import DashScopeCredential
from agentscope.embedding import (
    DashScopeEmbeddingModel,
    EmbeddingResponse,
)

from .catalog import get_embedding

__all__ = ["build_embedding_model"]

_DEFAULT_NAME = "text_embedding_v4"


class _UsageEmbeddingModel(DashScopeEmbeddingModel):
    """在 DashScope 嵌入模型上旁路记录 token 用量。"""

    def __init__(
        self,
        *args: Any,
        usage_sink: Callable[[int], None] | None = None,
        **kwargs: Any,
    ) -> None:
        """构造模型，并保存用量回调。

        Args:
            *args: 传给 DashScopeEmbeddingModel。
            usage_sink: 嵌入 token 用量回调；None 表示不记录。
            **kwargs: 传给 DashScopeEmbeddingModel。
        """
        super().__init__(*args, **kwargs)
        self._usage_sink = usage_sink

    async def __call__(self, *args: Any, **kwargs: Any) -> EmbeddingResponse:
        """调用嵌入模型，并在成功后上报 token 用量。

        Args:
            *args: 传给底层模型。
            **kwargs: 传给底层模型。

        Returns:
            底层模型的嵌入响应。
        """
        response = await super().__call__(*args, **kwargs)
        tokens = getattr(getattr(response, "usage", None), "tokens", None)
        if tokens and self._usage_sink is not None:
            self._usage_sink(int(tokens))
        return response


def build_embedding_model(
    *,
    api_key: str,
    model_name: str | None = None,
    dimensions: int | None = None,
    usage_sink: Callable[[int], None] | None = None,
):
    """造一个 DashScope 嵌入模型。

    Args:
        api_key: DashScope 密钥。
        model_name: 模型名；None 用目录默认值。
        dimensions: 向量维度；None 用目录默认值。
        usage_sink: 嵌入 token 用量回调；None 表示不记录。

    Returns:
        `DashScopeEmbeddingModel` 子类实例。

    Raises:
        KeyError: 目录里没有默认嵌入模型登记。
    """
    ready = get_embedding(_DEFAULT_NAME)
    return _UsageEmbeddingModel(
        credential=DashScopeCredential(api_key=api_key),
        model=model_name or ready.model,
        dimensions=dimensions if dimensions is not None else ready.dimensions,
        usage_sink=usage_sink,
    )
