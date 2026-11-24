"""两套判定：允许清单（每个包能依赖谁）与禁止合同（红线，谁绝不许依赖谁）。"""

from __future__ import annotations

from utils.linting.graph import (
    apply_ignores,
    build_adjacency,
    expand_expression,
    overlaps,
    shortest_chain,
)
from utils.linting.model import (
    AllowViolation,
    Config,
    ContractResult,
    Edge,
    Forbid,
    Report,
)
from utils.linting.scan import collect_edges, nearest_module


def check_allow_list(
    config: Config, edges: list[Edge]
) -> tuple[list[AllowViolation], list[tuple[str, str]]]:
    """按声明模块的 depends_on / cannot_depend_on / utility 裁决，并统计多余依赖。"""
    violations: list[AllowViolation] = []
    used: dict[str, set[str]] = {module_path: set() for module_path in config.modules}

    for edge in edges:
        own = nearest_module(edge.importer, config.modules)
        if not own:
            continue
        module_entry = config.modules[own]
        if module_entry.get("unchecked"):
            continue

        target = nearest_module(edge.imported, config.modules)
        if not target or target == own:
            continue
        if config.modules[target].get("utility"):
            continue
        used[own].add(target)

        forbidden = set(module_entry.get("cannot_depend_on") or [])
        allowed = module_entry.get("depends_on")
        if target in forbidden:
            violation = AllowViolation(
                edge.file, edge.line, edge.imported, own, target, "forbidden"
            )
        elif allowed is not None and target not in allowed:
            violation = AllowViolation(
                edge.file, edge.line, edge.imported, own, target, "undeclared"
            )
        else:
            continue
        if violation not in violations:
            violations.append(violation)

    unused: list[tuple[str, str]] = []
    if config.exact:
        for module_path, module_entry in config.modules.items():
            for declared in module_entry.get("depends_on") or []:
                if declared not in used[module_path]:
                    unused.append((module_path, declared))
    return violations, unused


def check_forbid(config: Config, edges: list[Edge]) -> tuple[list[ContractResult], list[str]]:
    """逐条执行禁止合同：删 ignored 边 → 展开模块 → 直接边或最短链。"""
    results: list[ContractResult] = []
    warnings: list[str] = []
    adjacency = build_adjacency(edges)
    nodes = set(adjacency)
    nodes |= {target for imports in adjacency.values() for target in imports}
    nodes |= {ancestor for node in list(nodes) for ancestor in _ancestors(node)}

    for contract in config.forbids:
        graph, contract_warnings = apply_ignores(adjacency, contract)
        result = ContractResult(contract.slug, contract.name, warnings=contract_warnings)
        warnings.extend(contract_warnings)

        for source_expr in contract.source:
            for forbidden_expr in contract.forbidden:
                if overlaps(source_expr, forbidden_expr):
                    continue
                sources = expand_expression(source_expr, nodes)
                targets = expand_expression(forbidden_expr, nodes)
                if not sources or not targets:
                    continue
                result.chains.extend(_chains_for_pair(graph, sources, targets, contract))

        results.append(result)
    return results, warnings


def _ancestors(node: str) -> set[str]:
    """a.b.c → {a, a.b}，让 `backend.apps` 这类父包能作为节点被匹配。"""
    parts = node.split(".")
    return {".".join(parts[:depth]) for depth in range(1, len(parts))}


def _chains_for_pair(
    adjacency: dict[str, dict[str, tuple[str, int]]],
    sources: set[str],
    targets: set[str],
    contract: Forbid,
) -> list[list[tuple[str, str, int]]]:
    """一对 source/forbidden 表达式之间的违规链；allow_indirect 时只看直接边。"""
    found: list[list[tuple[str, str, int]]] = []

    if contract.allow_indirect:
        for source in sorted(sources):
            for imported, (file, line) in sorted(adjacency.get(source, {}).items()):
                if imported in targets:
                    found.append([(f"{source} -> {imported}", file, line)])
        return found

    chain = shortest_chain(adjacency, sources, targets)
    if chain is None:
        return found

    hops: list[tuple[str, str, int]] = []
    for importer, imported in zip(chain, chain[1:], strict=False):
        file, line = adjacency[importer][imported]
        hops.append((f"{importer} -> {imported}", file, line))
    return [hops]


def check(config: Config) -> Report:
    """跑完整检查：先抽事实，再分别做允许清单与禁止合同。"""
    edges, scanned = collect_edges(config)
    report = Report(files_scanned=scanned)
    report.allow_violations, report.unused = check_allow_list(config, edges)
    report.contracts, warnings = check_forbid(config, edges)
    report.warnings.extend(warnings)
    report.allow_violations.sort(key=lambda item: (item.file, item.line, item.imported))
    report.unused.sort()
    return report
