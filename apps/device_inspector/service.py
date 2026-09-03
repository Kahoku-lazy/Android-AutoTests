"""device_inspector 服务 — capture 编排 + XPath 算法 re-export。

L1a 下沉（extract-algorithms-package）：XPath 纯算法已迁 `algorithms/xpath.py`，
此处 re-export 仅保本 App 内部兼容；跨 App 复用请直接 import `algorithms.*`。
"""

from algorithms.layout import classify_structure  # noqa: F401
from algorithms.xpath import (  # noqa: F401
    _LAYOUT_VIEWGROUPS,
    _has_identity,
    _simple_class,
    _specificity,
    gen_xpath_candidates,
    trim_hierarchy,
)

# ═══════════════════════════════════════════════
# v1.7 快照化 — capture 编排（设备可用性 / 截图 / 缩略图落盘）
# ═══════════════════════════════════════════════


# 执行引擎占用前缀：检查器不与执行引擎抢设备（PRD-03 §4.1）
_EXECUTION_OCCUPY_PREFIXES = ("runner-", "ai_agent", "task-", "run-")


class CaptureError(Exception):
    """capture 业务失败（用户可读 message + HTTP 状态码）。"""

    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.status_code = status_code


def _check_device_available(serial: str) -> None:
    """capture 前可用性校验（PRD-03 §4.1 口径）。

    Raises:
        CaptureError: serial 空 / 设备未注册 / 执行引擎占用（409）。
    """
    if not serial:
        raise CaptureError("未选择设备，请先连接设备")
    from apps.device_pool.models import Device

    try:
        Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        raise CaptureError("设备未注册")


def open_inspector_engine(serial: str):
    """校验设备可用 + 打开引擎连接（短连接，调用方用完需 close_engine）。

    替代原 ensure_current_device：不再切换「当前设备」，直接按 serial 打开引擎。
    """
    from apps.device_pool.models import Device
    from engines.device.registry import open_engine

    if not serial:
        raise CaptureError("未选择设备，请先连接设备")
    try:
        dev = Device.objects.get(serial=serial)
    except Device.DoesNotExist:
        raise CaptureError("设备未注册")
    if dev.status == "BUSY" and dev.occupied_by:
        for prefix in _EXECUTION_OCCUPY_PREFIXES:
            if dev.occupied_by.startswith(prefix):
                raise CaptureError(f"设备正被执行引擎占用（{dev.occupied_by}），请等待执行完毕")
    return open_engine(serial, dev.connection_addr or serial)


def _shot_dir():
    """媒体目录下 inspector 根目录（截图/缩略图统一存放）。"""
    from pathlib import Path

    from django.conf import settings

    return Path(settings.MEDIA_ROOT) / "inspector"


def capture_page_screenshot(engine, ts: str) -> str:
    """截图落盘，返回相对路径（media 目录内）。"""

    base = _shot_dir()
    shots = base / "shots"
    shots.mkdir(parents=True, exist_ok=True)
    shot_file = shots / f"capture_{ts}.png"
    engine.screenshot_file(str(shot_file))
    return f"inspector/shots/capture_{ts}.png"


def _crop_thumbnail(source: str, box: tuple[int, int, int, int], dest: str) -> bool:
    """按 box 从 source 裁剪并保存到 dest；失败返回 False。"""
    try:
        from PIL import Image

        img = Image.open(source)
        img.crop(box).save(dest, format="PNG")
        return True
    except Exception:
        import logging

        logging.getLogger(__name__).warning("缩略图裁剪失败: %s → %s", box, dest)
        return False


