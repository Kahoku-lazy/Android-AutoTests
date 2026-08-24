"""
Test case and result data models.
Migrated and extended from sku_stress_test.
"""

from dataclasses import dataclass, field
from enum import Enum

from .step_types import TestStep

# Enum 内的单下划线名会被收为成员，展示标签放模块级常量（枚举保持零 Django 依赖）。
_TASK_OUTCOME_LABELS = {
    "completed": "已完成",
    "stopped": "已停止",
    "interrupted": "运行中断",
    "error": "异常终止",
}
_TASK_CARD_STATUS_LABELS = {
    "idle": "未执行",
    "queued": "排队中",
    "running": "执行中",
    "done": "已完成",
}


class TestRunStatus(str, Enum):
    """测试执行状态 — tr_test_runs.status 唯一真相源（L1b 收敛后）。

    值口径统一小写，与 TaskCard.outcome（TaskOutcome）语义对齐：
        completed = 正常跑完（对应 TaskOutcome.COMPLETED）
        stopped   = 用户停止 / 运行中断（对应 TaskOutcome.STOPPED / INTERRUPTED）
        failed    = 异常终止 / 崩溃残留（对应 TaskOutcome.ERROR / 孤儿回收）
    """

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    STOPPED = "stopped"
    FAILED = "failed"


class TaskOutcome(str, Enum):
    """任务卡终态 — tr_task_cards.outcome 唯一真相源（L1b 收敛后新增）。

    仅当 TaskCard.status = done 时有意义；空串表示未终态。
    """

    COMPLETED = "completed"  # 正常完成
    STOPPED = "stopped"  # 用户主动停止
    INTERRUPTED = "interrupted"  # 运行中断（崩溃 / 孤儿回收）
    ERROR = "error"  # 异常终止

    @classmethod
    def terminal_values(cls) -> list[str]:
        """全部终态取值集合，供 state_machine/views 校验与查询复用。"""
        return [e.value for e in cls]

    @classmethod
    def fail_values(cls) -> list[str]:
        """fail() 合法取值：终态去掉 COMPLETED（正常完成不可走 fail）。"""
        return [cls.STOPPED.value, cls.INTERRUPTED.value, cls.ERROR.value]

    @classmethod
    def choices(cls):
        """Django field choices 格式。"""
        return [(e.value, _TASK_OUTCOME_LABELS.get(e.value, e.value)) for e in cls]


class TaskCardStatus(str, Enum):
    """任务卡状态 — tr_task_cards.status 唯一真相源（L1b 收敛后新增）。

    与 TestRunStatus（run 态）不同，这是 task 态的 4 值状态机；
    终态语义由 TaskOutcome 细分。
    """

    IDLE = "idle"  # 未执行（初始态）
    QUEUED = "queued"  # 排队中（等待设备）
    RUNNING = "running"  # 执行中
    DONE = "done"  # 已终态（outcome 细分）

    @classmethod
    def choices(cls):
        """Django field choices 格式。"""
        return [(e.value, _TASK_CARD_STATUS_LABELS.get(e.value, e.value)) for e in cls]


