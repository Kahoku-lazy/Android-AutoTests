"""element-locator 快照导入 API — 供设备检查器 / AI 保存工具调用（PRD-04 v7.2）。

api.py 已接近行数上限，快照导入独立成文件；api.py re-export 本模块函数，
跨 App 仍只 import element_locator.api（防火墙不变）。本文件属于 api 层，
写库收敛于此。
"""

import json

from .models import Element, Page

__all__ = [
    "ImportConflictError",
    "get_page_full",
    "import_snapshot_page",
]


class ImportConflictError(Exception):
    """快照导入冲突（同级重名 / 目录层级超限）→ 调用方映射 HTTP 409。"""


def _resolve_folder(folder_path: str, *, directory_id: int | None = None) -> int | None:
    """按「/」切段在 Android 项目下查找或创建 LocatorDirectory；返回目录 ID。

    若传入 directory_id，以其为起点继续解析相对路径；二者皆空则挂项目根。

    Raises:
        ImportConflictError: 目录层级超限
    """
    from .api_projects import ensure_system_projects, get_project_by_code
    from .models import LocatorDirectory

    ensure_system_projects()
    project = get_project_by_code(code="android")
    if project is None:
        raise ImportConflictError("Android 项目不存在")

    parent_id = directory_id
    if parent_id is not None:
        parent = LocatorDirectory.objects.filter(id=parent_id, project=project).first()
        if parent is None:
            raise ImportConflictError("目标目录不存在")

    if not folder_path:
        return parent_id

    MAX_DEPTH = 20
    depth = 0
    if parent_id is not None:
        cur = parent_id
        while cur is not None:
            depth += 1
            cur = (
                LocatorDirectory.objects.filter(id=cur).values_list("parent_id", flat=True).first()
            )

    for segment in [s.strip() for s in folder_path.split("/") if s.strip()]:
        depth += 1
        if depth > MAX_DEPTH:
            raise ImportConflictError(f"目录最多嵌套 {MAX_DEPTH} 层")
        node = LocatorDirectory.objects.filter(
            project=project, name=segment, parent_id=parent_id
        ).first()
        if node is None:
            node = LocatorDirectory.objects.create(
                project=project, name=segment, parent_id=parent_id
            )
        parent_id = node.id
    return parent_id


