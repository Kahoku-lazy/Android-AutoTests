"""UI 层级 XML 纯解析 — L1a 算法层（零 apps/django 依赖）。

D-1 边界：设备取数（3 层 fallback dump）归设备侧（现状 `device_pool/pool.py`，
目标 `engines/`）；本模块只吃 raw 字符串，是纯函数。
自 `apps/device_pool/pool.py:175-240` 解析段平移（extract-algorithms-package change），
异常文案与修复语义未改。
"""

import logging
import xml.etree.ElementTree as ET

logger = logging.getLogger(__name__)


def parse_hierarchy_xml(raw):
    """解析 dump XML → 标准节点 dict 列表（含截断检测与 rfind 修复）。

    Args:
        raw: dump 原始字符串或 bytes（u2 dump_hierarchy 的返回值）。

    Raises:
        RuntimeError: 解析失败且无法修复。
    """
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")

    raw_len = len(raw)
    logger.debug("[dump] XML length: %s chars", raw_len)

    if not raw.lstrip().startswith("<?"):
        raw = '<?xml version="1.0" encoding="UTF-8"?>\n' + raw

    stripped = raw.rstrip()
    if not stripped.endswith(">") or stripped.endswith("/>"):
        logger.warning("[dump] XML may be truncated, last 100 chars: ...%s", stripped[-100:])

    try:
        root = ET.fromstring(raw.encode("utf-8") if isinstance(raw, str) else raw)
    except ET.ParseError as pe:
        logger.warning("[dump] XML parse failed: %s, trying truncation repair...", pe)
        last_complete = raw.rfind(">")
        if last_complete > 0:
            fixed = raw[: last_complete + 1]
            try:
                root = ET.fromstring(fixed.encode("utf-8"))
                logger.info("[dump] Repair succeeded, truncated %s chars", raw_len - len(fixed))
            except ET.ParseError:
                raise RuntimeError(f"XML parse failed and cannot repair: {pe}")
        else:
            raise RuntimeError(f"XML parse failed: {pe}")

    nodes = []

    def walk(el, depth=0):
        bounds_str = el.attrib.get("bounds", "[0,0][0,0]")
        parts = bounds_str.replace("][", ",").strip("[]").split(",")
        try:
            l, t, r, b = map(int, parts)
        except Exception:
            l, t, r, b = 0, 0, 0, 0

        nodes.append(
            {
                "depth": depth,
                "class_name": el.attrib.get("class", ""),
                "text": el.attrib.get("text", ""),
                "content_desc": el.attrib.get("content-desc", ""),
                "resource_id": el.attrib.get("resource-id", ""),
                "package": el.attrib.get("package", ""),
                "index": el.attrib.get("index", ""),
                "bounds": f"[{l},{t}][{r},{b}]",
                "x": l,
                "y": t,
                "width": r - l,
                "height": b - t,
                "clickable": el.attrib.get("clickable", "false") == "true",
                "enabled": el.attrib.get("enabled", "false") == "true",
                "scrollable": el.attrib.get("scrollable", "false") == "true",
                "checkable": el.attrib.get("checkable", "false") == "true",
                "checked": el.attrib.get("checked", "false") == "true",
                "focusable": el.attrib.get("focusable", "false") == "true",
                "long_clickable": el.attrib.get("long-clickable", "false") == "true",
            }
        )
        for child in el:
            walk(child, depth + 1)

    walk(root)
    return nodes
