"""
文件名: ➡️ models.py 🏁
路径: ➡️ engines/ae_harness/knowledge/models.py 🏁
模块功能：➡️ 按知识库自带配置创建向量模型，并交出用的是哪把密钥 🏁
Python 调试：➡️ python -m engines.ae_harness.knowledge.models 🏁
时间：➡️ 2026-11-15 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-15 🏁
类型: ➡️ 模型配置模块 🏁
简介说明：➡️
1. CreatedEmbedding: 造模型的结果——模型实例 + 密钥环境变量名（只有名字，没有值）。
2. create_embedding_model(): 按一条向量模型配置创建 DashScope 嵌入模型。
🏁
关联模块：➡️
1. engines.ae_harness.knowledge.config: 提供向量模型配置与密钥取值。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_knowledge_config.py: 缺密钥时报可读错误且不泄露明文
🏁
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from agentscope.credential import DashScopeCredential
from agentscope.embedding import DashScopeEmbeddingModel

from .config import EmbeddingModelSpec, load_secret

__all__ = ["CreatedEmbedding", "create_embedding_model"]

_PROVIDER: Final[str] = "dashscope"


@dataclass(frozen=True)
class CreatedEmbedding:
    """
    造向量模型的结果。

    密钥只给环境变量名，不给值；记账按这个名字归组。

    Attributes:
        model: 已创建的嵌入模型实例。
        api_key_env: 本次使用的密钥所在的环境变量名。
        dimensions: 输出向量维度。
    """

    model: DashScopeEmbeddingModel
    api_key_env: str
    dimensions: int


def create_embedding_model(
    spec: EmbeddingModelSpec,
    *,
    environ: Mapping[str, str] | None = None,
) -> CreatedEmbedding:
    """
    按一条向量模型配置创建嵌入模型。

    Args:
        spec: 已校验的向量模型配置。
        environ: 测试注入的进程环境；None 时先查仓库根 .env 再查进程环境。

    Returns:
        模型实例、密钥环境变量名与维度。

    Raises:
        ValueError: provider 不受支持，或该密钥未配置。
    """
    if spec.provider != _PROVIDER:
        raise ValueError(f"只支持 {_PROVIDER} 向量模型，收到 {spec.provider!r}")
    api_key = load_secret(spec.api_key, environ)
    if not api_key:
        raise ValueError(f"没有配置向量模型密钥 {spec.api_key}")
    return CreatedEmbedding(
        model=DashScopeEmbeddingModel(
            credential=DashScopeCredential(api_key=api_key),
            model=spec.model_name,
            dimensions=spec.dimensions,
        ),
        api_key_env=spec.api_key,
        dimensions=spec.dimensions,
    )


if __name__ == "__main__":
    from .config import load_config

    print(create_embedding_model(load_config().embedding).api_key_env)  # noqa: T201
