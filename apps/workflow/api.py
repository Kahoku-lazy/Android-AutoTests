from __future__ import annotations

"""workflow public API — 目录 + JSON 文档 CRUD / 导入导出."""

__all__ = [
    "build_export_envelope",
    "create_directory",
    "delete_directory",
    "delete_document",
    "export_document",
    "gen_doc_id",
    "get_directory_tree",
    "get_document",
    "import_document_envelope",
    "list_directories_flat",
    "list_documents",
    "move_directory",
    "move_document",
    "serialize_directory",
    "serialize_document",
    "update_directory",
    "upsert_document",
]

import json
import random
import string

from datetime import datetime
from typing import Any

from django.db import IntegrityError

from .models import WorkflowDirectory, WorkflowDocument

FORMAT_V1 = "workflow-doc-v1"


def gen_doc_id(doc_type: str) -> str:
    """WF-PF|TC-YYYYMMDD-HHMMSS-XXXX — 全局唯一."""
    prefix = "PF" if doc_type == WorkflowDocument.TYPE_PAGE_FLOW else "TC"
    now = datetime.now()
    suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
    candidate = f"WF-{prefix}-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{suffix}"
    # 极低概率碰撞时重试
    for _ in range(8):
        if not WorkflowDocument.objects.filter(doc_id=candidate).exists():
            return candidate
        suffix = "".join(random.choices(string.ascii_uppercase + string.digits, k=4))
        candidate = f"WF-{prefix}-{now.strftime('%Y%m%d')}-{now.strftime('%H%M%S')}-{suffix}"
    return f"WF-{prefix}-{now.strftime('%Y%m%d%H%M%S%f')}-{suffix}"


def _parse_config(raw: str | dict | list | None) -> Any:
    if raw is None or raw == "":
        return {}
    if isinstance(raw, (dict, list)):
        return raw
    try:
        return json.loads(raw)
    except Exception:
        return {}


def serialize_directory(d: WorkflowDirectory) -> dict:
    return {
        "id": d.id,
        "name": d.name,
        "parent_id": d.parent_id,
        "sort_order": d.sort_order,
        "created_at": d.created_at.isoformat() if d.created_at else "",
        "updated_at": d.updated_at.isoformat() if d.updated_at else "",
        "doc_count": d.documents.count(),
    }


def serialize_document(doc: WorkflowDocument, *, include_config: bool = True) -> dict:
    data = {
        "id": doc.id,
        "doc_id": doc.doc_id,
        "title": doc.title,
        "doc_type": doc.doc_type,
        "directory_id": doc.directory_id,
        "description": doc.description or "",
        "created_at": doc.created_at.isoformat() if doc.created_at else "",
        "updated_at": doc.updated_at.isoformat() if doc.updated_at else "",
    }
    if include_config:
        data["config"] = _parse_config(doc.config_json)
    return data


def build_export_envelope(doc: WorkflowDocument) -> dict:
    return {
        "format": FORMAT_V1,
        "doc_id": doc.doc_id,
        "doc_type": doc.doc_type,
        "title": doc.title,
        "description": doc.description or "",
        "directory_id": doc.directory_id,
        "exported_at": datetime.now().isoformat(),
        "config": _parse_config(doc.config_json),
    }


# ── Directories ──


def list_directories_flat() -> list[dict]:
    return [serialize_directory(d) for d in WorkflowDirectory.objects.order_by("sort_order", "id")]


def get_directory_tree() -> list[dict]:
    def build(node: WorkflowDirectory) -> dict:
        children = [build(c) for c in node.children.all().order_by("sort_order", "id")]
        docs = [
            {
                "doc_id": x.doc_id,
                "title": x.title,
                "doc_type": x.doc_type,
                "updated_at": x.updated_at.isoformat() if x.updated_at else "",
            }
            for x in node.documents.all().order_by("title")
        ]
        return {
            **serialize_directory(node),
            "children": children,
            "documents": docs,
        }

    roots = WorkflowDirectory.objects.filter(parent__isnull=True).order_by("sort_order", "id")
    return [build(r) for r in roots]


def create_directory(name: str, parent_id: int | None = None, sort_order: int = 0):
    name = (name or "").strip()
    if not name:
        return False, "目录名不能为空"
    parent = None
    if parent_id is not None:
        try:
            parent = WorkflowDirectory.objects.get(id=parent_id)
        except WorkflowDirectory.DoesNotExist:
            return False, "父目录不存在"
    if WorkflowDirectory.objects.filter(parent=parent, name=name).exists():
        return False, f"同级已存在目录「{name}」"
    d = WorkflowDirectory.objects.create(name=name, parent=parent, sort_order=sort_order)
    return True, serialize_directory(d)


