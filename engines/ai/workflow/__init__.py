"""工作流包 —— SOP 步骤编排、步骤与结果契约、点击与设备日志证据、验收截图落盘。

公开导出编排入口、步骤与结果契约、SOP 步骤层、证据配对与渲染、截图落盘；
私有解析辅助留在 `workflow` 子模块。
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
from .sop_step import (
    ExecutionSOPContext,
    ExecutionSOPStep,
    ExecutorAdapter,
    StepAttemptSink,
    VerifierAdapter,
    verdict_payload,
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
    "ExecutionSOPContext",
    "ExecutionSOPStep",
    "ExecutorAdapter",
    "Plan",
    "Step",
    "StepAttemptSink",
    "VerificationOutput",
    "VerifierAdapter",
    "WorkflowResult",
    "build_executor_log_check",
    "checked_log_keywords",
    "detected_log_timestamp",
    "extract_action_time",
    "render_log_evidence",
    "save_verify_screenshot",
    "verdict_payload",
]
