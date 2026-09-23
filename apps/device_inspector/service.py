"""device_inspector 服务 — capture 编排。

XPath / OCR 算法已下沉 `algorithms/`，本模块按需 import。
"""

from algorithms.hierarchy import parse_hierarchy_xml
from algorithms.xpath import gen_xpath_candidates, trim_hierarchy

# ═══════════════════════════════════════════════
# v1.7 快照化 — capture 编排（设备可用性 / 截图 / 缩略图落盘）
# ═══════════════════════════════════════════════


# 执行引擎占用前缀：检查器不与执行引擎抢设备
_EXECUTION_OCCUPY_PREFIXES = ("runner-", "ai_agent", "task-", "run-")


class CaptureError(Exception):
    """capture 业务失败（用户可读 message + HTTP 状态码）。"""

    def __init__(self, message: str, status_code: int = 409):
        super().__init__(message)
        self.status_code = status_code


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


def crop_save_thumbnails(
    screenshot_rel: str, jobs: list[tuple[int, tuple[int, int, int, int]]]
) -> dict[int, str]:
    """保存到元素定位时，按 bounds 从快照整屏截图批量裁剪缩略图。

    Args:
        screenshot_rel: 快照整屏截图的相对路径（media 目录内）。
        jobs: [(元素序号, (left, top, right, bottom)), ...]

    Returns:
        {元素序号: 缩略图相对路径}。截图缺失、元素无尺寸或单张裁剪失败时该序号不入表，
        由调用方留空；失败一律写告警日志，不让保存整次失败。
    """
    if not screenshot_rel or not jobs:
        return {}
    import logging

    from pathlib import Path

    from django.conf import settings

    logger = logging.getLogger(__name__)
    source = Path(settings.MEDIA_ROOT) / screenshot_rel
    if not source.is_file():
        logger.warning("保存到元素定位时快照截图不存在，缩略图留空: %s", screenshot_rel)
        return {}

    # 缩略图与快照截图同批（同一 ts 目录），随快照清理流程一并回收
    ts = Path(screenshot_rel).stem.removeprefix("capture_")
    thumbs = _shot_dir() / "thumbs" / ts
    result: dict[int, str] = {}
    for index, box in jobs:
        if box[2] <= box[0] or box[3] <= box[1]:
            continue
        thumbs.mkdir(parents=True, exist_ok=True)
        dest = thumbs / f"save_{index}.png"
        if _crop_thumbnail(str(source), box, str(dest)):
            result[index] = f"inspector/thumbs/{ts}/save_{index}.png"
    return result


def capture_dump_payload(engine, ts: str) -> dict:
    """抓取 UI 层级 + XPath 候选 + 元素缩略图落盘，返回 dump_json。"""
    # 引擎只给层级原始 XML，解析归算法层（引擎不 import algorithms）
    nodes = parse_hierarchy_xml(engine.dump_hierarchy_xml())

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

    # 全量节点索引：未裁剪节点 + 保留标记，不含 XPath 候选（候选是派生数据，查询时按需生成）
    kept_ids = {id(e) for e in elements}
    node_index = [
        {
            "depth": e["depth"],
            "class_name": e["class_name"],
            "text": e["text"],
            "content_desc": e["content_desc"],
            "resource_id": e["resource_id"],
            "index": e["index"],
            "bounds": e["bounds"],
            "x": e["x"],
            "y": e["y"],
            "width": e["width"],
            "height": e["height"],
            "clickable": e["clickable"],
            "enabled": e["enabled"],
            "scrollable": e["scrollable"],
            "checkable": e["checkable"],
            "checked": e["checked"],
            "focusable": e["focusable"],
            "long_clickable": e["long_clickable"],
            "kept_in_snapshot": id(e) in kept_ids,
        }
        for e in nodes
    ]

    return {
        "elements": elements,
        "actionable": actionable,
        "element_count": len(elements),
        "actionable_count": len(actionable),
        "package": package,
        "activity": activity,
        "nodes": node_index,
    }


def capture_ocr_payload(ts: str) -> dict:
    """截屏 OCR 识别 + OCR 缩略图落盘，返回 ocr_json。"""
    from algorithms.vision.ocr import recognize

    shot_abs = str(_shot_dir() / "shots" / f"capture_{ts}.png")
    texts = recognize(shot_abs)

    thumb_dir = _shot_dir() / "thumbs" / ts
    for i, t in enumerate(texts):
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


def _parse_text_filters(raw: str) -> list[str]:
    """「多文本」入参 → 关键词表（英文/中文逗号、顿号、换行分隔；忽略大小写去重）。"""
    keywords: list[str] = []
    normalized = raw.replace("，", ",").replace("、", ",").replace("\n", ",")
    for chunk in normalized.split(","):
        word = chunk.strip().casefold()
        if word and word not in keywords:
            keywords.append(word)
    return keywords


def ocr_page_payload(screenshot_path: str, texts: str = "") -> dict:
    """OCR 识别截图文本 → 文本 + 原始角点 + 归一化中心点（纯函数，无设备交互）。

    Args:
        screenshot_path: 截图文件路径。
        texts: 可选的多文本过滤，命中任一关键词即保留（忽略大小写的子串匹配）；
            英文/中文逗号、顿号、换行都可作分隔符；留空返回整页全部文本。

    `center` 的归一化分母取**截图自身像素尺寸**，与 OCR 坐标处于同一像素空间；
    因此即使截图被缩放，「坐标」与「中心点」仍自洽。
    """
    from PIL import Image

    from algorithms.vision.ocr import recognize

    with Image.open(screenshot_path) as img:
        screen_w, screen_h = img.size
    if screen_w <= 0 or screen_h <= 0:
        raise CaptureError("截图尺寸无效，无法计算归一化中心点", status_code=500)

    keywords = _parse_text_filters(texts)

    regions = []
    for item in recognize(screenshot_path):
        if keywords and not any(word in item["text"].casefold() for word in keywords):
            continue
        coords = item.get("coordinates") or []
        if len(coords) < 2:
            raise CaptureError("OCR 结果缺少角点坐标，无法计算中心点", status_code=500)
        xs = [p[0] for p in coords]
        ys = [p[1] for p in coords]
        regions.append(
            {
                "text": item["text"],
                "confidence": item["confidence"],
                "coordinates": coords,
                "center": [
                    round((min(xs) + max(xs)) / 2 / screen_w, 4),
                    round((min(ys) + max(ys)) / 2 / screen_h, 4),
                ],
            }
        )

    return {"screen_w": screen_w, "screen_h": screen_h, "texts": regions}


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
