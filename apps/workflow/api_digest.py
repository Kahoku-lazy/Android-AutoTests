"""workflow AI 数据出口 — 页面流语义摘要查询（只读）.

AI 工具（ai_assistant.tool_registry）只允许 import 本 App 的 ``api.py``，
``api.py`` 从本模块再导出这两个函数。语义构造见 ``semantics.py``。
"""

from __future__ import annotations

import json

from typing import Any

from django.db.models import Q

from .models import WorkflowDocument
from .semantics import build_graph_digest

__all__ = ["get_document_digest", "list_document_summaries"]


def get_document_digest(doc_id: str) -> tuple[bool, Any]:
    """页面流 → AI 语义摘要（只读工具数据出口）。

    返回 (ok, digest|error)。doc 不存在 / 类型不支持 / 配置解析失败
    均显式报错，绝不静默返回空图。
    """
    try:
        doc = WorkflowDocument.objects.get(doc_id=doc_id)
    except WorkflowDocument.DoesNotExist:
        return False, f"文档不存在: {doc_id}"
    if doc.doc_type == WorkflowDocument.TYPE_TEST_CASE:
        return False, "文档类型不支持（仅 page_flow）"
    try:
        cfg = json.loads(doc.config_json) if doc.config_json else {}
    except json.JSONDecodeError as e:
        return False, f"配置解析失败: {e}"
    if not isinstance(cfg, dict):
        return False, "配置必须是 JSON 对象"
    return True, build_graph_digest(cfg, doc)


def list_document_summaries(
    *, query: str = "", directory_id: int | None = None, limit: int = 20
) -> list[dict]:
    """AI 列表工具数据出口：文档摘要（含节点/连线数，不含 config）。"""
    qs = WorkflowDocument.objects.filter(doc_type=WorkflowDocument.TYPE_PAGE_FLOW)
    if directory_id is not None:
        qs = qs.filter(directory_id=directory_id)
    if query:
        qs = qs.filter(Q(title__icontains=query) | Q(doc_id__icontains=query))
    qs = qs.select_related("directory").order_by("-updated_at")[:limit]

    rows: list[dict] = []
    for d in qs:
        rows.append(
            {
                "doc_id": d.doc_id,
                "title": d.title,
                "directory_id": d.directory_id,
                "directory_name": d.directory.name if d.directory else "",
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
