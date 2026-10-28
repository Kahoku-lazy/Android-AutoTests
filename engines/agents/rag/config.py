"""
python -m 调试路径: engines.agents.rag.config

本模块的业务功能如下：
1. RagConfig: RAG 数据目录、索引目录、嵌入模型、切块与检索参数。
2. load_rag_config(): 从环境变量读取并做基本归一化。

本模块只读配置，不创建索引、不调用模型。
"""

from __future__ import annotations

import os

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

_REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
DEFAULT_DATA_DIR: Final[str] = r"D:\Govee\data\rag_data"
DEFAULT_INDEX_DIR: Final[str] = "data/rag_index"
DEFAULT_COLLECTION: Final[str] = "voice_knowledge"
DEFAULT_EMBEDDING_MODEL: Final[str] = "text-embedding-v4"
DEFAULT_EMBEDDING_DIMENSIONS: Final[int] = 1024
DEFAULT_CHUNK_SIZE: Final[int] = 400
DEFAULT_CHUNK_OVERLAP: Final[int] = 60
DEFAULT_TOP_K: Final[int] = 4
DEFAULT_SCORE_THRESHOLD: Final[float] = 0.55
DEFAULT_MAX_CONTEXT_CHARS: Final[int] = 3000


@dataclass(frozen=True)
class RagConfig:
    """
    RAG 配置。

    Attributes:
        enabled: 是否启用 RAG。
        data_dir: 资料目录（只读）。
        index_dir: 本地索引目录。
        collection: 向量集合名。
        api_key: 嵌入模型密钥；repr 中隐藏。
        embedding_model: 嵌入模型名。
        embedding_dimensions: 向量维度。
        chunk_size: 每块近似 token 数。
        chunk_overlap: 相邻块重叠 token 数。
        top_k: 检索返回条数。
        score_threshold: 余弦相似度下限。
        max_context_chars: 注入上下文的字符上限。
    """

    enabled: bool
    data_dir: Path
    index_dir: Path
    collection: str
    api_key: str = field(repr=False)
    embedding_model: str = DEFAULT_EMBEDDING_MODEL
    embedding_dimensions: int = DEFAULT_EMBEDDING_DIMENSIONS
    chunk_size: int = DEFAULT_CHUNK_SIZE
    chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    top_k: int = DEFAULT_TOP_K
    score_threshold: float = DEFAULT_SCORE_THRESHOLD
    max_context_chars: int = DEFAULT_MAX_CONTEXT_CHARS


def _read(environ: Mapping[str, str] | None, name: str, default: str = "") -> str:
    """读取配置：注入映射优先，否则读进程环境变量。"""
    value = environ.get(name) if environ is not None else os.environ.get(name)
    return (value or default).strip()


def _parse_bool(
    environ: Mapping[str, str] | None,
    name: str,
    default: bool,
) -> bool:
    """解析布尔配置，无法识别时返回默认值。"""
    raw = _read(environ, name).lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _parse_int(
    environ: Mapping[str, str] | None,
    name: str,
    default: int,
    minimum: int,
) -> int:
    """解析整数配置，非法时返回默认值。"""
    try:
        return max(minimum, int(_read(environ, name) or default))
    except (TypeError, ValueError):
        return default


def _parse_float(
    environ: Mapping[str, str] | None,
    name: str,
    default: float,
    minimum: float,
    maximum: float,
) -> float:
    """解析浮点配置，非法时返回默认值。"""
    try:
        value = float(_read(environ, name) or default)
    except (TypeError, ValueError):
        return default
    return min(maximum, max(minimum, value))


def _resolve_path(raw: str, default: str) -> Path:
    """把相对路径按仓库根目录解析。"""
    value = Path(raw or default)
    if not value.is_absolute():
        value = _REPO_ROOT / value
    return value.resolve()


def load_rag_config(environ: Mapping[str, str] | None = None) -> RagConfig:
    """
    从环境变量读取 RAG 配置。

    Args:
        environ: 测试注入的配置映射；None 表示读 `os.environ`。

    Returns:
        RAG 配置；缺少密钥时 `enabled=False`。
    """
    api_key = _read(environ, "EMBEDDING_API_KEY") or _read(
        environ,
        "DASHSCOPE_API_KEY",
    )
    return RagConfig(
        enabled=_parse_bool(environ, "KNOWLEDGE_ASSISTANT_RAG_ENABLED", True) and bool(api_key),
        data_dir=_resolve_path(
            _read(environ, "KNOWLEDGE_ASSISTANT_RAG_DATA_DIR"),
            DEFAULT_DATA_DIR,
        ),
        index_dir=_resolve_path(
            _read(environ, "KNOWLEDGE_ASSISTANT_RAG_INDEX_DIR"),
            DEFAULT_INDEX_DIR,
        ),
        collection=_read(
            environ,
            "KNOWLEDGE_ASSISTANT_RAG_COLLECTION",
            DEFAULT_COLLECTION,
        )
        or DEFAULT_COLLECTION,
        api_key=api_key,
        embedding_model=_read(
            environ,
            "EMBEDDING_MODEL",
            DEFAULT_EMBEDDING_MODEL,
        )
        or DEFAULT_EMBEDDING_MODEL,
        embedding_dimensions=_parse_int(
            environ,
            "EMBEDDING_DIMENSIONS",
            DEFAULT_EMBEDDING_DIMENSIONS,
            1,
        ),
        chunk_size=_parse_int(
            environ,
            "KNOWLEDGE_ASSISTANT_RAG_CHUNK_SIZE",
            DEFAULT_CHUNK_SIZE,
            50,
        ),
        chunk_overlap=_parse_int(
            environ,
            "KNOWLEDGE_ASSISTANT_RAG_CHUNK_OVERLAP",
            DEFAULT_CHUNK_OVERLAP,
            0,
        ),
        top_k=_parse_int(
            environ,
            "KNOWLEDGE_ASSISTANT_RAG_TOP_K",
            DEFAULT_TOP_K,
            1,
        ),
        score_threshold=_parse_float(
            environ,
            "KNOWLEDGE_ASSISTANT_RAG_SCORE_THRESHOLD",
            DEFAULT_SCORE_THRESHOLD,
            -1.0,
            1.0,
        ),
        max_context_chars=_parse_int(
            environ,
            "KNOWLEDGE_ASSISTANT_RAG_MAX_CONTEXT_CHARS",
            DEFAULT_MAX_CONTEXT_CHARS,
            200,
        ),
    )
