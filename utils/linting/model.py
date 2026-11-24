"""linting 的数据结构：配置、事实、违规与报告。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Forbid:
    """一条禁止合同（红线），语义对齐禁止边。"""

    slug: str
    name: str
    source: list[str]
    forbidden: list[str]
    ignore_imports: list[str]
    allow_indirect: bool
    unmatched_alerting: str


@dataclass(frozen=True)
class Config:
    """一份已解析的 .linting。"""

    root: Path
    source_roots: list[Path]
    exclude: frozenset[str]
    exclude_raw: list[str]
    exact: bool
    ignore_type_checking: bool
    root_packages: list[str]
    include_external: bool
    modules: dict[str, dict]
    forbids: list[Forbid]


@dataclass(frozen=True)
class Edge:
    """一条静态 import：哪个文件 import 了谁。"""

    importer: str
    imported: str
    target: str
    file: str
    line: int


@dataclass(frozen=True)
class AllowViolation:
    """允许清单违规：模块 import 了没登记的依赖。"""

    file: str
    line: int
    imported: str
    usage_module: str
    definition_module: str
    kind: str


@dataclass
class ContractResult:
    """一条禁止合同的执行结果。"""

    slug: str
    name: str
    chains: list[list[tuple[str, str, int]]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def kept(self) -> bool:
        """没有违规链即为通过。"""
        return not self.chains


@dataclass
class Report:
    """一次检查的全部结果。"""

    files_scanned: int = 0
    allow_violations: list[AllowViolation] = field(default_factory=list)
    contracts: list[ContractResult] = field(default_factory=list)
    unused: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        """允许清单、禁止合同、多余依赖三者都干净才算通过。"""
        return not self.allow_violations and not self.unused and all(c.kept for c in self.contracts)
