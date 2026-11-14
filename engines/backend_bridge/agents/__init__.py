"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/backend_bridge/agents/__init__.py 🏁
模块功能：➡️ 平台角色子包：对外只导出 UI 执行角色的装配入口 🏁
Python 调试：➡️ python -m engines.backend_bridge.agents 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 对外只导出 UI_EXECUTOR_ROLE 与 build_ui_executor。
2. 新增平台角色一律在本子包建模块，禁止放进 backend_bridge 根目录。
🏁
关联模块：➡️
1. engines.backend_bridge.agents.ui_executor: 平台 UI 执行角色。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_ui_executor.py
🏁
"""

from __future__ import annotations

from .ui_executor import UI_EXECUTOR_ROLE, PlatformRole, build_ui_executor

__all__ = ["PlatformRole", "UI_EXECUTOR_ROLE", "build_ui_executor"]
