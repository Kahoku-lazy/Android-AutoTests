"""OCR text recognition — L1a 算法层（vision 子包）。

自 apps/device_inspector/ocr.py 平移（extract-algorithms-package change），
双检锁惰性加载保持。cnocr 重依赖惰性导入：不碰 OCR 的模块零代价。
"""

import logging
import threading

from cnocr import CnOcr

logger = logging.getLogger(__name__)

# Lazily-initialized cnocr engine. Model download happens on first use (~/.cnocr),
# so we init once and cache to avoid re-downloading / re-loading on every call.
_engine = None
_engine_lock = threading.Lock()


def _get_engine() -> CnOcr:
    """Return the cached CnOcr engine, initializing it on first call."""
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = CnOcr()
    return _engine


def recognize(screenshot_path: str) -> list[dict]:
    """Run OCR on a full-resolution screenshot.

    Returns a list of text regions, each with an axis-aligned bounding box in
    device pixels (matching dump element x/y/width/height). `bounds` 与 dump
    元素同格式（[x,y][r,b]），坐标口径统一。

    Args:
        screenshot_path: Path to a PNG screenshot file.

    Returns:
        list[dict]: [{text, confidence, x, y, width, height, bounds, coordinates}]

        `coordinates` 是文本框的**左上与右下两个对角点** `[[x, y], [x2, y2]]`
        （设备像素）；`bounds` 是同一包围盒的字符串形式。
    """
    engine = _get_engine()
    # cnocr returns [{text, score, position}] — position is a (N,2) array of corner points.
    results = engine.ocr(screenshot_path)

    texts = []
    for r in results:
        position = r.get("position")
        if position is None or len(position) == 0:
            continue
        xs = [float(p[0]) for p in position]
        ys = [float(p[1]) for p in position]
        x, y = int(min(xs)), int(min(ys))
        width, height = int(max(xs) - x), int(max(ys) - y)
        if width <= 0 or height <= 0:
            continue
        texts.append(
            {
                "text": r.get("text", ""),
                "confidence": round(float(r.get("score", 0)), 4),
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "bounds": f"[{x},{y}][{x + width},{y + height}]",
                "coordinates": [[x, y], [x + width, y + height]],
            }
        )
    return texts
