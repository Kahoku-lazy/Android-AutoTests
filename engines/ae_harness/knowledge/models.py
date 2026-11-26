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
    model: DashScopeEmbeddingModel
    api_key_env: str
    dimensions: int


def create_embedding_model(
    spec: EmbeddingModelSpec,
    *,
    environ: Mapping[str, str] | None = None,
) -> CreatedEmbedding:
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
    from .config import EmbeddingModelSpec

    spec = EmbeddingModelSpec(provider="dashscope", model_name="text-embedding-v4", dimensions=1024)
    print(create_embedding_model(spec).api_key_env)  # noqa: T201
