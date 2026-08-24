"""OCR re-export — L1a 下沉至 algorithms/vision/ocr（原处兼容）。

跨 App 复用请直接 import `algorithms.vision.ocr`。
"""

from algorithms.vision.ocr import _get_engine, _pil_to_b64, recognize  # noqa: F401
