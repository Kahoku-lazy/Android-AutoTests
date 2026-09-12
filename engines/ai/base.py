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
