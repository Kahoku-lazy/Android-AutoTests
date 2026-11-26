from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


@dataclass(frozen=True)
class Forbid:
    slug: str
    name: str
    source: list[str]
    forbidden: list[str]
    ignore_imports: list[str]
    allow_indirect: bool
    unmatched_alerting: str


@dataclass(frozen=True)
class Config:
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
    importer: str
    imported: str
    target: str
    file: str
    line: int


@dataclass(frozen=True)
class AllowViolation:
    file: str
    line: int
    imported: str
    usage_module: str
    definition_module: str
    kind: str


@dataclass
class ContractResult:
    slug: str
    name: str
    chains: list[list[tuple[str, str, int]]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def kept(self) -> bool:
        return not self.chains


@dataclass
class Report:
    files_scanned: int = 0
    allow_violations: list[AllowViolation] = field(default_factory=list)
    contracts: list[ContractResult] = field(default_factory=list)
    unused: list[tuple[str, str]] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.allow_violations and not self.unused and all(c.kept for c in self.contracts)
