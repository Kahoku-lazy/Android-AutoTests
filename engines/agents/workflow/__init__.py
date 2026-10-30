"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/agents/workflow/__init__.py 🏁
模块功能：➡️ SOP 工作流：设备检查一次运行与家电用例编写一次运行 🏁
Python 调试：➡️ python -m engines.agents.workflow 🏁
时间：➡️ 2026-10-30 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. （模块无公开类/函数，见源码）
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/graybox/unit/test_case_authoring_modules.py: 模块化用例编写：规划切分、截断拆分、文本拼装与整份模式回退
2. tests/graybox/unit/test_case_authoring_roles.py: 家电测试用例编写/验收角色的装配与成对运行入口
3. tests/graybox/unit/test_case_goal_workflow.py: GoalPipeline 模块池：模块存储、单模块判定与截断兜底
4. tests/graybox/unit/test_sop_steps.py: 步骤输入装配：短名、必须达成的结果，以及已启动的角色
🏁
"""

from .case_authoring_workflow import (
    CaseAuthoringResult,
    CaseAuthoringWorkflow,
    ModuleOutcome,
    build_run_input,
    run_case_authoring,
    run_case_authoring_modules,
)
from .ui_auto_workflow import AgentSOPWorkflow, load_test_cases, run_workflow

__all__ = [
    "AgentSOPWorkflow",
    "CaseAuthoringResult",
    "CaseAuthoringWorkflow",
    "ModuleOutcome",
    "build_run_input",
    "load_test_cases",
    "run_case_authoring",
    "run_case_authoring_modules",
    "run_workflow",
]
