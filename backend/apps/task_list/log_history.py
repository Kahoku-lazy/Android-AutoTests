"""给验收模型准备关键词对照文本。历史取证已去掉。"""

from __future__ import annotations

from django.conf import settings

from engines.device.logbus import KeywordIndex

__all__ = ["keyword_catalog_text"]


def keyword_catalog_text() -> str:
    """当前日志关键词表 → 给验收模型看的「关键词 → 功能点」对照文本（取不到返回空串）。"""
    path = str(getattr(settings, "DEVICE_LOG_KEYWORD_FILE", "") or "")
    mapping = KeywordIndex.from_file(path).mapping
    if not mapping:
        return ""
    lines = [
        "本平台日志关键词表（检查日志时从这里选关键词，报给 check_device_log）：",
    ]
    for keyword, features in mapping.items():
        marks = "、".join(
            f"#{item.get('id')} {item.get('module')}-{item.get('feature')}"
            for item in features or []
        )
        lines.append(f"  - {keyword} → {marks}" if marks else f"  - {keyword}")
    return "\n".join(lines)