@dataclass
class TestCaseDef:
    """Definition of a test case (mirrors DB row + JSON file format)."""

    id: str  # Unique identifier (slug)
    title: str  # Human-readable title
    category: str = ""  # Grouping category (e.g. "连接", "开关")
    description: str = ""  # Longer description
    steps: str = ""  # Summary of test steps (for CSV export)
    enabled: bool = True  # Whether this case is active
    steps_data: list = field(default_factory=list)  # list[TestStep]
    is_json: bool = False  # True if loaded from JSON definition
    package_name: str = ""  # Target app package (empty = use default)
    watchers: list = field(default_factory=list)  # [{xpath, action}] for popup handling
    created_at: str = ""  # ISO timestamp
    updated_at: str = ""  # ISO timestamp
    # ── 类型感知扩展 ──
    task_type: str = "ui_automation"  # ui_automation / api_testing / web_automation
    extra_data: dict = field(default_factory=dict)  # API/Web 专用字段

    def __post_init__(self):
        if self.steps_data is None:
            self.steps_data = []

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "category": self.category,
            "description": self.description,
            "steps": self.steps,
            "enabled": self.enabled,
            "steps_data": [s.to_dict() if isinstance(s, TestStep) else s for s in self.steps_data],
            "is_json": self.is_json,
            "package_name": self.package_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "task_type": self.task_type,
            "extra_data": self.extra_data,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "TestCaseDef":
        steps_raw = d.get("steps_data", [])
        steps_data = []
        for s in steps_raw:
            if isinstance(s, TestStep):
                steps_data.append(s)
            else:
                steps_data.append(TestStep.from_dict(s))
        return cls(
            id=d.get("id", ""),
            title=d.get("title", ""),
            category=d.get("category", ""),
            description=d.get("description", ""),
            steps=d.get("steps", ""),
            enabled=d.get("enabled", True),
            steps_data=steps_data,
            is_json=d.get("is_json", False),
            package_name=d.get("package_name", ""),
            created_at=d.get("created_at", ""),
            updated_at=d.get("updated_at", ""),
            task_type=d.get("task_type", "ui_automation"),
            extra_data=d.get("extra_data", {}),
        )

    @classmethod
    def from_db_row(cls, row: dict) -> "TestCaseDef":
        """Create from a SQLite row (from test_definitions table)."""
        import json

        steps_raw = json.loads(row.get("steps_json", "[]"))
        steps_data = [TestStep.from_dict(s) for s in steps_raw]
        return cls(
            id=row.get("id", ""),
            title=row.get("title", ""),
            category=row.get("category", ""),
            description=row.get("description", ""),
            steps=row.get("steps", ""),
            enabled=bool(row.get("enabled", 1)),
            steps_data=steps_data,
            is_json=True,
            package_name=row.get("package_name", ""),
            created_at=row.get("created_at", ""),
            updated_at=row.get("updated_at", ""),
        )


@dataclass
class TestResult:
    """Result of a single test case execution (one iteration)."""

    case_id: str
    case_title: str
    iteration: int
    result: str  # 'pass' | 'fail' | 'stopped'
    duration_ms: float
    detail: str = ""
    case_type: str = "ui_automation"  # discriminates UI/API/Web/Storage
    step_details: list | None = None  # per-step execution details with screenshot paths

    def to_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "case_title": self.case_title,
            "iteration": self.iteration,
            "result": self.result,
            "duration_ms": self.duration_ms,
            "detail": self.detail,
            "case_type": self.case_type,
        }


@dataclass
class TestRun:
    """A complete test run (one or more test cases × loop_count iterations)."""

    run_id: str  # Unique run identifier (timestamp-based)
    device_serial: str  # Target device
    status: TestRunStatus = TestRunStatus.PENDING
    selected_cases: list = field(default_factory=list)  # list of case IDs
    loop_count: int = 1  # Iterations per case
    case_results: list = field(default_factory=list)  # list[TestResult]
    perf_results: list = field(
        default_factory=list
    )  # [{case_id, case_title, iteration, description, duration}]
    summary: dict = field(default_factory=dict)  # {case_id: {pass, fail, rate}}
    started_at: str = ""
    finished_at: str = ""
    csv_path: str = ""
    log_path: str = ""

    def to_dict(self) -> dict:
        return {
            "run_id": self.run_id,
            "device_serial": self.device_serial,
            "status": self.status.value,
            "selected_cases": self.selected_cases,
            "loop_count": self.loop_count,
            "case_results": [r.to_dict() for r in self.case_results],
            "perf_results": self.perf_results,
            "summary": self.summary,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "csv_path": self.csv_path,
            "log_path": self.log_path,
        }
