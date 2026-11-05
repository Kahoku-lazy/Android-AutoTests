"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/workflow/__init__.py 🏁
模块功能：➡️ 工作流包：设备 SOP 一次运行，以及用例编写的状态机三段式流水线 🏁
Python 调试：➡️ python -m engines.agents.workflow 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 2.0.0 🏁
修改时间: ➡️ 2026-11-05 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 设备侧入口：AgentSOPWorkflow / load_test_cases / run_workflow。
2. 用例编写入口：CaseAuthoringResult / build_case_run_input / run_case_authoring_artifact。
🏁
关联模块：➡️
1. engines/agents/workflow/case_goal_workflow.py: 用例编写的目标流水线入口
2. engines/agents/workflow/ui_auto_workflow.py: 设备任务的 SOP 入口
🏁
测试：➡️
1. tests/graybox/unit/test_case_goal_workflow.py: 目标流水线：产物累积、预检拦截与渲染
2. tests/graybox/unit/test_sop_steps.py: 步骤输入装配：短名、必须达成的结果，以及已启动的角色
🏁
"""

from .case_goal_workflow import (
    CaseAuthoringResult,
    build_case_run_input,
    run_case_authoring_artifact,
)
from .ui_auto_workflow import AgentSOPWorkflow, load_test_cases, run_workflow

__all__ = [
    "AgentSOPWorkflow",
    "CaseAuthoringResult",
    "build_case_run_input",
    "load_test_cases",
    "run_case_authoring_artifact",
    "run_workflow",
]
