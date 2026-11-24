"""
文件名: ➡️ sop_ui.py 🏁
路径: ➡️ engines/backend_bridge/workflow/sop_ui.py 🏁
模块功能：➡️ 一次 SOP 运行的结果形状：每步结论与整体用量 🏁
Python 调试：➡️ python -m engines.backend_bridge.workflow.sop_ui 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. SopStepResult: 一步的结论，含是否通过、尝试次数与验收说明。
2. SopRunResult: 一次运行的每步结论、产物路径与用量汇总。
3. 只放结果形状：旧的 run_sop_once 连同写死的提示词文件一起退役。
🏁
关联模块：➡️
1. engines.backend_bridge.workflow.bound_sop: 复用这两个结果类型整理一次运行。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["SopRunResult", "SopStepResult"]


@dataclass(frozen=True)
class SopStepResult:
    """
    一步的结论。

    Attributes:
        subject: 步骤名。
        passed: 验收是否通过。
        attempts: 实际尝试次数。
        message: 最后一次验收的说明；通过时是依据，不通过时是缺什么。
        expected: 这一步必须达成的结果；步骤定义没有时为空串。
    """

    subject: str
    passed: bool
    attempts: int
    message: str = ""
    expected: str = ""


@dataclass(frozen=True)
class SopRunResult:
    """
    一次 SOP 运行的产物与用量。

    Attributes:
        phase: 流程最终阶段。
        steps: 每步的结论。
        report_path: HTML 报告路径。
        log_path: JSONL 事件日志路径。
        model: 本次使用的模型名。
        tokens: 四类 token 合计（input / output / cache_hit / cache_creation）。
        by_api_key_env: 密钥环境变量名到该组调用次数的映射。
        usages: 逐次调用的用量明细（可直接序列化）。
        cost_s: 本次运行的墙钟耗时秒数。
    """

    phase: str
    steps: list[SopStepResult] = field(default_factory=list)
    report_path: Path | None = None
    log_path: Path | None = None
    model: str = ""
    tokens: dict = field(default_factory=dict)
    by_api_key_env: dict = field(default_factory=dict)
    usages: list = field(default_factory=list)
    cost_s: float = 0.0