def capture_dump_payload(engine, ts: str) -> dict:
    """抓取 UI 层级 + XPath 候选 + 元素缩略图落盘，返回 dump_json。"""
    nodes = engine.dump_hierarchy()

    # 生成 XPath 候选（用完整层级算 count，保证定位语义准确）
    for e in nodes:
        if e["resource_id"] or e["text"] or e["content_desc"] or e["clickable"]:
            e["xpaths"] = gen_xpath_candidates(e, nodes)

    elements = trim_hierarchy(nodes)
    actionable = [
        e for e in elements if e["clickable"] or e["text"] or e["resource_id"] or e["content_desc"]
    ]

    # 元素缩略图：按 bounds 从页面截图裁剪落盘
    thumb_dir = _shot_dir() / "thumbs" / ts
    source = str(_shot_dir() / "shots" / f"capture_{ts}.png")
    for i, e in enumerate(actionable):
        w, h = e.get("width", 0), e.get("height", 0)
        if w > 0 and h > 0:
            thumb_dir.mkdir(parents=True, exist_ok=True)
            dest = str(thumb_dir / f"el_{i}.png")
            if _crop_thumbnail(
                source,
                (e["x"], e["y"], e["x"] + w, e["y"] + h),
                dest,
            ):
                e["thumbnail_path"] = f"inspector/thumbs/{ts}/el_{i}.png"
            else:
                e["thumbnail_path"] = ""
        else:
            e["thumbnail_path"] = ""

    package = ""
    activity = ""
    try:
        cur = engine.app_current()
        package = cur.get("package", "")
        activity = cur.get("activity", "")
    except Exception:
        pass

    return {
        "elements": elements,
        "actionable": actionable,
        "element_count": len(elements),
        "actionable_count": len(actionable),
        "package": package,
        "activity": activity,
    }


def capture_ocr_payload(ts: str) -> dict:
    """截屏 OCR 识别 + OCR 缩略图落盘，返回 ocr_json（不含 base64）。"""
    from .ocr import recognize

    shot_abs = str(_shot_dir() / "shots" / f"capture_{ts}.png")
    texts = recognize(shot_abs)

    thumb_dir = _shot_dir() / "thumbs" / ts
    for i, t in enumerate(texts):
        # 丢弃 base64 缩略图，改为文件落盘 + 路径（PRD-03 C-07）
        t.pop("thumbnail", None)
        t.pop("thumbnail_format", None)
        w, h = t.get("width", 0), t.get("height", 0)
        if w > 0 and h > 0:
            thumb_dir.mkdir(parents=True, exist_ok=True)
            dest = str(thumb_dir / f"ocr_{i}.png")
            if _crop_thumbnail(
                shot_abs,
                (t["x"], t["y"], t["x"] + w, t["y"] + h),
                dest,
            ):
                t["thumbnail_path"] = f"inspector/thumbs/{ts}/ocr_{i}.png"
            else:
                t["thumbnail_path"] = ""
        else:
            t["thumbnail_path"] = ""

    return {
        "texts": texts,
        "ocr_count": len(texts),
    }


def analyze_snapshot_payload(snapshot) -> dict:
    """基于已存快照 dump_json 计算结构分区（即时，不落库，无设备交互）。

    复用 `algorithms.layout.classify_structure`（纯规则：位置/class/package）；
    元素的 XPath 已在 capture 时生成并存于 dump_json，`dict(el)` 拷贝时原样保留。
    """
    elements = (snapshot.dump_json or {}).get("elements") or []
    structure = classify_structure(elements, snapshot.screen_h or 0)
    return {
        "package": snapshot.package,
        "activity": snapshot.activity,
        **structure,
    }


def delete_snapshot_files(screenshot_path: str, thumb_dir_rel: str) -> None:
    """删除快照关联的截图与缩略图文件（尽力清理，失败仅告警）。"""
    import logging

    from pathlib import Path

    from django.conf import settings

    logger = logging.getLogger(__name__)
    for rel in (screenshot_path, thumb_dir_rel):
        if not rel:
            continue
        target = Path(settings.MEDIA_ROOT) / rel
        try:
            if target.is_file():
                target.unlink()
            elif target.is_dir():
                for f in target.iterdir():
                    f.unlink()
                target.rmdir()
        except Exception:
            logger.debug("清理快照文件失败: %s", rel)
