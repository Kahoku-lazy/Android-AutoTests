"""
文件名: ➡️ log_keywords.py 🏁
路径: ➡️ engines/agents/config/log_keywords.py 🏁
模块功能：➡️ 按型号读取日志关键词目录，供验收步骤提示注入 🏁
Python 调试：➡️ python -m engines.agents.config.log_keywords 🏁
时间：➡️ 2026-11-03 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-03 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. load_log_keywords: 读 config/data/log_keywords/<SKU>.md，返回「功能点 → 关键词」正文
2. _safe_sku: 型号名做白名单过滤，避免把 YAML 里的字符串直接拼成路径
3. 目录缺失或不可读时返回空串，不抛异常：该步照常开始，由提示词降级为截图核对
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/graybox/unit/test_log_keywords.py: 按型号读取、缺失降级、非法型号名
2. tests/graybox/unit/test_log_keyword_catalog.py: 目录里的关键词必须存在于全量目录
🏁
"""

from __future__ import annotations

import re

from pathlib import Path
from typing import Final

LOG_KEYWORDS_DIR: Final[Path] = Path(__file__).resolve().parent / "data" / "log_keywords"
"""按型号的关键词目录所在目录。"""

_SKU_PATTERN: Final[re.Pattern[str]] = re.compile(r"^[A-Za-z0-9_-]+$")

__all__ = ["LOG_KEYWORDS_DIR", "load_log_keywords"]


def _safe_sku(sku: str) -> str:
    """把型号名收敛成可安全拼进文件名的一段。

    Args:
        sku: 型号名，来自用例的 `log.sku`。

    Returns:
        只含字母、数字、下划线与短横的型号名；不合法时返回空串。
    """
    name = str(sku or "").strip()
    return name if _SKU_PATTERN.match(name) else ""


def load_log_keywords(sku: str) -> str:
    """按型号读取日志关键词目录正文。

    Args:
        sku: 型号名，如 H6810。

    Returns:
        `config/data/log_keywords/<SKU>.md` 的正文；型号非法、文件缺失或不可读时返回空串。
    """
    name = _safe_sku(sku)
    if not name:
        return ""
    path = LOG_KEYWORDS_DIR / f"{name}.md"
    try:
        return path.read_text(encoding="utf-8").strip()
    except OSError:
        return ""