def update_directory(dir_id: int, name: str | None = None, parent_id=None):
    try:
        d = WorkflowDirectory.objects.get(id=dir_id)
    except WorkflowDirectory.DoesNotExist:
        return False, "目录不存在"
    if name is not None:
        name = name.strip()
        if not name:
            return False, "目录名不能为空"
        d.name = name
    if parent_id is not None:
        if parent_id == "":
            d.parent = None
        else:
            try:
                d.parent = WorkflowDirectory.objects.get(id=int(parent_id))
            except (WorkflowDirectory.DoesNotExist, ValueError, TypeError):
                return False, "父目录不存在"
    try:
        d.save()
    except IntegrityError:
        return False, "同级目录名冲突"
    return True, serialize_directory(d)


def delete_directory(dir_id: int):
    try:
        d = WorkflowDirectory.objects.get(id=dir_id)
    except WorkflowDirectory.DoesNotExist:
        return False, "目录不存在"

    # 级联删除子目录内文档（避免 SET_NULL 孤儿残留）
    def collect_ids(node: WorkflowDirectory) -> list[int]:
        ids = [node.id]
        for c in node.children.all():
            ids.extend(collect_ids(c))
        return ids

    dir_ids = collect_ids(d)
    WorkflowDocument.objects.filter(directory_id__in=dir_ids).delete()
    d.delete()
    return True, "ok"


# ── Documents ──


def list_documents(
    *,
    directory_id: int | None = None,
    doc_type: str | None = None,
    include_orphans: bool = True,
) -> list[dict]:
    qs = WorkflowDocument.objects.all().order_by("-updated_at")
    if directory_id is not None:
        qs = qs.filter(directory_id=directory_id)
    elif not include_orphans:
        qs = qs.filter(directory__isnull=False)
    if doc_type:
        qs = qs.filter(doc_type=doc_type)
    return [serialize_document(d, include_config=False) for d in qs]


def get_document(doc_id: str) -> dict | None:
    try:
        doc = WorkflowDocument.objects.get(doc_id=doc_id)
    except WorkflowDocument.DoesNotExist:
        return None
    return serialize_document(doc, include_config=True)


def upsert_document(
    *,
    doc_id: str | None,
    title: str,
    doc_type: str,
    config: Any,
    directory_id: int | None = None,
    description: str = "",
    allow_create: bool = True,
    clear_directory: bool = False,
) -> tuple[bool, Any, int]:
    """Returns (ok, payload_or_error, http_hint_status).

    clear_directory=True → 显式移到根（directory=None）。
    否则 directory_id=None 且 clear_directory=False 时保持原目录（仅更新场景由 view 传已有 id）。
    """
    title = (title or "").strip()
    if not title:
        return False, "标题不能为空", 400
    if doc_type not in (WorkflowDocument.TYPE_PAGE_FLOW, WorkflowDocument.TYPE_TEST_CASE):
        return False, "doc_type 必须是 page_flow 或 test_case", 400

    directory = None
    set_directory = clear_directory or directory_id is not None
    if directory_id is not None:
        try:
            directory = WorkflowDirectory.objects.get(id=directory_id)
        except WorkflowDirectory.DoesNotExist:
            return False, "目录不存在", 400

    config_str = json.dumps(config if config is not None else {}, ensure_ascii=False)

    if doc_id:
        doc_id = doc_id.strip()
        existing = WorkflowDocument.objects.filter(doc_id=doc_id).first()
        if existing:
            existing.title = title
            existing.doc_type = doc_type
            existing.config_json = config_str
            if set_directory:
                existing.directory = directory
            existing.description = description or ""
            existing.save()
            return True, serialize_document(existing), 200
        if not allow_create:
            return False, f"文档不存在: {doc_id}", 404
        if WorkflowDocument.objects.filter(doc_id=doc_id).exists():
            return False, f"doc_id 已存在: {doc_id}", 409
        try:
            doc = WorkflowDocument.objects.create(
                doc_id=doc_id,
                title=title,
                doc_type=doc_type,
                config_json=config_str,
                directory=directory,
                description=description or "",
            )
        except IntegrityError:
            return False, f"doc_id 已存在: {doc_id}", 409
        return True, serialize_document(doc), 201

    # auto id
    new_id = gen_doc_id(doc_type)
    doc = WorkflowDocument.objects.create(
        doc_id=new_id,
        title=title,
        doc_type=doc_type,
        config_json=config_str,
        directory=directory,
        description=description or "",
    )
    return True, serialize_document(doc), 201


def move_document(doc_id: str, directory_id: int | None) -> tuple[bool, Any]:
    """将文档移入目录（directory_id=None 表示根/未分类）。"""
    try:
        doc = WorkflowDocument.objects.get(doc_id=doc_id)
    except WorkflowDocument.DoesNotExist:
        return False, "文档不存在"
    directory = None
    if directory_id is not None:
        try:
            directory = WorkflowDirectory.objects.get(id=directory_id)
        except WorkflowDirectory.DoesNotExist:
            return False, "目录不存在"
    doc.directory = directory
    doc.save(update_fields=["directory", "updated_at"])
    return True, serialize_document(doc, include_config=False)


