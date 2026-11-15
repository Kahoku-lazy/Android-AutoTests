"""
文件名: ➡️ config.py 🏁
路径: ➡️ engines/ae_harness/knowledge/config.py 🏁
模块功能：➡️ 读知识库自带的两份 yaml：向量模型配置与库目录 🏁
Python 调试：➡️ python -m engines.ae_harness.knowledge.config 🏁
时间：➡️ 2026-11-15 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-15 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. EmbeddingModelSpec: 一条向量模型配置；禁止出现 chat / realtime / tts 字段。
2. KnowledgeBaseSpec: 一个本地知识库的名称、说明、只读资料目录与启用状态。
3. KnowledgeConfig: 向量模型 + 库目录 + 检索与切块参数。
4. load_config(): 读两份 yaml 并校验字段、库名与资料目录隔离。
5. load_secret(): 按环境变量名取密钥，先查仓库根 .env 再查进程环境。
🏁
关联模块：➡️
1. 无 Harness 内依赖：只依赖 yaml、dotenv 与标准库，保证本模块可整目录删除。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_knowledge_config.py: 向量模型字段、库目录隔离与密钥取值
🏁
"""

from __future__ import annotations

import os
import re

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Final, Literal, Mapping

import yaml

from dotenv import dotenv_values
from pydantic import BaseModel, ConfigDict, Field

_HERE: Final[Path] = Path(__file__).resolve().parent
CONFIG_DIR: Final[Path] = _HERE / "config"
MODELS_PATH: Final[Path] = CONFIG_DIR / "models.yaml"
BASES_PATH: Final[Path] = CONFIG_DIR / "knowledge_bases.yaml"
INDEX_DIR: Final[Path] = _HERE / "index"
# 仓库根 .env：knowledge/config.py 往上三级。
ENV_PATH: Final[Path] = _HERE.parents[2] / ".env"
DEFAULT_EMBEDDING: Final[str] = "dashscope_embedding_v4"
DEFAULT_TOP_K: Final[int] = 4
DEFAULT_SCORE_THRESHOLD: Final[float] = 0.55
DEFAULT_CHUNK_SIZE: Final[int] = 400
DEFAULT_CHUNK_OVERLAP: Final[int] = 60
_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[a-z][a-z0-9_]*$")
_DEFAULTS_KEY: Final[str] = "defaults"

__all__ = [
    "BASES_PATH",
    "CONFIG_DIR",
    "DEFAULT_EMBEDDING",
    "ENV_PATH",
    "INDEX_DIR",
    "MODELS_PATH",
    "EmbeddingModelSpec",
    "KnowledgeBaseSpec",
    "KnowledgeConfig",
    "load_config",
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
    """

    embedding: EmbeddingModelSpec
    bases: tuple[KnowledgeBaseSpec, ...]
    top_k: int = DEFAULT_TOP_K
    score_threshold: float = DEFAULT_SCORE_THRESHOLD
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP

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


def load_config(
    *,
    models_path: str | Path | None = None,
    bases_path: str | Path | None = None,
) -> KnowledgeConfig:
    """
    装载向量模型与库目录。

    Args:
        models_path: 向量模型配置文件；None 时用模块自带的 config/models.yaml。
        bases_path: 库目录文件；None 时用模块自带的 config/knowledge_bases.yaml。

    Returns:
        合并后的知识库配置。

    Raises:
        ValueError: 文件结构不合法、库名非法、字段未知，或两个启用库的资料目录冲突。
        ValidationError: 向量模型条目校验不通过。
    """
    models_raw = _read_mapping(models_path, MODELS_PATH)
    bases_raw = _read_mapping(bases_path, BASES_PATH)
    defaults = _parse_defaults(bases_raw.get(_DEFAULTS_KEY))
    embedding_name = str(defaults.get("embedding") or DEFAULT_EMBEDDING)
    raw_model = models_raw.get(embedding_name)
    if not isinstance(raw_model, dict):
        choices = ", ".join(sorted(models_raw)) or "无"
        raise ValueError(f"未知向量模型 {embedding_name!r}；可选：{choices}")
    candidates = tuple(
        _parse_base(str(name), value, Path(bases_path or BASES_PATH).parent)
        for name, value in bases_raw.items()
        if name != _DEFAULTS_KEY
    )
    _reject_overlapping_dirs(candidates)
    return KnowledgeConfig(
        embedding=EmbeddingModelSpec.model_validate(raw_model),
        bases=candidates,
        top_k=int(defaults.get("top_k", DEFAULT_TOP_K)),
        score_threshold=float(defaults.get("score_threshold", DEFAULT_SCORE_THRESHOLD)),
        chunk_size=int(defaults.get("chunk_size", DEFAULT_CHUNK_SIZE)),
        chunk_overlap=int(defaults.get("chunk_overlap", DEFAULT_CHUNK_OVERLAP)),
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


def _read_mapping(path: str | Path | None, default: Path) -> dict:
    """
    读一份 yaml 映射。

    Args:
        path: 显式路径；None 时用 default。
        default: 模块自带的默认路径。

    Returns:
        yaml 顶层映射。

    Raises:
        ValueError: 文件不存在、顶层不是非空映射。
    """
    target = Path(path) if path is not None else default
    if not target.exists():
        raise ValueError(f"知识库配置不存在：{target}")
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"知识库配置必须是非空映射：{target}")
    return raw


def _parse_defaults(raw: object) -> dict:
    """
    解析 defaults 段。

    Args:
        raw: defaults 段的原始值。

    Returns:
        参数字典；缺失时为空字典。

    Raises:
        ValueError: defaults 不是映射，或出现未知键。
    """
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValueError("defaults 必须是映射")
    allowed = {"embedding", "top_k", "score_threshold", "chunk_size", "chunk_overlap"}
    unknown = set(raw) - allowed
    if unknown:
        raise ValueError(f"defaults 未知字段：{', '.join(sorted(unknown))}")
    return raw


def _parse_base(name: str, raw: object, base_dir: Path) -> KnowledgeBaseSpec:
    """
    解析一个库条目。

    Args:
        name: 库名。
        raw: 库表中的原始条目。
        base_dir: 相对资料目录的解析基准。

    Returns:
        库规格。

    Raises:
        ValueError: 库名、字段或资料目录不合法。
    """
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"知识库名不合法：{name}")
    if not isinstance(raw, dict):
        raise ValueError(f"{name}: 库条目必须是映射")
    unknown = set(raw) - {"description", "data_dir", "enabled"}
    if unknown:
        raise ValueError(f"{name}: 未知字段 {', '.join(sorted(unknown))}")
    description = str(raw.get("description") or "").strip()
    data_dir = str(raw.get("data_dir") or "").strip()
    if not description or not data_dir:
        raise ValueError(f"{name}: description 和 data_dir 不能为空")
    enabled = raw.get("enabled", True)
    if not isinstance(enabled, bool):
        raise ValueError(f"{name}: enabled 必须是布尔值")
    path = Path(data_dir)
    if not path.is_absolute():
        path = base_dir / path
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
    print(load_config())  # noqa: T201 - 模块自测：确认两份 yaml 能装载
