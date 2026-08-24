"""device-inspector public API — v1.7 快照化跨模块白名单.

Cross-app access: ai_assistant Tool handlers 与 views 只调本白名单函数；
写库收敛本模块（di_snapshots 归属本模块）；元素定位写入经其 api。
"""

__all__ = [
    "capture_snapshot",
    "delete_snapshot",
    "get_page_view",
    "get_snapshot",
    "list_snapshots",
    "save_snapshot_to_elements",
]

import logging

from datetime import datetime

logger = logging.getLogger(__name__)


def capture_snapshot(user_id: str, serial: str, method: str = "both") -> dict:
    """一键获取（dump/OCR/both）→ 快照落库，返回快照全量 JSON。

    方法级降级：both 时单方法失败以成功方法落库（method 记实际值）；
    dump 与 OCR 全部失败不落库（CaptureError 500）。
    """
    from apps.device_pool.api import device

    from .models import Snapshot
    from .service import (
        CaptureError,
        _check_device_available,
        capture_dump_payload,
        capture_ocr_payload,
        capture_page_screenshot,
        ensure_current_device,
    )

    if method not in ("dump", "ocr", "both"):
        raise CaptureError("无效的获取方法", status_code=400)
    _check_device_available(serial)
    ensure_current_device(serial)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    # 页面截图先行：OCR 识别与元素缩略图裁剪均依赖截图文件
    screenshot_path = capture_page_screenshot(device, ts)

    dump_data = None
    ocr_data = None

    if method in ("dump", "both"):
        try:
            dump_data = capture_dump_payload(device, ts)
        except Exception:
            logger.exception("capture dump failed serial=%s", serial)
            if method == "dump":
                _cleanup_capture_files(ts)
                raise CaptureError("获取失败", status_code=500)

    if method in ("ocr", "both"):
        try:
            ocr_data = capture_ocr_payload(device, ts)
        except Exception:
            logger.exception("capture ocr failed serial=%s", serial)
            if method == "ocr":
                _cleanup_capture_files(ts)
                raise CaptureError("OCR 识别失败，请稍后重试", status_code=500)

    if dump_data is None and ocr_data is None:
        _cleanup_capture_files(ts)
        raise CaptureError("获取失败", status_code=500)

    info = device.info()
    effective = "both" if (dump_data and ocr_data) else ("dump" if dump_data else "ocr")
    snapshot = Snapshot.objects.create(
        device_id=None,
        serial=serial,
        method=effective,
        dump_json=dump_data or {},
        ocr_json=ocr_data or {},
        screenshot_path=screenshot_path,
        package=(dump_data or {}).get("package", ""),
        activity=(dump_data or {}).get("activity", ""),
        screen_w=info.get("displayWidth", 0) or 0,
        screen_h=info.get("displayHeight", 0) or 0,
        element_count=(dump_data or {}).get("element_count", 0),
        actionable_count=(dump_data or {}).get("actionable_count", 0),
        ocr_count=(ocr_data or {}).get("ocr_count", 0),
        created_by=user_id,
    )
    try:
        from apps.device_pool.models import Device

        snapshot.device = Device.objects.filter(serial=serial).first()
        snapshot.save(update_fields=["device"])
    except Exception:
        logger.debug("快照关联设备失败 serial=%s", serial)

    return snapshot_to_dict(snapshot)


def list_snapshots(user_id: str, offset: int = 0, limit: int = 100) -> dict:
    """快照列表（创建时间倒序 + 分页）。"""
    from .models import Snapshot

    qs = Snapshot.objects.filter(created_by=user_id).order_by("-created_at")
    total = qs.count()
    items = [snapshot_meta_dict(s) for s in qs[offset : offset + limit]]
    return {"total": total, "items": items}


def get_snapshot(snapshot_id: int) -> dict | None:
    """快照详情全量 JSON；不存在返回 None。"""
    from .models import Snapshot

    snapshot = Snapshot.objects.filter(id=snapshot_id).first()
    if snapshot is None:
        return None
    return snapshot_to_dict(snapshot)


