from __future__ import annotations

from django.conf import settings

from engines.device.logbus import KeywordIndex

__all__ = ["keyword_catalog_text"]


def keyword_catalog_text() -> str:
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
