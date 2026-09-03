"""AI 引擎协议层 — Django 与可替换 AI 引擎之间的进程内契约。

对齐设备引擎 `engines/device/base.py`（L1c 可替换插槽）。Django 只传
`TaskRequest`（任务表单 + 三角色模型配置 + 工具清单），引擎返回归一化
`TaskResult`。换框架只换引擎实现，Django 逻辑不变。

导入边界：零 `django.*`、零 `apps.*`；只依赖标准库类型。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Literal, Protocol

__all__ = [
    "AiEngine",
    "ModelSpec",
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


@dataclass
class TaskRequest:
    """任务表单 + 模型 + 工具 —— Django 传给引擎的唯一入参。"""

    goal: str
    route: str  # "device_control" | "platform_task"
    models: dict[str, ModelSpec]  # {"planner","executor","verifier"}
    tools: list[ToolSpec] = field(default_factory=list)
    max_loops: int = 3
    requirements: str = ""
    checklist: str = ""
    report_name: str = ""
    device_serial: str = ""
    user_id: str = ""


@dataclass
class TaskResult:
    """归一化结果 —— 引擎唯一返回（device_control / platform_task 两条线路同构）。"""

    status: Literal["success", "fail"]
    summary: str = ""
    completed: list[str] = field(default_factory=list)
    failed: list[dict] = field(default_factory=list)
    log: list[dict] = field(default_factory=list)
    usage: dict = field(default_factory=dict)  # token 用量（计费），含 models 拆分
    reason: str = ""


class AiEngine(Protocol):
    """AI 引擎协议 —— 阻塞执行，框架细节（async 装配/循环）全在实现内部。"""

    def run(self, req: TaskRequest) -> TaskResult: ...
