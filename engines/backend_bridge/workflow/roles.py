"""
文件名: ➡️ roles.py 🏁
路径: ➡️ engines/backend_bridge/workflow/roles.py 🏁
模块功能：➡️ 一次 SOP 运行用到的两个角色 🏁
Python 调试：➡️ python -m engines.backend_bridge.workflow.roles 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. SopRoles: 一次运行用到的两个角色 bundle 与共用的观测中间件。
2. 只放结果形状：写死提示词文件的 build_sop_roles 已随旧 SOP 入口退役。
🏁
关联模块：➡️
1. engines.ae_harness.agents.creator: AgentBundle 是两个角色的类型。
2. engines.ae_harness.middleware: ObservationMiddleware 由两个角色共用。
3. engines.backend_bridge.workflow.bound_roles: 按名片绑定参数填这两个角色。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_bound_roles.py: 验收者只读、共用观察者
🏁
"""

from __future__ import annotations

from dataclasses import dataclass

from engines.ae_harness.agents.creator import AgentBundle
from engines.ae_harness.middleware import ObservationMiddleware

__all__ = ["SopRoles"]


@dataclass(frozen=True)
class SopRoles:
    """
    一次 SOP 运行用到的两个角色。

    Attributes:
        executor: 执行者：挂全量设备工具，负责动手。
        verifier: 验收者：只挂只读工具，负责核对「必须达成的结果」。
        observer: 两个角色共用的观测中间件；记录里带角色名，仍能分清是谁的。
    """

    executor: AgentBundle
    verifier: AgentBundle
    observer: ObservationMiddleware
