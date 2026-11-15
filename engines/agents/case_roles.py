"""
文件名: ➡️ case_roles.py 🏁
路径: ➡️ engines/agents/case_roles.py 🏁
模块功能：➡️ 用例角色成对装配的过渡入口 🏁
Python 调试：➡️ python -m engines.agents.case_roles 🏁
时间：➡️ 2026-11-09 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 本文件只再导出 assistant.case_roles，供尚未改导入路径的调用方使用。
🏁
关联模块：➡️
1. engines.agents.assistant.case_roles: 成对装配的实现。
🏁
测试：➡️
1. tests/graybox/unit/test_case_authoring_roles.py: 旧路径与新路径导出同一函数
🏁
"""

from engines.agents.assistant.case_roles import build_case_authoring_roles

__all__ = ["build_case_authoring_roles"]
