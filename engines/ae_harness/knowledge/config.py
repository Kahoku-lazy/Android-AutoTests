from __future__ import annotations

import os
import re

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal, Mapping

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field, ValidationError

_HERE: Final[Path] = Path(__file__).resolve().parent
INDEX_DIR: Final[Path] = _HERE / "index"
ENV_PATH: Final[Path] = _HERE.parents[2] / ".env"
DEFAULT_TOP_K: Final[int] = 4
DEFAULT_SCORE_THRESHOLD: Final[float] = 0.55
DEFAULT_CHUNK_SIZE: Final[int] = 400
DEFAULT_CHUNK_OVERLAP: Final[int] = 60
_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_]*$")

__all__ = [
    "ENV_PATH",
    "INDEX_DIR",
    "EmbeddingModelSpec",
    "KnowledgeBaseSpec",
    "KnowledgeConfig",
    "build_config",
    "load_secret",
]


class EmbeddingModelSpec(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    provider: Literal["dashscope"]
    api_key: Literal["DASHSCOPE_API_KEY"] = "DASHSCOPE_API_KEY"
    model_name: str = Field(min_length=1)
    dimensions: int = Field(default=1024, ge=1)


@dataclass(frozen=True)
class KnowledgeBaseSpec:
    name: str
    description: str
    data_dir: Path
    enabled: bool


@dataclass(frozen=True)
class KnowledgeConfig:
    embedding: EmbeddingModelSpec
    bases: tuple[KnowledgeBaseSpec, ...]
    top_k: int = DEFAULT_TOP_K
    score_threshold: float = DEFAULT_SCORE_THRESHOLD
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    index_epoch: int = 0

    def enabled_bases(self) -> tuple[KnowledgeBaseSpec, ...]:
        return tuple(spec for spec in self.bases if spec.enabled)

    def base(self, name: str) -> KnowledgeBaseSpec | None:
        for spec in self.bases:
            if spec.name == name:
                return spec
        return None


def build_config(
    embedding: Mapping[str, object],
    bases: list[Mapping[str, object]],
    *,
    top_k: int = DEFAULT_TOP_K,
    score_threshold: float = DEFAULT_SCORE_THRESHOLD,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP,
    index_epoch: int = 0,
) -> KnowledgeConfig:
    try:
        spec = EmbeddingModelSpec.model_validate(dict(embedding))
    except ValidationError as exc:
        raise ValueError(_embedding_error(exc)) from exc
    candidates = tuple(_parse_base(item) for item in bases)
    _reject_overlapping_dirs(candidates)
    if top_k < 1 or chunk_size < 1 or chunk_overlap < 0 or chunk_overlap >= chunk_size:
        raise ValueError("检索参数不合法：top_k 与切块大小须为正整数，重叠须小于切块大小")
    if not 0 <= float(score_threshold) <= 1:
        raise ValueError("相似度阈值必须在 0 到 1 之间")
    return KnowledgeConfig(
        embedding=spec,
        bases=candidates,
        top_k=int(top_k),
        score_threshold=float(score_threshold),
        chunk_size=int(chunk_size),
        chunk_overlap=int(chunk_overlap),
        index_epoch=int(index_epoch),
    )


def load_secret(name: str, environ: Mapping[str, str] | None = None) -> str:
    if environ is not None:
        return str(environ.get(name) or "")
    return str(_dotenv().get(name) or os.environ.get(name, ""))


@lru_cache(maxsize=1)
def _dotenv() -> dict[str, str]:
    if not ENV_PATH.exists():
        return {}
    return {str(key): str(value or "") for key, value in dotenv_values(ENV_PATH).items()}


def _embedding_error(exc: ValidationError) -> str:
    fields = ", ".join(str(part) for error in exc.errors() for part in error["loc"]) or "字段"
    return f"向量模型参数不合法：{fields}"


def _parse_base(raw: Mapping[str, object]) -> KnowledgeBaseSpec:
    unknown = set(raw) - {"name", "description", "data_dir", "enabled"}
    if unknown:
        raise ValueError(f"未知字段 {', '.join(sorted(unknown))}")
    name = str(raw.get("name") or "").strip()
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"知识库名不合法：{name}")
    description = str(raw.get("description") or "").strip()
    data_dir = str(raw.get("data_dir") or "").strip()
    if not description or not data_dir:
        raise ValueError(f"{name}: description 和 data_dir 不能为空")
    enabled = raw.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError(f"{name}: enabled 必须是布尔值")
    path = Path(data_dir)
    if not path.is_absolute():
        raise ValueError(f"{name}: 资料目录必须是绝对路径")
    return KnowledgeBaseSpec(
        name=name,
        description=description,
        data_dir=path.resolve(),
        enabled=enabled,
    )


def _reject_overlapping_dirs(specs: tuple[KnowledgeBaseSpec, ...]) -> None:
    enabled = [spec for spec in specs if spec.enabled]
    for index, left in enumerate(enabled):
        for right in enabled[index + 1 :]:
            if left.data_dir == right.data_dir or _contains(left.data_dir, right.data_dir):
                raise ValueError(f"启用库资料目录冲突：{left.name} 与 {right.name}")


def _contains(left: Path, right: Path) -> bool:
    return left in right.parents or right in left.parents


if __name__ == "__main__":
    sample = build_config(
        {"provider": "dashscope", "model_name": "text-embedding-v4", "dimensions": 1024},
        [],
    )
    print(sample.embedding.model_name)  # noqa: T201 - 模块自测：确认参数能组装