def move_directory(dir_id: int, parent_id: int | None) -> tuple[bool, Any]:
    """移动目录；禁止移入自身或子孙。"""
    try:
        d = WorkflowDirectory.objects.get(id=dir_id)
    except WorkflowDirectory.DoesNotExist:
        return False, "目录不存在"
    if parent_id is not None:
        if parent_id == dir_id:
            return False, "不能将目录移入自身"
        try:
            parent = WorkflowDirectory.objects.get(id=parent_id)
        except WorkflowDirectory.DoesNotExist:
            return False, "目标目录不存在"
        # 禁止移入子孙
        cur = parent
        while cur:
            if cur.id == dir_id:
                return False, "不能将目录移入其子目录"
            cur = cur.parent
        d.parent = parent
    else:
        d.parent = None
    try:
        d.save()
    except IntegrityError:
        return False, "同级目录名冲突"
    return True, serialize_directory(d)


def delete_document(doc_id: str) -> tuple[bool, str]:
    deleted, _ = WorkflowDocument.objects.filter(doc_id=doc_id).delete()
    if not deleted:
        return False, "文档不存在"
    return True, "ok"


def import_document_envelope(payload: dict, *, overwrite: bool = False) -> tuple[bool, Any, int]:
    """
    Import workflow-doc-v1 JSON.
    - doc_id 为空 → 自动生成
    - doc_id 已存在且 overwrite=False → 409
    - overwrite=True → 更新同 id
    """
    if not isinstance(payload, dict):
        return False, "导入内容必须是 JSON 对象", 400

    fmt = payload.get("format") or FORMAT_V1
    if fmt not in (FORMAT_V1, "testcase-scratch-v1"):
        # 仍允许无 format 的裸对象（需有 doc_type + config/blocks）
        pass

    doc_type = payload.get("doc_type")
    config = payload.get("config")
    title = payload.get("title") or payload.get("name") or ""

    # 兼容旧前端导出 testcase-scratch-v1
    if fmt == "testcase-scratch-v1" or (not doc_type and isinstance(payload.get("blocks"), list)):
        doc_type = WorkflowDocument.TYPE_TEST_CASE
        config = {
            "format": "testcase-scratch-v1",
            "name": payload.get("name") or title,
            "package_name": payload.get("package_name") or "",
            "blocks": payload.get("blocks") or [],
            "flat_steps": payload.get("flat_steps") or [],
        }
        title = title or payload.get("name") or "导入的用例"

    # 兼容页面流裸 snapshot
    if not doc_type and ("nodes" in payload or (isinstance(config, dict) and "nodes" in config)):
        doc_type = WorkflowDocument.TYPE_PAGE_FLOW
        if config is None:
            config = {
                "name": payload.get("name") or title or "导入的页面流",
                "version": payload.get("version") or "1.0",
                "nodes": payload.get("nodes") or [],
                "links": payload.get("links") or [],
            }

    if doc_type not in (WorkflowDocument.TYPE_PAGE_FLOW, WorkflowDocument.TYPE_TEST_CASE):
        return False, "无法识别 doc_type（page_flow / test_case）", 400
    if config is None:
        config = {}
    if not title:
        title = "导入的文档"

    doc_id = (payload.get("doc_id") or "").strip() or None
    directory_id = payload.get("directory_id")
    description = payload.get("description") or ""

    if doc_id and WorkflowDocument.objects.filter(doc_id=doc_id).exists() and not overwrite:
        return False, f"doc_id 已存在，禁止重复导入: {doc_id}", 409

    if doc_id and overwrite:
        ok, result, status = upsert_document(
            doc_id=doc_id,
            title=title,
            doc_type=doc_type,
            config=config,
            directory_id=directory_id,
            description=description,
            allow_create=True,
        )
        return ok, result, status

    if doc_id:
        # create only if unique
        ok, result, status = upsert_document(
            doc_id=doc_id,
            title=title,
            doc_type=doc_type,
            config=config,
            directory_id=directory_id,
            description=description,
            allow_create=True,
        )
        return ok, result, status

    ok, result, status = upsert_document(
        doc_id=None,
        title=title,
        doc_type=doc_type,
        config=config,
        directory_id=directory_id,
        description=description,
    )
    return ok, result, status


def export_document(doc_id: str) -> tuple[bool, Any]:
    try:
        doc = WorkflowDocument.objects.get(doc_id=doc_id)
    except WorkflowDocument.DoesNotExist:
        return False, "文档不存在"
    return True, build_export_envelope(doc)
