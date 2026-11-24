"""
模块功能：➡️ 模块依赖检查包：允许清单 + 禁止合同，入口 python -m utils.linting 🏁
Python 调试：➡️ python -m utils.linting 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（门禁 `linting` 直接调用）
🏁
"""

from utils.linting.checks import check
from utils.linting.cli import main
from utils.linting.config import CONFIG_NAME, load_config

__all__ = ["CONFIG_NAME", "check", "load_config", "main"]
