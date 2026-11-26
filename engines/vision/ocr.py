import logging
import threading

from cnocr import CnOcr

logger = logging.getLogger(__name__)

_engine = None
_engine_lock = threading.Lock()


def _get_engine() -> CnOcr:
    global _engine
    if _engine is None:
        with _engine_lock:
            if _engine is None:
                _engine = CnOcr()
    return _engine


def recognize(screenshot_path: str) -> list[dict]:
    engine = _get_engine()
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
