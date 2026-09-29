"""AI 引擎协议层 — Django 与可替换 AI 引擎之间的进程内契约。

对齐设备引擎 `engines/device/base.py`（L1c 可替换插槽）。Django 只传
`TaskRequest`（任务表单 + 三角色模型配置 + 工具清单），引擎返回归一化
`TaskResult`。换框架只换引擎实现，Django 逻辑不变。

导入边界：零 `django.*`、零 `apps.*`；只依赖标准库类型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal, Protocol

ProgressCallback = Callable[[dict], None]

__all__ = [
    "AiEngine",
    "LogEvidenceProvider",
    "ModelSpec",
    "ProgressCallback",
    "TaskRequest",
    "TaskResult",
    "ToolSpec",
]


@dataclass
class ModelSpec:
    """单个模型连接（api_key 已由 Django 解密，base_url 已由 Django 解析默认值）。"""

    provider: str
    model_name: str
    api_key: str = ""
    base_url: str = ""


@dataclass
class ToolSpec:
    """平台工具（框架无关：纯函数 + 元数据，由 Django 注入引擎）。"""

    name: str
    handler: Callable[..., str]  # 同步函数，内部只调各 App api.py，返回 JSON 字符串
    read_only: bool = True
    auto_allow: bool = False


class LogEvidenceProvider(Protocol):
    """设备日志证据提供者 —— Django 侧注入，引擎只经协议调用。

    与 `on_progress` 同构：只含标准库类型，引擎不直接碰串口 / TCP 句柄，也不 import `engines.device`。
    工作流在把步骤交给执行模型**之前**开窗，在验收之前读窗。
    """

    def open_window(self, device: str, label: str = "") -> str:
        """开一个日志证据窗口，返回窗口标识（必须早于动作发出）。"""
        ...

    def read_window(
        self,
        device: str,
        window_id: str = "",
        action_times: list[str] | None = None,
        wait_seconds: float = 0.0,
    ) -> dict:
        """读窗口并返回日志证据（含等级标注）；未开窗时应抛错，不得用历史日志顶替。

        `action_times` 是本步骤**全部**副作用动作的发出时刻（一步可能有多次点击）：
        取证窗取「每次动作 + 阈值」的并集，只有首次动作会把后面的响应误判成超窗。
        """
        ...


@dataclass
class TaskRequest:
    """任务表单 + 模型 + 工具 —— Django 传给引擎的唯一入参。"""

    goal: str
    models: dict[str, ModelSpec]  # {"planner","executor","verifier"}
    tools: list[ToolSpec] = field(default_factory=list)
    max_loops: int = 3
    device_serial: str = ""
    user_id: str = ""
    task_id: int = 0  # 验收截图落盘目录 ai_tasks/{task_id}/
    media_root: str = ""  # 绝对路径；空则跳过截图落盘
    on_progress: ProgressCallback | None = None  # 规划/每轮/每目标检查点；引擎不写库
    skill_dirs: list[str] = field(default_factory=list)  # enable_skills 打开时注入的 skill 目录
    # 设备日志证据提供者（Django 注入；空 = 无日志证据，验收阶段标注后照常执行）
    log_evidence: LogEvidenceProvider | None = None
    # 当前日志关键词表文本（关键词 → 功能点；Django 从运行时索引渲染后注入，空 = 不附）
    log_keywords: str = ""


@dataclass
class TaskResult:
    """归一化结果 —— 引擎唯一返回（设备控制）。"""

    status: Literal["success", "fail"]
    summary: str = ""
    completed: list[str] = field(default_factory=list)
    failed: list[dict] = field(default_factory=list)
    plans: list[dict] = field(default_factory=list)
    log: list[dict] = field(default_factory=list)
    usage: dict = field(default_factory=dict)  # token 用量（计费），含 models 拆分
    models: dict = field(default_factory=dict)  # planner/executor/verifier 模型名
    reason: str = ""


class AiEngine(Protocol):
    """AI 引擎协议 —— 阻塞执行，框架细节（async 装配/循环）全在实现内部。"""

    def run(self, req: TaskRequest) -> TaskResult: ...
