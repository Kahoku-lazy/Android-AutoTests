"""OCR text recognition for device-inspector — cnocr on live screenshots."""

import base64
import io
import logging
import threading

from cnocr import CnOcr
from PIL import Image

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


def _pil_to_b64(img: Image.Image) -> str:
    """Encode a PIL image as base64 JPEG (compact thumbnail)."""
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format="JPEG", quality=50)
    return base64.b64encode(buf.getvalue()).decode("ascii")


def recognize(screenshot_path: str) -> list[dict]:
    """Run OCR on a full-resolution screenshot.

    Returns a list of text regions, each with an axis-aligned bounding box
    (device pixels, matching dump element x/y/width/height) and a cropped
    base64 thumbnail.

    Args:
        screenshot_path: Path to a PNG screenshot file.

    Returns:
        list[dict]: [{text, confidence, x, y, width, height,
                      thumbnail, thumbnail_format}]
    """
    engine = _get_engine()
    # cnocr returns [{text, score, position}] — position is a (N,2) array of corner points.
    results = engine.ocr(screenshot_path)
    img = Image.open(screenshot_path)

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
        thumbnail = _pil_to_b64(img.crop((x, y, x + width, y + height)))
        texts.append(
            {
                "text": r.get("text", ""),
                "confidence": round(float(r.get("score", 0)), 4),
                "x": x,
                "y": y,
                "width": width,
                "height": height,
                "thumbnail": thumbnail,
                "thumbnail_format": "jpeg",
            }
        )
    return texts
