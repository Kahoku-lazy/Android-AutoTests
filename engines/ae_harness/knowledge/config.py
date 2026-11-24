"""
文件名: ➡️ config.py 🏁
路径: ➡️ engines/ae_harness/knowledge/config.py 🏁
模块功能：➡️ 校验调用方传入的向量模型参数、库列表与检索参数 🏁
Python 调试：➡️ python -m engines.ae_harness.knowledge.config 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-15 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. EmbeddingModelSpec: 一条向量模型配置；禁止出现 chat / realtime / tts 字段。
2. KnowledgeBaseSpec: 一个本地知识库的名称、说明、只读资料目录与启用状态。
3. KnowledgeConfig: 向量模型 + 库目录 + 检索与切块参数。
4. build_config(): 校验调用方传入的向量模型、库列表与检索参数。
5. load_secret(): 按环境变量名取密钥，先查仓库根 .env 再查进程环境。
🏁
关联模块：➡️
1. 无 Harness 内依赖：只依赖 dotenv 与标准库，保证本模块可整目录删除。
🏁
测试：➡️
1. 暂无
🏁
"""

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
# 仓库根 .env：knowledge/config.py 往上三级。
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
    """
    一条向量模型配置。

    只允许 dashscope 向量模型；出现未知字段（例如 chat 的 stream）时直接校验失败。

    Attributes:
        provider: 厂商名；本期只允许 dashscope。
        api_key: 密钥所在的环境变量名；只允许 DASHSCOPE_API_KEY。
        model_name: 厂商正式模型名，如 text-embedding-v4。
        dimensions: 输出向量维度。

    Raises:
        ValidationError: 字段缺失、类型不对、出现未知字段，或 provider 不受支持。
    """

    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True, frozen=True)

    provider: Literal["dashscope"]
    api_key: Literal["DASHSCOPE_API_KEY"] = "DASHSCOPE_API_KEY"
    model_name: str = Field(min_length=1)
    dimensions: int = Field(default=1024, ge=1)


@dataclass(frozen=True)
class KnowledgeBaseSpec:
    """
    一个本地知识库。

    Attributes:
        name: 库名，同时作为向量集合名。
        description: 给工具描述与探针展示的说明。
        data_dir: 只读资料目录。
        enabled: 是否参与索引与检索。
    """

    name: str
    description: str
    data_dir: Path
    enabled: bool


@dataclass(frozen=True)
class KnowledgeConfig:
    """
    知识库模块的全部配置。

    Attributes:
        embedding: 本次使用的向量模型。
        bases: 按文件顺序排列的库。
        top_k: 默认返回条数。
        score_threshold: 余弦相似度下限。
        chunk_size: 每块近似 token 数。
        chunk_overlap: 相邻块重叠 token 数。
        index_epoch: 调用方的索引版本；切块参数变化时由调用方加一。
    """

    embedding: EmbeddingModelSpec
    bases: tuple[KnowledgeBaseSpec, ...]
    top_k: int = DEFAULT_TOP_K
    score_threshold: float = DEFAULT_SCORE_THRESHOLD
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    index_epoch: int = 0

    def enabled_bases(self) -> tuple[KnowledgeBaseSpec, ...]:
        """
        返回参与索引与检索的库。

        Returns:
            启用库，顺序与库目录一致。
        """
        return tuple(spec for spec in self.bases if spec.enabled)

    def base(self, name: str) -> KnowledgeBaseSpec | None:
        """
        按库名取一条库规格。

        Args:
            name: 库名。

        Returns:
            库规格；库不存在时为 None。
        """
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
    """
    用调用方传入的参数组装知识库配置。本模块不读配置文件。

    Args:
        embedding: 向量模型参数，只允许 provider / api_key / model_name / dimensions。
        bases: 库列表，每项含 name / description / data_dir / enabled。
        top_k: 默认返回条数。
        score_threshold: 余弦相似度下限。
        chunk_size: 每块近似 token 数。
        chunk_overlap: 相邻块重叠 token 数。
        index_epoch: 调用方的索引版本，随配置原样带回。

    Returns:
        校验后的知识库配置。

    Raises:
        ValueError: 库名非法、字段未知，或两个启用库的资料目录冲突。
        ValidationError: 向量模型参数含未知字段、厂商不受支持或缺字段。
    """
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
    """
    按环境变量名取密钥值。

    先查仓库根 .env，再查进程环境；两处都没有时返回空串。只返回值，不写任何日志。

    Args:
        name: 环境变量名，例如 DASHSCOPE_API_KEY。
        environ: 测试注入的进程环境；None 时读 os.environ。

    Returns:
        密钥值；未配置时为空串。
    """
    if environ is not None:
        return str(environ.get(name) or "")
    return str(_dotenv().get(name) or os.environ.get(name, ""))


@lru_cache(maxsize=1)
def _dotenv() -> dict[str, str]:
    """读仓库根 .env 并缓存；文件不存在时返回空表。"""
    if not ENV_PATH.exists():
        return {}
    return {str(key): str(value or "") for key, value in dotenv_values(ENV_PATH).items()}


def _embedding_error(exc: ValidationError) -> str:
    """把向量模型校验错误收成一句可读原因，指出违规字段。"""
    fields = ", ".join(str(part) for error in exc.errors() for part in error["loc"]) or "字段"
    return f"向量模型参数不合法：{fields}"


def _parse_base(raw: Mapping[str, object]) -> KnowledgeBaseSpec:
    """
    解析一个库条目。

    Args:
        raw: 含 name / description / data_dir / enabled 的映射。

    Returns:
        库规格。

    Raises:
        ValueError: 库名、字段或资料目录不合法。
    """
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
    """
    拒绝两个启用库使用相同或互相包含的资料目录。

    Args:
        specs: 已解析的库规格。

    Raises:
        ValueError: 两个启用库的资料目录冲突。
    """
    enabled = [spec for spec in specs if spec.enabled]
    for index, left in enumerate(enabled):
        for right in enabled[index + 1 :]:
            if left.data_dir == right.data_dir or _contains(left.data_dir, right.data_dir):
                raise ValueError(f"启用库资料目录冲突：{left.name} 与 {right.name}")


def _contains(left: Path, right: Path) -> bool:
    """判断两个目录是否一方包含另一方。"""
    return left in right.parents or right in left.parents


if __name__ == "__main__":
    sample = build_config(
        {"provider": "dashscope", "model_name": "text-embedding-v4", "dimensions": 1024},
        [],
    )
    print(sample.embedding.model_name)  # noqa: T201 - 模块自测：确认参数能组装
