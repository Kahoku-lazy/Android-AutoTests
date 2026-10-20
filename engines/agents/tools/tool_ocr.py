"""引擎侧 OCR 工具：读取当前页面文本与坐标（不装配给任何角色）。

截图经 `engines.device.action.Screenshot`，识别经 `engines.vision.ocr`；
本模块只被测试与人工调用，MUST NOT 进入任何角色的工具集。
"""

from __future__ import annotations

import base64
import json
import tempfile

from contextlib import contextmanager
from pathlib import Path
from typing import Any, Callable

from engines.device.action import Screenshot, System, open_device
from utils.logs import agent_event_log

from .tool_base import ToolSpec

__all__ = ["build_ocr_tools", "ocr_tool_specs"]

_READ_ONLY = frozenset({"ocr_page"})
_TOOL_ORDER = ("ocr_page",)
# 临时文件扩展名（识别库按内容解码，扩展名只求与格式一致）
_SHOT_SUFFIX = {"image/png": ".png", "image/jpeg": ".jpg"}


def _error(message: str) -> str:
    return json.dumps({"error": message}, ensure_ascii=False)


def _parse_text_filters(raw: str) -> list[str]:
    """把「多文本」入参拆成关键词表（英文/中文逗号、顿号、换行分隔；忽略大小写去重）。"""
    keywords: list[str] = []
    normalized = str(raw or "").replace("，", ",").replace("、", ",").replace("\n", ",")
    for chunk in normalized.split(","):
        word = chunk.strip().casefold()
        if word and word not in keywords:
            keywords.append(word)
    return keywords


def _recognize(screenshot_path: str) -> list[dict]:
    """惰性调用引擎视觉识别（避免引擎导入期拉起 cnocr 重依赖）。"""
    from engines.vision.ocr import recognize

    return recognize(screenshot_path)


def _ocr_payload(screenshot_path: str, texts: str = "") -> dict:
    """识别截图文本 → {screen_w, screen_h, texts:[...]}（纯函数，无设备交互）。

    Args:
        screenshot_path: 截图文件路径。
        texts: 可选的多文本过滤，命中任一关键词即保留（忽略大小写的子串匹配）；
            英文/中文逗号、顿号、换行都可作分隔符；留空返回整页全部文本。

    Returns:
        {"screen_w", "screen_h", "texts": [{text, confidence, coordinates, center}]}；
        center 为按截图自身像素尺寸归一化到 0~1 的中心点。

    Raises:
        ValueError: 截图尺寸无效，或 OCR 结果缺少角点坐标。
    """
    from PIL import Image

    with Image.open(screenshot_path) as img:
        screen_w, screen_h = img.size
    if screen_w <= 0 or screen_h <= 0:
        raise ValueError("截图尺寸无效，无法计算归一化中心点")

    keywords = _parse_text_filters(texts)
    regions: list[dict] = []
    for item in _recognize(screenshot_path):
        if keywords and not any(word in item["text"].casefold() for word in keywords):
            continue
        coords = item.get("coordinates") or []
        if len(coords) < 2:
            raise ValueError("OCR 结果缺少角点坐标，无法计算中心点")
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


@contextmanager
def _device(serial: str):
    """打开一台设备，离开时断开。"""
    connection, info, control = open_device(System.ANDROID, str(serial))
    try:
        yield info, control
    finally:
        connection.disconnect()


def build_ocr_tools() -> dict[str, Callable[..., Any]]:
    """按固定顺序产出 OCR 工具函数表。"""

    def ocr_page(serial: str, texts: str = "") -> str:
        """OCR 识别设备当前页面的文本，返回文本、置信度、原始角点坐标与归一化中心点。

        中心点为 0~1 的归一化坐标，可直接作为点击/拖拽工具的入参使用。
        页面文本很多时用 texts 收窄结果，避免返回无关文本。
        Args:
            serial: 设备序列号
            texts: 要查找的文本，可一次指定多个，用逗号/顿号/换行分隔（如「设置,WiFi」）；
                命中任一即返回（忽略大小写的子串匹配）；留空返回整页全部文本
        """
        try:
            with _device(serial) as (_info, control):
                shot = Screenshot(control).capture()
            # 识别库只吃文件路径：在临时目录里落一份，离开作用域即删，不污染截图目录
            with tempfile.TemporaryDirectory(prefix="ocr_shot_") as tmp:
                path = Path(tmp) / f"shot{_SHOT_SUFFIX.get(shot['media_type'], '.png')}"
                path.write_bytes(base64.b64decode(shot["image_base64"]))
                payload = _ocr_payload(str(path), texts)
        except Exception as exc:  # noqa: BLE001 - 设备/识别失败一律转可读结论
            agent_event_log.warning(f"OCR 执行失败：{exc}")
            return _error(f"OCR 执行失败：{exc}")
        return json.dumps(payload, ensure_ascii=False, default=str)

    impls = {"ocr_page": ocr_page}
    return {name: impls[name] for name in _TOOL_ORDER}


def ocr_tool_specs() -> list[ToolSpec]:
    """按工具函数表产出 `ToolSpec` 列表（只读；不装配给任何角色）。"""
    return [
        ToolSpec(
            name=name,
            handler=func,
            read_only=name in _READ_ONLY,
            auto_allow=True,
        )
        for name, func in build_ocr_tools().items()
    ]
