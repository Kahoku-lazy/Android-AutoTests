"""
文件名: ➡️ catalog.py 🏁
路径: ➡️ engines/agents/rag/catalog.py 🏁
模块功能：➡️ 装载知识库目录，并校验库名与资料目录隔离 🏁
Python 调试：➡️ python -m engines.agents.rag.catalog 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. KnowledgeBaseSpec: 一个知识库的名称、说明、资料目录和启用状态。
2. load_knowledge_catalog(): 从 knowledge_bases.yaml 装载目录并校验隔离。
🏁
关联模块：➡️
1. engines.utils.io_files: 导入 YAMLFileIO，读取知识库目录
🏁
测试：➡️
1. tests/engines/agents/unit/test_rag_catalog.py: 库名、目录冲突和禁用库
🏁
"""

from __future__ import annotations

import re

from dataclasses import dataclass
from pathlib import Path
from typing import Final

from engines.utils.io_files import YAMLFileIO

DEFAULT_CATALOG_PATH: Final[Path] = (
    Path(__file__).resolve().parents[1] / "config" / "data" / "knowledge_bases.yaml"
)
_NAME_RE: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z][A-Za-z0-9_]*$")


@dataclass(frozen=True)
class KnowledgeBaseSpec:
    """
    一个本地知识库。

    Attributes:
        name: 库名，同时作为向量集合名。
        description: 给探针和后续工具展示的说明。
        data_dir: 只读资料目录。
        enabled: 是否参与索引和检索。
    """

    name: str
    description: str
    data_dir: Path
    enabled: bool


def load_knowledge_catalog(path: str | Path | None = None) -> tuple[KnowledgeBaseSpec, ...]:
    """
    装载知识库目录。

    Args:
        path: 目录文件；None 时读取默认的 knowledge_bases.yaml。

    Returns:
        按文件顺序排列的知识库规格。

    Raises:
        ValueError: 文件结构、库名、字段或资料目录隔离不合法。
    """
    catalog_path = Path(path) if path is not None else DEFAULT_CATALOG_PATH
    raw = YAMLFileIO.read_yaml(catalog_path)
    if not isinstance(raw, dict) or not raw:
        raise ValueError(f"知识库目录必须是非空映射：{catalog_path}")
    specs = tuple(
        _parse_entry(str(name), value, catalog_path.parent) for name, value in raw.items()
    )
    _reject_overlapping_dirs(specs)
    return specs


def _parse_entry(name: str, raw: object, base_dir: Path) -> KnowledgeBaseSpec:
    """
    解析一个库条目。

    Args:
        name: 库名。
        raw: 库表中的原始条目。
        base_dir: 相对资料目录的解析基准。

    Returns:
        知识库规格。

    Raises:
        ValueError: 库名、字段或资料目录不合法。
    """
    if not _NAME_RE.fullmatch(name):
        raise ValueError(f"知识库名不合法：{name}")
    if not isinstance(raw, dict):
        raise ValueError(f"{name}: 知识库条目必须是映射")
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
    return KnowledgeBaseSpec(
        name=name,
        description=description,
        data_dir=_resolve_dir(data_dir, base_dir),
        enabled=enabled,
    )


def _resolve_dir(raw: str, base_dir: Path) -> Path:
    """把相对资料目录按库表所在目录解析。"""
    path = Path(raw)
    if not path.is_absolute():
        path = base_dir / path
    return path.resolve()


def _reject_overlapping_dirs(specs: tuple[KnowledgeBaseSpec, ...]) -> None:
    """
    拒绝两个启用库使用相同或互相包含的资料目录。

    Args:
        specs: 已解析的知识库规格。

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
