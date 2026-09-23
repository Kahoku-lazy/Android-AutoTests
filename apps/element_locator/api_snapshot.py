"""element-locator 快照导入 API — 供设备检查器 / AI 保存工具调用。

api.py 已接近行数上限，快照导入独立成文件；api.py re-export 本模块函数，
跨 App 仍只 import element_locator.api（防火墙不变）。本文件属于 api 层，
写库收敛于此。
"""

import hashlib
import logging
import re
import shutil

from pathlib import Path

from django.conf import settings

from .models import Element, Page

logger = logging.getLogger(__name__)

# 元素定位自有媒体目录（相对 MEDIA_ROOT）：导入时把检查器媒体复制到这里，
# 两个模块的资产不再共命（删快照不再影响已保存页面）。
_LOCATOR_MEDIA_DIR = "locator/pages"

# 资源 ID 作为文件名时的安全化：只保留跨平台通杀字符
_UNSAFE_FILENAME_CHARS = re.compile(r"[^A-Za-z0-9_.-]")

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


def _media_filename(resource_id: str, bounds: str) -> str:
    """元素缩略图副本的文件名：由 upsert 键 (resource_id, bounds) 派生。

    命名必须与 upsert 键同源——若按元素序号命名，同一页面二次导入且元素集合/顺序变化时，
    序号文件会被另一个元素覆盖，而只存在于首轮的行仍指向该文件，导致串图。
    """
    safe = _UNSAFE_FILENAME_CHARS.sub("_", resource_id or "").strip("_")[:32] or "el"
    digest = hashlib.sha1(f"{resource_id}|{bounds}".encode()).hexdigest()[:8]
    return f"el_{safe}_{digest}.png"


def _copy_into_locator(rel_path: str, dest_rel: str) -> str:
    """把媒体复制到元素定位自有目录，返回记录应保存的相对路径。

    - 空路径 → 空
    - 已在元素定位自有目录下 → 原样返回（重复导入幂等）
    - 源文件缺失 → 返回空路径并告警（既不指向检查器媒体，也不指向不存在的副本）
    - 复制失败 → 返回空路径并告警（元素数据是主产物，不因媒体失败丢掉整次导入）
    """
    if not rel_path:
        return ""
    if rel_path.startswith(_LOCATOR_MEDIA_DIR + "/"):
        return rel_path
    source = Path(settings.MEDIA_ROOT) / rel_path
    if not source.is_file():
        logger.warning("导入元素定位时源缩略图不存在，留空: %s", rel_path)
        return ""
    try:
        dest = Path(settings.MEDIA_ROOT) / dest_rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, dest)
    except OSError:
        logger.warning(
            "导入元素定位时复制缩略图失败，留空: %s -> %s",
            rel_path,
            dest_rel,
            exc_info=True,
        )
        return ""
    return dest_rel


def import_snapshot_page(
    *,
    page_label: str = "",
    folder_path: str = "",
    directory_id: int | None = None,
    page_id: int | None = None,
    package: str = "",
    activity: str = "",
    ocr_json: dict | None = None,
    snapshot_id: int | None = None,
    elements: list[dict] | None = None,
    device=None,
) -> dict:
    """快照导入：新建页面（自动建目录 + 页面）或写入已有页面（page_id）+ 元素 upsert。

    两种模式：
      - 新建：page_label + folder_path / directory_id（目录按 LocatorDirectory）
      - 已有：page_id（页面已存在，元素 upsert 追加；OCR/溯源仅在页面为空时补全）

    不保存也不关联整屏截图：页面 `screenshot_path` 保持为空，元素缩略图按各元素的去重键复制副本。

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
        flags = e.get("flags") or {}
        fields = {
            "seq": int(e.get("seq") or 0),
            "alias": alias,
            "text_val": e.get("text", ""),
            "primary_xpath": e.get("primary_xpath", "") or "",
            "primary_stable": bool(e.get("primary_stable", False)),
            "resource_id": e.get("resource_id", ""),
            "bounds": e.get("bounds", ""),
            "clickable": bool(flags.get("clickable", False)),
            "long_clickable": bool(flags.get("long_clickable", False)),
            "scrollable": bool(flags.get("scrollable", False)),
            "checkable": bool(flags.get("checkable", False)),
            "checked": bool(flags.get("checked", False)),
            "enabled": bool(flags.get("enabled", False)),
            "focusable": bool(flags.get("focusable", False)),
            "thumbnail_path": "",
        }
        thumb_src = (e.get("thumbnail_path") or "").strip()
        if thumb_src:
            fields["thumbnail_path"] = _copy_into_locator(
                thumb_src,
                f"{_LOCATOR_MEDIA_DIR}/{page.id}/"
                f"{_media_filename(fields['resource_id'], fields['bounds'])}",
            )
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
    """元素模型 → dict（收敛口径：呈现字段 + 去重键）。"""
    return {
        "id": el.id,
        "alias": el.alias,
        "text_val": el.text_val,
        "resource_id": el.resource_id,
        "bounds": el.bounds,
        "seq": el.seq,
        "primary_xpath": el.primary_xpath,
        "primary_stable": el.primary_stable,
        "thumbnail_path": el.thumbnail_path,
        "clickable": el.clickable,
        "long_clickable": el.long_clickable,
        "scrollable": el.scrollable,
        "checkable": el.checkable,
        "checked": el.checked,
        "enabled": el.enabled,
        "focusable": el.focusable,
        "is_test_point": el.is_test_point,
    }
