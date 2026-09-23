"""device-inspector public API — v1.7 快照化跨模块白名单.

Cross-app access: ai_assistant Tool handlers 与 views 只调本白名单函数；
写库收敛本模块（di_snapshots 归属本模块）；元素定位写入经其 api。
"""

__all__ = [
    "SNAPSHOT_RETENTION",
    "capture_screen",
    "capture_snapshot",
    "clear_snapshots",
    "delete_snapshot",
    "list_layers",
    "list_snapshots",
    "ocr_screen",
    "prune_snapshots",
    "save_snapshot_to_elements",
]

import logging

from datetime import datetime

logger = logging.getLogger(__name__)

# 历史快照保留上限（每个调用者）：采集成功后自动淘汰更早的记录，列表也最多返回这么多条
SNAPSHOT_RETENTION = 10


def capture_snapshot(user_id: str, serial: str, method: str = "dump") -> dict:
    """一键获取（dump 或 OCR，二选一）→ 快照落库，返回快照全量 JSON。"""
    from engines.device.registry import close_engine

    from .models import Snapshot
    from .service import (
        CaptureError,
        capture_dump_payload,
        capture_ocr_payload,
        capture_page_screenshot,
        open_inspector_engine,
    )

    if method not in ("dump", "ocr"):
        raise CaptureError("无效的获取方法", status_code=400)

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")

    engine = open_inspector_engine(serial)
    # 页面截图先行：OCR 识别与元素缩略图裁剪均依赖截图文件
    screenshot_path = capture_page_screenshot(engine, ts)

    if method == "dump":
        try:
            dump_data = capture_dump_payload(engine, ts)
        except Exception:
            logger.exception("capture dump failed serial=%s", serial)
            _cleanup_capture_files(ts)
            raise CaptureError("获取失败", status_code=500)
        ocr_data = None
    else:  # method == "ocr"
        try:
            ocr_data = capture_ocr_payload(ts)
        except Exception:
            logger.exception("capture ocr failed serial=%s", serial)
            _cleanup_capture_files(ts)
            raise CaptureError("OCR 识别失败，请稍后重试", status_code=500)
        dump_data = None

    info = engine.device_info
    close_engine(engine)
    from apps.device_pool.models import Device

    # 索引单独成列：dump_json 只留展示集（否则同一份节点数据会被写两遍）
    node_index = (dump_data or {}).get("nodes") or []
    dump_record = {k: v for k, v in (dump_data or {}).items() if k != "nodes"}

    snapshot = Snapshot.objects.create(
        device=Device.objects.filter(serial=serial).first(),
        serial=serial,
        method=method,
        dump_json=dump_record,
        nodes_json=node_index,
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
    # 数据带截图 ID（复用 snapshot_id）：dump/OCR 结果内嵌 screenshot_id，标识此次结果对应哪张图
    _shot_fields = []
    if dump_data is not None:
        snapshot.dump_json = {**snapshot.dump_json, "screenshot_id": snapshot.id}
        _shot_fields.append("dump_json")
    if ocr_data is not None:
        snapshot.ocr_json = {**snapshot.ocr_json, "screenshot_id": snapshot.id}
        _shot_fields.append("ocr_json")
    if _shot_fields:
        snapshot.save(update_fields=_shot_fields)

    # 保留上限：落库后把该调用者更早的快照收敛到上限。
    # 淘汰是采集的附带维护动作，失败只告警不回滚（否则用户会看到「获取失败」但记录已落库）。
    try:
        prune_snapshots(user_id)
    except Exception:
        logger.exception("prune snapshots failed user=%s", user_id)

    return snapshot_to_dict(snapshot)


def capture_screen(serial: str) -> dict:
    """轻量截屏：仅校验设备可用 + 切换 + 截图落盘，不做 dump/OCR/快照落库。

    供 AI 视觉点击链路（screenshot_page）调用——只取当前屏幕图，不产生快照记录。
    """
    from engines.device.registry import close_engine

    from .service import capture_page_screenshot, open_inspector_engine

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    engine = open_inspector_engine(serial)
    screenshot_path = capture_page_screenshot(engine, ts)
    info = engine.device_info
    current = engine.app_current() or {}
    close_engine(engine)
    return {
        "screenshot_path": screenshot_path,
        "serial": serial,
        "package": current.get("package", ""),
        "activity": current.get("activity", ""),
        "screen_w": info.get("displayWidth", 0) or 0,
        "screen_h": info.get("displayHeight", 0) or 0,
    }


def ocr_screen(serial: str, texts: str = "") -> dict:
    """OCR 识别当前页面 → 文本 + 原始角点 + 归一化中心点（一次性只读，不落库）。

    供 AI 视觉识别工具调用：校验设备 → 截屏 → 关引擎 → 识别 → 删除截图文件。
    与 `capture_screen` 一样只做一次性取样，不产生 `di_snapshots` 记录
    （快照是检查器页面的资产，AI 调用是即时读取）。

    `texts` 为可选的多文本过滤（分隔符与匹配语义见 `service.ocr_page_payload`）；
    留空返回整页全部文本。
    """
    from pathlib import Path

    from django.conf import settings

    from engines.device.registry import close_engine

    from .service import capture_page_screenshot, ocr_page_payload, open_inspector_engine

    ts = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    engine = open_inspector_engine(serial)
    try:
        screenshot_path = capture_page_screenshot(engine, ts)
    finally:
        # OCR 不需要设备：截完即还，设备占用窗口保持最短
        close_engine(engine)

    try:
        payload = ocr_page_payload(str(Path(settings.MEDIA_ROOT) / screenshot_path), texts)
    finally:
        # 契约只回 JSON 不回图片，截图用完即删，避免 AI 高频调用堆积磁盘
        _cleanup_capture_files(ts)

    return {"serial": serial, "count": len(payload["texts"]), **payload}


def list_snapshots(user_id: str, offset: int = 0, limit: int = 100) -> dict:
    """快照列表（创建时间倒序 + 分页）。

    条数上限取 SNAPSHOT_RETENTION：历史列表最多返回保留上限条，无论请求多大条数；
    total 恒为该调用者快照的真实总数（不因封顶而变化）。排序与淘汰口径一致
    （创建时间倒序，时间相同再按 ID 倒序），避免「展示的十条」与「保留的十条」不是同一批。
    """
    from .models import Snapshot

    qs = Snapshot.objects.filter(created_by=user_id).order_by("-created_at", "-id")
    total = qs.count()
    capped = min(limit, SNAPSHOT_RETENTION)
    items = [snapshot_meta_dict(s) for s in qs[offset : offset + capped]]
    return {"total": total, "items": items}


# 可作为筛减条件的交互标志（与元素条目的 flags 键一致）
_FILTER_FLAGS = (
    "clickable",
    "long_clickable",
    "scrollable",
    "checkable",
    "checked",
    "enabled",
    "focusable",
)


def _legacy_node(entry: dict) -> dict:
    """历史快照的保留集元素 → 节点索引形态（缺全量索引时的降级输入）。

    降级集里没有「被展示裁剪丢弃」的信息，故保留标记一律为真；调用方据 source 提示不完整。
    """
    return {**entry, "kept_in_snapshot": True}


def _layer_match(
    entry: dict, group: str, sub: str, flags, query: str, only_kept: bool, only_stable: bool
) -> bool:
    """元素条目是否命中筛减条件（多个交互标志取交集）。"""
    if group and entry["level1"] != group:
        return False
    if sub and entry["level2"] != sub:
        return False
    for flag in flags:
        if not entry["flags"].get(flag):
            return False
    if only_kept and not entry["kept_in_snapshot"]:
        return False
    if only_stable and not entry["primary"]["stable"]:
        return False
    if query:
        needle = query.casefold()
        haystack = (entry["text"], entry["resource_id"], entry["content_desc"], entry["class_name"])
        if not any(needle in (value or "").casefold() for value in haystack):
            return False
    return True


def list_layers(
    snapshot_id: int,
    user_id: str = "",
    group: str = "",
    sub: str = "",
    flags=(),
    query: str = "",
    only_kept: bool = False,
    only_stable: bool = False,
    offset: int = 0,
    limit: int | None = None,
) -> dict | None:
    """快照的分层数据：两级分组摘要 + 坐标顺序的元素条目，支持筛减与分页。

    分层由全量节点索引即时计算（不落库）；索引缺失的历史快照降级为「仅保留集」，
    并在 source 里如实标注（legacy）。快照不存在或不属于该调用者时返回 None。
    摘要里的分组计数恒为全量（供分组选择器显示徽标），total_matched 才是筛减后的条数。

    **条数缺省即不截断**：limit=None 时返回自 offset 起的全部命中，响应里的 limit 为
    None（如实表示本次没有上限）。隐式上限会让「摘要全量」与「条目切片」两个口径分叉，
    前端因此拿到自相矛盾的分组计数与行数；只有显式给条数的调用方才需要切片。

    Raises:
        ValueError: 分组/二级分组/交互标志取值非法（由视图映射 400）。
    """
    from algorithms.element_layers import LEVEL2_ORDER, ROLE_ORDER, build_layers

    from .models import Snapshot

    if group and group not in ROLE_ORDER:
        raise ValueError("未知的一级分组")
    if sub and sub not in LEVEL2_ORDER:
        raise ValueError("未知的二级分组")
    if sub and group != "content_widget":
        raise ValueError("二级分组只在一级分组为内容控件时有效")
    for flag in flags:
        if flag not in _FILTER_FLAGS:
            raise ValueError("未知的交互标志：%s" % flag)

    snapshot = Snapshot.objects.filter(id=snapshot_id, created_by=user_id).first()
    if snapshot is None:
        return None

    index = snapshot.nodes_json or []
    if index:
        source = "index"
        nodes = [dict(node) for node in index]
    else:
        source = "legacy"
        nodes = [_legacy_node(e) for e in (snapshot.dump_json or {}).get("elements", [])]

    layers = build_layers(nodes)
    matched = [
        e
        for e in layers["elements"]
        if _layer_match(e, group, sub, flags, query, only_kept, only_stable)
    ]

    return {
        "snapshot_id": snapshot.id,
        "source": source,
        "package": snapshot.package,
        "activity": snapshot.activity,
        "screen": {"w": snapshot.screen_w, "h": snapshot.screen_h},
        "screenshot_path": snapshot.screenshot_path,
        "summary": layers["summary"],
        "total_matched": len(matched),
        "offset": offset,
        "limit": limit,
        "elements": matched[offset:] if limit is None else matched[offset : offset + limit],
    }


def _media_referenced(screenshot_path: str, thumbs_dir_rel: str) -> bool:
    """该批媒体是否仍被元素定位引用（跨 App 读 Model，只读不写）。

    页面级 OCR 不再随保存落库后，媒体引用只剩两处：已保存页面的整屏截图与元素的
    缩略图。任一处命中即视为整批仍被引用——宁可多留几个文件，也不误删他人资产。
    """
    from apps.element_locator.models import Element, Page

    if screenshot_path and Page.objects.filter(screenshot_path=screenshot_path).exists():
        return True
    if thumbs_dir_rel:
        prefix = thumbs_dir_rel.rstrip("/") + "/"
        if Element.objects.filter(thumbnail_path__startswith=prefix).exists():
            return True
    return False


def _thumbs_dir_rel(snapshot) -> str:
    """快照的缩略图目录（相对路径）：thumbs/{ts}/el_0.png → thumbs/{ts}。

    dump 的 actionable 与 OCR 的 texts 都可能带缩略图路径，前者取不到时回落后者。取不到返回空串。
    """
    for field, marker in (("dump_json", "actionable"), ("ocr_json", "texts")):
        items = (getattr(snapshot, field) or {}).get(marker) or []
        first_thumb = next(
            (t.get("thumbnail_path", "") for t in items if t.get("thumbnail_path")), ""
        )
        if not first_thumb:
            continue
        parts = first_thumb.split("/")
        if len(parts) >= 3:
            return "/".join(parts[:3])
    return ""


def _delete_snapshot_record(snapshot) -> None:
    """删除一条快照记录与其未被引用的媒体（单条删除 / 淘汰 / 清空三处共用）。

    先判定再删除：被元素定位引用时只删记录、保留文件（否则已保存页面的图会全碎）；
    判定在删除任何文件之前完成：判定抛错时一个文件都不会被删（fail-closed），异常向上传播。
    """
    from .service import delete_snapshot_files

    thumbs_dir_rel = _thumbs_dir_rel(snapshot)
    if _media_referenced(snapshot.screenshot_path, thumbs_dir_rel):
        logger.info(
            "快照 %s 的媒体仍被元素定位引用，保留文件（shot=%s thumbs=%s）",
            snapshot.id,
            snapshot.screenshot_path,
            thumbs_dir_rel,
        )
    else:
        delete_snapshot_files(snapshot.screenshot_path, thumbs_dir_rel)
    snapshot.delete()


def delete_snapshot(snapshot_id: int, user_id: str = "") -> bool:
    """删除本人快照记录；截图/缩略图仅在没有其它模块引用时才删除。

    不存在返回 False。判定在删除任何文件之前完成：判定抛错时一个文件都不会被删
    （fail-closed），异常向上传播为 500。
    """
    from .models import Snapshot

    snapshot = Snapshot.objects.filter(id=snapshot_id, created_by=user_id).first()
    if snapshot is None:
        return False
    _delete_snapshot_record(snapshot)
    return True


def prune_snapshots(user_id: str) -> int:
    """把该调用者的历史快照收敛到保留上限，返回实际淘汰的条数。

    淘汰创建时间最早的多余记录。媒体清理沿用 _delete_snapshot_record 的引用判定，
    MUST NOT 直接用 queryset.delete() —— 那会绕过引用判定，删掉仍被元素定位引用的媒体。
    """
    from .models import Snapshot

    stale_ids = list(
        Snapshot.objects.filter(created_by=user_id)
        .order_by("-created_at", "-id")
        .values_list("id", flat=True)[SNAPSHOT_RETENTION:]
    )
    deleted = 0
    for snapshot_id in stale_ids:
        snapshot = Snapshot.objects.filter(id=snapshot_id).first()
        if snapshot is None:
            continue
        _delete_snapshot_record(snapshot)
        deleted += 1
    return deleted


def clear_snapshots(user_id: str) -> int:
    """清空该调用者的全部历史快照，返回实际删除的条数（没有快照时为 0）。

    只作用于该调用者自己的记录，不影响其它调用者；媒体清理沿用
    _delete_snapshot_record 的引用判定（被元素定位引用则保留文件）。
    """
    from .models import Snapshot

    snapshot_ids = list(Snapshot.objects.filter(created_by=user_id).values_list("id", flat=True))
    deleted = 0
    for snapshot_id in snapshot_ids:
        snapshot = Snapshot.objects.filter(id=snapshot_id).first()
        if snapshot is None:
            continue
        _delete_snapshot_record(snapshot)
        deleted += 1
    return deleted


def save_snapshot_to_elements(
    snapshot_id: int,
    user_id: str = "",
    page_label: str = "",
    folder_path: str = "",
    page_id: int | None = None,
    element_ids=None,
    aliases: dict | None = None,
    element_aliases: list[dict] | None = None,
) -> dict:
    """筛减保存快照到元素定位（经 element_locator.api）。

    Args:
        page_id: 目标已有页面 ID（与 page_label/folder_path 二选一：有 page_id
            为「保存到已有页面」，否则为「新建页面」）。
        element_ids: 勾选元素的**坐标顺序序号**（1 基，与分层端点 `seq` 同源）；空 = 全部。
            出现不在该快照序号范围内的值即抛 ValueError（视图映射 400），不静默丢弃。
        aliases: {resource_id: alias} 中文别名映射，按 resource_id 回填到元素（AI 工具口径）。
        element_aliases: [{index, name}] 逐元素中文名称，index 为坐标顺序序号；优先于
            aliases，同一 resource_id 的多个元素互不覆盖。

    缩略图在保存时按元素 bounds 从该快照的整屏截图裁剪（检查器侧）；整屏截图本身不写入
    元素定位，页面级 OCR 也不落库（rework-inspector-view）：快照自身的 OCR 仍存于
    di_snapshots.ocr_json，元素定位侧 ocr_json 恒为空。
    """
    from algorithms.element_layers import build_layers

    from .models import Snapshot
    from .service import crop_save_thumbnails

    snapshot = Snapshot.objects.filter(id=snapshot_id, created_by=user_id).first()
    if snapshot is None:
        raise ValueError("快照不存在")
    if not page_id and not page_label:
        raise ValueError("页面名称不能为空")

    nodes = [dict(node) for node in (snapshot.nodes_json or [])]
    if not nodes:
        raise ValueError("该快照无全量元素索引，无法保存")
    # 分层算法给出与检查器表格同源的坐标顺序序号（1 基）与主定位口径
    entries = build_layers(nodes)["elements"]
    by_seq = {entry["seq"]: entry for entry in entries}

    seqs: list[int] = []
    if element_ids:
        for raw in element_ids:
            if not isinstance(raw, int) or raw not in by_seq:
                raise ValueError(f"元素序号不存在：{raw!r}")
            seqs.append(raw)
    else:
        seqs = [entry["seq"] for entry in entries]

    selected = [_locator_element(by_seq[seq]) for seq in seqs]
    thumbs = crop_save_thumbnails(
        snapshot.screenshot_path, [(seq, _thumbnail_box(by_seq[seq])) for seq in seqs]
    )
    for item in selected:
        item["thumbnail_path"] = thumbs.get(item["seq"], "")

    aliases = aliases or {}
    for e in selected:
        rid = (e.get("resource_id") or "").strip()
        if rid and rid in aliases:
            e["alias"] = aliases[rid]

    # 逐元素名称（检查器内联重命名口径）：同名 resource_id 的元素互不干扰，且优先于 rid 别名
    index_aliases: dict[int, str] = {}
    for item in element_aliases or []:
        if not isinstance(item, dict):
            continue
        index = item.get("index")
        name = (item.get("name") or "").strip()
        if isinstance(index, int) and name:
            index_aliases[index] = name
    if index_aliases:
        for e in selected:
            name = index_aliases.get(e["seq"])
            if name:
                e["alias"] = name

    from apps.element_locator.api import import_snapshot_page

    return import_snapshot_page(
        page_label=page_label,
        folder_path=folder_path,
        page_id=page_id,
        package=snapshot.package,
        activity=snapshot.activity,
        ocr_json=None,
        snapshot_id=snapshot.id,
        elements=selected,
    )


def _locator_element(entry: dict) -> dict:
    """分层元素条目 → 元素定位写入载荷（收敛后的六项 + 去重键）。"""
    primary = entry.get("primary") or {}
    coords = entry.get("coords") or {}
    return {
        "seq": entry["seq"],
        "alias": "",
        "text": entry.get("text", ""),
        "primary_xpath": primary.get("xpath", "") or "",
        "primary_stable": bool(primary.get("stable", False)),
        "flags": entry.get("flags") or {},
        "resource_id": entry.get("resource_id", ""),
        "bounds": coords.get("bounds", ""),
        "thumbnail_path": "",
    }


def _thumbnail_box(entry: dict) -> tuple[int, int, int, int]:
    """分层元素条目 → PIL 裁剪盒 (left, top, right, bottom)。"""
    coords = entry.get("coords") or {}
    x = int(coords.get("x") or 0)
    y = int(coords.get("y") or 0)
    return (x, y, x + int(coords.get("w") or 0), y + int(coords.get("h") or 0))


# ═══════════════════════════════════════════════
# 序列化（快照记录 → JSON）
# ═══════════════════════════════════════════════


def _cleanup_capture_files(ts: str) -> None:
    """清理本批截图与缩略图文件（capture 失败时、或结果取用完毕后；尽力，失败仅告警）。"""
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
