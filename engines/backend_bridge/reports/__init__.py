"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/backend_bridge/reports/__init__.py 🏁
模块功能：➡️ 报告落盘子包：对外只导出根目录常量 🏁
Python 调试：➡️ python -m engines.backend_bridge.reports 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. 对外只导出 REPORT_ROOT，子模块路径细节不暴露。
2. 报告路径只在这里定义；其它模块 MUST NOT 自行拼接该路径。
3. 每次运行的子目录由事件记录器按时间戳创建。
🏁
关联模块：➡️
1. engines.backend_bridge.reports.paths: 路径常量实现。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_paths.py
🏁
"""

from __future__ import annotations

from .paths import REPORT_ROOT

__all__ = ["REPORT_ROOT"]
