"""
Executor 统一接口 — 所有执行器模块实现此协议。

调度器通过此接口与执行器解耦：
- 调度器负责：排队、并发、设备状态、DB 持久化、状态机
- 执行器负责：执行测试步骤、通过 callbacks 上报进度、返回 RunResult
"""
from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


# ═══════════════════════════════════════════════════════
# 数据结构
# ═══════════════════════════════════════════════════════

@dataclass
class StepEvent:
    """单步执行事件 — 执行器每步通过 callbacks 上报"""
    run_id: str = ""
    case_id: str = ""
    iteration: int = 0
    step_index: int = 0
    total_steps: int = 0
    step_type: str = ""
    description: str = ""
    result: str = ""                # "running" | "pass" | "fail" | "stopped" | "skip"
    log_line: str = ""
    duration_ms: float = 0.0


@dataclass
class CaseResult:
    """单个用例的执行结果"""
    case_id: str = ""
    case_title: str = ""
    pass_count: int = 0
    fail_count: int = 0
    total: int = 0
    iterations: list = field(default_factory=list)  # [{iteration, result, duration_ms, detail}]


@dataclass
class RunResult:
    """执行器返回的完整执行结果"""
    status: str = "completed"       # completed | stopped | error
    case_results: list = field(default_factory=list)   # list[CaseResult]
    log_lines: list = field(default_factory=list)
    perf_results: list = field(default_factory=list)
    summary: dict = field(default_factory=dict)


# ═══════════════════════════════════════════════════════
# 协议
# ═══════════════════════════════════════════════════════

@runtime_checkable
class Executor(Protocol):
    """执行器协议。每个执行器模块（ui/api/web）实现此接口。

    调度器向执行器传入：
    - spec: TaskSpec（用例数据 + 配置）
    - callbacks: ExecutorCallbacks（进度上报接口）

    执行器返回：
    - RunResult（汇总结果）
    """

    async def execute(self, spec, callbacks) -> RunResult:
        """
        执行测试用例序列。

        spec 包含：
        - run_id: str
        - test_cases: list[TestCaseDef]
        - loop_count: int
        - interval_seconds: int
        - extra: dict  (执行器特定参数)

        callbacks 包含：
        - on_step_started(run_id, case_id, iteration, step_index, total, type, desc)
        - on_step_result(run_id, case_id, iteration, step_index, total, type, desc, result)
        - on_log(run_id, message)
        - on_case_started(run_id, case_id, title, loop_count)
        - on_case_finished(run_id, case_id, pass_count, fail_count, rate)
        - on_heartbeat(run_id)
        - stopped() -> bool

        返回 RunResult。
        """
        ...
