"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/backend_bridge/workflow/__init__.py 🏁
模块功能：➡️ 平台编排装配子包：把 ae_harness 的 SOP 抽象装成平台可用入口 🏁
Python 调试：➡️ python -m engines.backend_bridge.workflow 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 本子包只装配：角色怎么建、报告落哪、结果怎么整理。
2. 编排本身（步骤加载、推进、重试、驳回、事件、报告）全部调 engines/ae_harness/workflow/sop。
3. SOP 不进 AI 助手对话页，由平台侧入口触发。
🏁
关联模块：➡️
1. engines.backend_bridge.workflow.roles: 一次运行的两个角色。
2. engines.backend_bridge.workflow.bound_roles: 按名片绑定参数装配一对角色。
3. engines.backend_bridge.workflow.bound_sop: 名片绑定 SOP 的一次运行入口。
4. engines.backend_bridge.workflow.sop_ui: 一次运行的结果形状。
5. engines.ae_harness.workflow.sop: 被复用的通用 SOP 抽象。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_bound_roles.py: 验收者只读、共用观察者
2. tests/engines/backend_bridge/unit/test_bound_sop.py: 结果字段与用量汇总
🏁
"""

from __future__ import annotations

from .bound_roles import RoleBinding, build_bound_roles
from .bound_sop import run_bound_sop
from .roles import SopRoles
from .sop_ui import SopRunResult, SopStepResult

__all__ = [
    "RoleBinding",
    "SopRoles",
    "SopRunResult",
    "SopStepResult",
    "build_bound_roles",
    "run_bound_sop",
]
