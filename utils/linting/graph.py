from __future__ import annotations

import re

from collections import deque
from collections.abc import Iterator

from utils.linting.model import Edge, Forbid


def pattern_matches(node: str, pattern: str) -> bool:
    if pattern == node:
        return True
    regex = re.escape(pattern)
    regex = regex.replace(r"\*\*", r"[A-Za-z0-9_.]+").replace(r"\*", r"[A-Za-z0-9_]+")
    return re.fullmatch(regex, node) is not None


def expand_expression(expr: str, nodes: set[str]) -> set[str]:
    if expr.endswith(".**"):
        prefix = expr[: -len(".**")] + "."
        return {node for node in nodes if node.startswith(prefix)}
    return {node for node in nodes if node == expr or node.startswith(expr + ".")}


def overlaps(left: str, right: str) -> bool:
    left_base = left.removesuffix(".**")
    right_base = right.removesuffix(".**")
    return (
        left_base == right_base
        or left_base.startswith(right_base + ".")
        or right_base.startswith(left_base + ".")
    )


def build_adjacency(edges: list[Edge]) -> dict[str, dict[str, tuple[str, int]]]:
    adjacency: dict[str, dict[str, tuple[str, int]]] = {}
    for edge in edges:
        for node in node_and_ancestors(edge.target):
            adjacency.setdefault(edge.importer, {}).setdefault(node, (edge.file, edge.line))
    return adjacency


def node_and_ancestors(node: str) -> Iterator[str]:
    yield node
    parts = node.split(".")
    for depth in range(1, len(parts)):
        yield ".".join(parts[:depth])


def apply_ignores(
    adjacency: dict[str, dict[str, tuple[str, int]]],
    contract: Forbid,
) -> tuple[dict[str, dict[str, tuple[str, int]]], list[str]]:
    warnings: list[str] = []
    if not contract.ignore_imports:
        return adjacency, warnings

    graph = {importer: dict(imported) for importer, imported in adjacency.items()}
    unmatched: list[str] = []
    for expression in contract.ignore_imports:
        if "->" not in expression:
            raise ValueError(f"禁止合同 {contract.slug} 的 ignore_imports 缺少 '->'：{expression}")
        left, right = (part.strip() for part in expression.split("->", 1))
        matched = False
        for importer, imported_map in graph.items():
            if not pattern_matches(importer, left):
                continue
            for imported in list(imported_map):
                if pattern_matches(imported, right):
                    del imported_map[imported]
                    matched = True
        if not matched:
            unmatched.append(expression)

    for expression in unmatched:
        message = f"禁止合同 {contract.slug}：ignore 表达式没有匹配到任何 import（{expression}）"
        if contract.unmatched_alerting == "error":
            raise ValueError(message)
        if contract.unmatched_alerting == "warn":
            warnings.append(message)
    return graph, warnings


def shortest_chain(
    adjacency: dict[str, dict[str, tuple[str, int]]],
    sources: set[str],
    targets: set[str],
) -> list[str] | None:
    if sources & targets:
        return None

    parents: dict[str, str | None] = {source: None for source in sources}
    queue = deque(sorted(sources))
    while queue:
        current = queue.popleft()
        for neighbour in sorted(adjacency.get(current, {})):
            if neighbour in parents:
                continue
            parents[neighbour] = current
            if neighbour in targets:
                chain = [neighbour]
                while parents[chain[-1]] is not None:
                    chain.append(parents[chain[-1]])  # type: ignore[arg-type]
                return list(reversed(chain))
            queue.append(neighbour)
    return None
