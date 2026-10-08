"""工作流包 —— 三角色编排、步骤与结果契约、点击与设备日志证据、验收截图落盘。

公开导出：编排入口与五个数据契约、点击/日志证据的配对与渲染、验收截图落盘。
私有解析辅助（`_coerce` / `_emit_progress` / `_progress_payload` 等）留在 `workflow` 子模块。
"""

from .evidence import save_verify_screenshot
from .logcheck import (
    GRADE_LABEL,
    build_executor_log_check,
    checked_log_keywords,
    detected_log_timestamp,
    extract_action_time,
    render_log_evidence,
)
from .workflow import (
    DeviceExecutionWorkflow,
    ExecutionOutput,
    Plan,
    Step,
    VerificationOutput,
    WorkflowResult,
)

__all__ = [
    "GRADE_LABEL",
    "DeviceExecutionWorkflow",
    "ExecutionOutput",
    "Plan",
    "Step",
    "VerificationOutput",
    "WorkflowResult",
    "build_executor_log_check",
    "checked_log_keywords",
    "detected_log_timestamp",
    "extract_action_time",
    "render_log_evidence",
    "save_verify_screenshot",
]
