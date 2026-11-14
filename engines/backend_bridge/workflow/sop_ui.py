"""
文件名: ➡️ sop_ui.py 🏁
路径: ➡️ engines/backend_bridge/workflow/sop_ui.py 🏁
模块功能：➡️ 平台 UI 执行 + 验收 SOP 的一次运行入口 🏁
Python 调试：➡️ python -m engines.backend_bridge.workflow.sop_ui 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. SopStepResult / SopRunResult: 一次运行的每步结论与整体结果。
2. run_sop_once: 选流程 → 覆盖任务描述 → 调 ae_harness 的 run_sop → 整理结果；不打印、不交互。
3. 每次调用新建一对角色，跑完即弃，不跨运行复用上下文。
🏁
关联模块：➡️
1. engines.ae_harness.workflow.sop: 导入 load_spec / run_sop，编排实现全在那里。
2. engines.backend_bridge.workflow.roles: 导入 build_sop_roles，装配两个角色。
3. engines.backend_bridge.reports: 报告路径唯一来源。
4. engines.ae_harness.event: 导入 summarize，汇总四类 token。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_sop_ui.py: 结果字段、不打印、两次运行互不影响
2. 真机：python manage.py run_ui_sop "回到桌面"
🏁
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import engines.ae_harness.workflow.sop as sop_package

from engines.ae_harness.event import summarize
from engines.ae_harness.workflow.sop import load_spec, run_sop
from engines.backend_bridge.reports import REPORT_ROOT
from engines.backend_bridge.workflow.roles import build_sop_roles

__all__ = ["SPEC_KEYS", "SopRunResult", "SopStepResult", "run_sop_once"]

# 平台可选的流程：键 → ae_harness 的步骤文件；不新增第二份步骤格式。
STEPS_DIR = Path(sop_package.__file__).resolve().parent / "steps"
SPEC_KEYS = {
    "ui_task": STEPS_DIR / "ui_task.yaml",
    "govee_widget": STEPS_DIR / "govee_widget.yaml",
}

# 报告文件名里的角色名：与单角色的 ui_executor 区分开。
SOP_ROLE = "sop_ui"


@dataclass(frozen=True)
class SopStepResult:
    """
    一步的结论。

    Attributes:
        subject: 步骤名。
        passed: 验收是否通过。
        attempts: 实际尝试次数。
        message: 最后一次验收的说明；通过时是依据，不通过时是缺什么。
    """

    subject: str
    passed: bool
    attempts: int
    message: str = ""


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


async def run_sop_once(
    task: str,
    *,
    spec_key: str = "ui_task",
    model_short: str | None = None,
    report_root: Path | None = None,
    controls: list | None = None,
) -> SopRunResult:
    """
    跑一次执行 + 验收 SOP。

    全程不向标准输出写任何内容：结果通过返回值交给调用方。

    Args:
        task: 任务描述，写进流程的 `task` 字段（不新增步骤）。
        spec_key: 流程键，取 `SPEC_KEYS` 里的键；默认通用 UI 流程。
        model_short: 模型短名；不传则用默认值。
        report_root: 报告根目录；不传则用平台报告根。
        controls: 额外的中间件（重试 / 预算 / 取消）；不传则只挂观测。两个角色共用。

    Returns:
        本次运行的每步结论、产物路径与用量汇总。

    Raises:
        KeyError: 流程键不存在。
        ValueError: 模型短名不存在或密钥没配。
        FileNotFoundError: 步骤文件或提示词文件不存在。
        SopSpecError: 步骤文件不合法。
    """
    spec_path = SPEC_KEYS[spec_key]
    spec = load_spec(spec_path)
    if task.strip():
        spec.task = task.strip()

    roles = await build_sop_roles(model_short=model_short, controls=controls)
    root = report_root if report_root is not None else REPORT_ROOT

    result = await run_sop(
        roles.executor.agent,
        roles.verifier.agent,
        spec,
        log_dir=root,
        role=SOP_ROLE,
        api_key_env=roles.executor.api_key_env,
        role_api_keys={
            roles.executor.agent.name: roles.executor.api_key_env,
            roles.verifier.agent.name: roles.verifier.api_key_env,
        },
        observations=roles.observer.records,
    )

    record = result.record
    totals = summarize(record.usages) if record is not None else None
    summary = totals.as_dict() if totals is not None else {}
    model = str(getattr(getattr(roles.executor.agent, "model", None), "model", "") or "")

    return SopRunResult(
        phase=result.phase,
        steps=[
            SopStepResult(
                subject=item.subject,
                passed=item.passed,
                attempts=item.attempts,
                message=item.message,
            )
            for item in result.steps
        ],
        report_path=record.html_path if record is not None else None,
        log_path=record.log_path if record is not None else None,
        model=model,
        tokens={
            "input": summary.get("input", 0),
            "output": summary.get("output", 0),
            "cache_hit": summary.get("cache_hit", 0),
            "cache_creation": summary.get("cache_creation", 0),
        },
        by_api_key_env=dict(totals.by_api_key_env) if totals is not None else {},
        usages=[item.as_dict() for item in record.usages] if record is not None else [],
        cost_s=float(record.cost_s) if record is not None else 0.0,
    )