def import_snapshot_page(
    *,
    page_label: str = "",
    folder_path: str = "",
    directory_id: int | None = None,
    page_id: int | None = None,
    package: str = "",
    activity: str = "",
    screenshot_path: str = "",
    ocr_json: dict | None = None,
    snapshot_id: int | None = None,
    elements: list[dict] | None = None,
    device=None,
) -> dict:
    """快照导入：新建页面（自动建目录 + 页面）或写入已有页面（page_id）+ 元素 upsert。

    两种模式：
      - 新建：page_label + folder_path / directory_id（目录按 LocatorDirectory）
      - 已有：page_id（页面已存在，元素 upsert 追加；截图/OCR/溯源仅在页面为空时补全）

    元素按 (page, resource_id, bounds) upsert（同现有去重口径）。
    返回 {"saved", "updated", "skipped", "page_id"}。

    Raises:
        ValueError: page_label 空（新建模式）/ elements 空 / page_id 无效
        ImportConflictError: 同级重名 / 目录层级超限
    """
    elements = elements or []
    if not elements:
        raise ValueError("元素数据不能为空")

    if page_id:
        page = Page.objects.filter(id=page_id, is_folder=False).first()
        if page is None:
            raise ValueError("目标页面不存在")
        # 补全缺失的页面级数据（已有内容不覆盖）
        update_fields = []
        if not page.screenshot_path and screenshot_path:
            page.screenshot_path = screenshot_path
            update_fields.append("screenshot_path")
        if not page.ocr_json and ocr_json:
            page.ocr_json = ocr_json
            update_fields.append("ocr_json")
        if page.snapshot_id is None and snapshot_id:
            page.snapshot_id = snapshot_id
            update_fields.append("snapshot_id")
        if update_fields:
            page.save(update_fields=update_fields)
    else:
        if not page_label:
            raise ValueError("页面名称不能为空")
        dir_id = _resolve_folder(folder_path, directory_id=directory_id)

        existing = Page.objects.filter(
            label=page_label, directory_id=dir_id, is_folder=False
        ).first()
        if existing:
            raise ImportConflictError(f"同级页面「{page_label}」已存在")

        page = Page.objects.create(
            device=device,
            parent_id=None,
            directory_id=dir_id,
            is_folder=False,
            label=page_label,
            package=package,
            activity=activity,
            screenshot_path=screenshot_path,
            ocr_json=ocr_json or {},
            snapshot_id=snapshot_id,
            element_count=len(elements),
        )

    saved = updated = skipped = 0
    for e in elements:
        alias = (
            (e.get("alias") or "").strip()
            or (e.get("text") or "").strip()
            or (e.get("resource_id") or "").strip()
        )
        fields = {
            "class_name": e.get("class_name", ""),
            "text_val": e.get("text", ""),
            "content_desc": e.get("content_desc", ""),
            "resource_id": e.get("resource_id", ""),
            "bounds": e.get("bounds", ""),
            "xpath_candidates": json.dumps(e.get("xpaths", []), ensure_ascii=False),
            "x": int(e.get("x") or 0),
            "y": int(e.get("y") or 0),
            "width": int(e.get("width") or 0),
            "height": int(e.get("height") or 0),
            "depth": int(e.get("depth") or 0),
            "index": str(e.get("index") or ""),
            "clickable": bool(e.get("clickable", False)),
            "enabled": bool(e.get("enabled", False)),
            "scrollable": bool(e.get("scrollable", False)),
            "checked": bool(e.get("checked", False)),
            "thumbnail_path": e.get("thumbnail_path", ""),
            "alias": alias,
        }
        prev = Element.objects.filter(
            page=page,
            resource_id=fields["resource_id"],
            bounds=fields["bounds"],
        ).first()
        if prev:
            for k, v in fields.items():
                setattr(prev, k, v)
            prev.save()
            updated += 1
        else:
            Element.objects.create(page=page, **fields)
            saved += 1

    page.element_count = Element.objects.filter(page=page).count()
    page.save(update_fields=["element_count"])
    return {"saved": saved, "updated": updated, "skipped": skipped, "page_id": page.id}


def get_page_full(page_id: int) -> dict | None:
    """元素定位已保存页面只读视图（供设备检查器回看）；不存在返回 None。"""
    page = Page.objects.filter(id=page_id, is_folder=False).first()
    if page is None:
        return None
    elements = list(Element.objects.filter(page=page).order_by("id"))
    return {
        "page_id": page.id,
        "label": page.label,
        "package": page.package,
        "activity": page.activity,
        "screenshot_path": page.screenshot_path,
        "element_count": page.element_count,
        "ocr_json": page.ocr_json or None,
        "elements": [_element_dict(e) for e in elements],
    }


def _element_dict(el: Element) -> dict:
    """元素模型 → dict（xpath_candidates 解析为 list）。"""
    try:
        xpaths = json.loads(el.xpath_candidates or "[]")
    except json.JSONDecodeError:
        xpaths = []
    return {
        "id": el.id,
        "class_name": el.class_name,
        "text_val": el.text_val,
        "content_desc": el.content_desc,
        "resource_id": el.resource_id,
        "bounds": el.bounds,
        "xpaths": xpaths,
        "x": el.x,
        "y": el.y,
        "width": el.width,
        "height": el.height,
        "depth": el.depth,
        "index": el.index,
        "clickable": el.clickable,
        "enabled": el.enabled,
        "scrollable": el.scrollable,
        "checked": el.checked,
        "thumbnail_path": el.thumbnail_path,
        "alias": el.alias,
        "is_test_point": el.is_test_point,
    }
