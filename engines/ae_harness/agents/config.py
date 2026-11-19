"""
文件名: ➡️ config.py 🏁
路径: ➡️ engines/ae_harness/agents/config.py 🏁
模块功能：➡️ 按型号读日志关键词目录 🏁
Python 调试：➡️ python -m engines.ae_harness.agents.config 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. load_log_keywords: 按型号读日志关键词目录，供验收提示注入；缺失时降级为空串。
🏁
关联模块：➡️
1. 无本地依赖：只依赖 yaml 与 dotenv。
🏁
测试：➡️
1. 见 engines.ae_harness.assistant.agent_executor。
🏁
"""

from __future__ import annotations

import re

from pathlib import Path

_HERE = Path(__file__).resolve().parent
LOG_KEYWORDS_DIR = _HERE / "config" / "log_keywords"

# 型号名白名单：只允许字母、数字、下划线与短横，避免把 YAML 里的字符串直接拼成路径。
_SKU_PATTERN = re.compile(r"^[A-Za-z0-9_-]+$")


def load_log_keywords(sku: str) -> str:
    """
    按型号读取日志关键词目录正文。

    Args:
        sku: 型号名，如 H6810。

    Returns:
        `config/log_keywords/<SKU>.md` 的正文；型号非法、文件缺失或不可读时返回空串。
    """
    name = str(sku or "").strip()
    if not _SKU_PATTERN.match(name):
        return ""
    try:
        return (LOG_KEYWORDS_DIR / f"{name}.md").read_text(encoding="utf-8").strip()
    except OSError:
        return ""
