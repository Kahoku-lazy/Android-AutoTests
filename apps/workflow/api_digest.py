"""workflow AI 数据出口 — 页面流语义摘要查询（只读）.

AI 工具（ai_assistant.tool_registry）只允许 import 本 App 的 ``api.py``，
``api.py`` 从本模块再导出这两个函数。语义构造见 ``semantics.py``。
"""

from __future__ import annotations

import json

from typing import Any

from django.db.models import Q

from .models import WorkflowDirectory, WorkflowDocument
from .semantics import build_graph_digest

__all__ = ["get_document_digest", "list_document_summaries"]

# 目录链深度上限（环保护；正常目录树远小于此）
_MAX_DIR_DEPTH = 32


def _directory_index() -> dict[int, tuple[str, int]]:
    """目录 id → (完整路径, 深度)；一次取数 + 记忆化构链，根目录深度为 1。

    含环保护：异常数据成环时降级为该目录自身名字，不无限递归、不抛错。
    """
    dirs = {d.id: d for d in WorkflowDirectory.objects.all()}
    resolved: dict[int, tuple[str, int]] = {}
    visiting: set[int] = set()

    def resolve(did: int) -> tuple[str, int]:
        cached = resolved.get(did)
        if cached is not None:
            return cached
        node = dirs.get(did)
        if node is None:
            return ("", 0)
        parent = node.parent_id
        if (
            parent is None
            or parent not in dirs
            or did in visiting
            or len(visiting) >= _MAX_DIR_DEPTH
        ):
            out = (node.name, 1)
        else:
            visiting.add(did)
            try:
                parent_path, parent_depth = resolve(parent)
            finally:
                visiting.discard(did)
            out = (f"{parent_path}/{node.name}" if parent_path else node.name, parent_depth + 1)
        resolved[did] = out
        return out

    return {did: resolve(did) for did in dirs}


def get_document_digest(doc_id: str) -> tuple[bool, Any]:
    """页面流 → AI 语义摘要（只读工具数据出口）。

    返回 (ok, digest|error)。doc 不存在 / 类型不支持 / 配置解析失败
    均显式报错，绝不静默返回空图。
    """
    try:
        doc = WorkflowDocument.objects.get(doc_id=doc_id)
    except WorkflowDocument.DoesNotExist:
        return False, f"文档不存在: {doc_id}"
    if doc.doc_type not in WorkflowDocument.SUPPORTED_TYPES:
        return False, "文档类型不支持（仅 page_flow）"
    try:
        cfg = json.loads(doc.config_json) if doc.config_json else {}
    except json.JSONDecodeError as e:
        return False, f"配置解析失败: {e}"
    if not isinstance(cfg, dict):
        return False, "配置必须是 JSON 对象"
    return True, build_graph_digest(cfg, doc)


def list_document_summaries(
    *,
    query: str = "",
    directory_id: int | None = None,
    prototype_id: int | None = None,
    limit: int | None = None,
) -> list[dict]:
    """AI 列表工具数据出口：文档摘要（含节点/连线数与目录层级，不含 config）。

    limit 默认 None = 不限量（调用方要"列出全部"时不必自己猜条数）。
    directory_path/directory_depth 给出文档在目录树中的位置；未归类文档为 ""/0。
    """
    qs = WorkflowDocument.objects.filter(doc_type__in=WorkflowDocument.SUPPORTED_TYPES)
    if prototype_id is not None:
        qs = qs.filter(prototype_id=prototype_id)
    if directory_id is not None:
        qs = qs.filter(directory_id=directory_id)
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(doc_id__icontains=query))
    qs = qs.select_related("directory", "prototype").order_by("-updated_at")
    if limit is not None:
        qs = qs[:limit]

    dir_paths = _directory_index()
    rows: list[dict] = []
    for d in qs:
        path, depth = dir_paths.get(d.directory_id, ("", 0)) if d.directory_id else ("", 0)
        rows.append(
            {
                "doc_id": d.doc_id,
                "title": d.title,
                "prototype_id": d.prototype_id,
                "prototype_name": d.prototype.name if d.prototype else "",
                "directory_id": d.directory_id,
                "directory_name": d.directory.name if d.directory else "",
                "directory_path": path,
                "directory_depth": depth,
                "node_count": _count(d.config_json, "nodes"),
                "link_count": _count(d.config_json, "links"),
                "updated_at": d.updated_at.isoformat() if d.updated_at else "",
            }
        )
    return rows


def _count(config_json: str, key: str) -> int | None:
    """配置中列表字段长度；配置解析失败返回 None（未知），不伪装成 0。"""
    try:
        cfg = json.loads(config_json) if config_json else {}
    except json.JSONDecodeError:
        return None
    if not isinstance(cfg, dict):
        return None
    value = cfg.get(key)
    return len(value) if isinstance(value, list) else 0