def delete_snapshot(snapshot_id: int) -> bool:
    """删除快照记录 + 截图/缩略图文件；不存在返回 False。"""
    from .models import Snapshot
    from .service import delete_snapshot_files

    snapshot = Snapshot.objects.filter(id=snapshot_id).first()
    if snapshot is None:
        return False

    thumbs_dir_rel = ""
    if snapshot.dump_json and snapshot.dump_json.get("actionable"):
        first_thumb = next(
            (
                e.get("thumbnail_path", "")
                for e in snapshot.dump_json["actionable"]
                if e.get("thumbnail_path")
            ),
            "",
        )
        if first_thumb:
            # thumbs/{ts}/el_0.png → thumbs/{ts}
            parts = first_thumb.split("/")
            if len(parts) >= 3:
                thumbs_dir_rel = "/".join(parts[:3])
    if not thumbs_dir_rel and snapshot.ocr_json and snapshot.ocr_json.get("texts"):
        first_thumb = next(
            (
                t.get("thumbnail_path", "")
                for t in snapshot.ocr_json["texts"]
                if t.get("thumbnail_path")
            ),
            "",
        )
        if first_thumb:
            parts = first_thumb.split("/")
            if len(parts) >= 3:
                thumbs_dir_rel = "/".join(parts[:3])

    delete_snapshot_files(snapshot.screenshot_path, thumbs_dir_rel)
    snapshot.delete()
    return True


def save_snapshot_to_elements(
    snapshot_id: int,
    page_label: str = "",
    folder_path: str = "",
    page_id: int | None = None,
    element_ids=None,
    include_ocr: bool = True,
) -> dict:
    """筛减保存快照到元素定位（经 element_locator.api，契约见 PRD-04 v7.2）。

    Args:
        page_id: 目标已有页面 ID（与 page_label/folder_path 二选一：有 page_id
            为「保存到已有页面」，否则为「新建页面」）。
        element_ids: 勾选的元素索引列表（对应 dump_json.elements 的下标）；空 = 全部。
    """
    from .models import Snapshot

    snapshot = Snapshot.objects.filter(id=snapshot_id).first()
    if snapshot is None:
        raise ValueError("快照不存在")
    if not page_id and not page_label:
        raise ValueError("页面名称不能为空")

    dump = snapshot.dump_json or {}
    elements = dump.get("elements") or []
    if not elements:
        raise ValueError("该快照无元素数据")

    if element_ids:
        selected = [
            elements[i] for i in element_ids if isinstance(i, int) and 0 <= i < len(elements)
        ]
    else:
        selected = elements

    from apps.element_locator.api import import_snapshot_page

    return import_snapshot_page(
        page_label=page_label,
        folder_path=folder_path,
        page_id=page_id,
        package=snapshot.package,
        activity=snapshot.activity,
        screenshot_path=snapshot.screenshot_path,
        ocr_json=snapshot.ocr_json if include_ocr else None,
        snapshot_id=snapshot.id,
        elements=selected,
    )


def get_page_view(page_id: int) -> dict | None:
    """元素定位已保存页面只读视图（供检查器回看）；不存在返回 None。"""
    from apps.element_locator.api import get_page_full

    return get_page_full(page_id)


# ═══════════════════════════════════════════════
# 序列化（快照记录 → JSON）
# ═══════════════════════════════════════════════


def _cleanup_capture_files(ts: str) -> None:
    """capture 失败时清理本批截图与缩略图文件（尽力，失败仅告警）。"""
    from pathlib import Path

    from django.conf import settings

    base = Path(settings.MEDIA_ROOT) / "inspector"
    targets = [base / "shots" / f"capture_{ts}.png", base / "thumbs" / ts]
    for target in targets:
        try:
            if target.is_file():
                target.unlink()
            elif target.is_dir():
                for f in target.iterdir():
                    f.unlink()
                target.rmdir()
        except Exception:
            logger.debug("清理 capture 文件失败: %s", target)


def snapshot_meta_dict(snapshot) -> dict:
    """快照列表行字段。"""
    return {
        "id": snapshot.id,
        "serial": snapshot.serial,
        "method": snapshot.method,
        "package": snapshot.package,
        "element_count": snapshot.element_count,
        "ocr_count": snapshot.ocr_count,
        "created_by": snapshot.created_by,
        "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
    }


def snapshot_to_dict(snapshot) -> dict:
    """快照详情全量 JSON（capture 响应 / 详情端点共用）。"""
    dump = snapshot.dump_json or {}
    ocr = snapshot.ocr_json or {}
    return {
        "snapshot_id": snapshot.id,
        "serial": snapshot.serial,
        "method": snapshot.method,
        "package": snapshot.package,
        "activity": snapshot.activity,
        "screen_w": snapshot.screen_w,
        "screen_h": snapshot.screen_h,
        "element_count": dump.get("element_count", snapshot.element_count),
        "actionable_count": dump.get("actionable_count", snapshot.actionable_count),
        "elements": dump.get("elements", []),
        "actionable": dump.get("actionable", []),
        "ocr_count": ocr.get("ocr_count", snapshot.ocr_count),
        "texts": ocr.get("texts", []),
        "screenshot_path": snapshot.screenshot_path,
        "created_at": snapshot.created_at.isoformat() if snapshot.created_at else None,
    }
