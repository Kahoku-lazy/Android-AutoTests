"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/ae_harness/workflow/sop/__init__.py 🏁
模块功能：➡️ SOP 编排门面：步骤定义、加载与运行 🏁
Python 调试：➡️ python -m engines.ae_harness.workflow.sop 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. load_spec: 从 YAML 读步骤定义。
2. run_sop: 传执行者、验收者与步骤即可跑完整流程。
3. 本包不建角色、不挂工具，角色由调用方准备好后传入。
🏁
关联模块：➡️
1. engines.ae_harness.workflow.sop.spec: 步骤模型与加载。
2. engines.ae_harness.workflow.sop.runner: 编排实现。
3. engines.ae_harness.workflow.sop.steps: 步骤 YAML。
🏁
测试：➡️
1. python -m engines.ae_harness.workflow.sop_runner
🏁
"""

from __future__ import annotations

from .runner import SopResult, StepOutcome, build_sop, run_sop
from .spec import SopSpec, SopSpecError, StepSpec, load_spec

__all__ = [
    "SopResult",
    "SopSpec",
    "SopSpecError",
    "StepOutcome",
    "StepSpec",
    "build_sop",
    "load_spec",
    "run_sop",
]
