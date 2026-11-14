"""
文件名: ➡️ sop_runner.py 🏁
路径: ➡️ engines/ae_harness/workflow/sop_runner.py 🏁
模块功能：➡️ SOP 命令行入口：读步骤 YAML、建两个角色、跑流程 🏁
Python 调试：➡️ python -m engines.ae_harness.workflow.sop_runner 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 2.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. build_agents: 建执行者（全量工具）与验收者（只读工具）。
2. run: 读步骤 YAML，交给 sop.run_sop 跑完并打印每步结论。
3. 实现都在 workflow/sop/ 下，本文件只做装配与展示。
🏁
关联模块：➡️
1. engines.ae_harness.workflow.sop: load_spec / run_sop。
2. engines.ae_harness.agents.creator: create_agent。
3. engines.ae_harness.tools: build_adb_tools / build_adb_readonly_tools。
🏁
测试：➡️
1. python -m engines.ae_harness.workflow.sop_runner
2. python -m engines.ae_harness.workflow.sop_runner "自定义任务描述"
3. python -m engines.ae_harness.workflow.sop_runner --spec 其他.yaml
🏁
"""

from __future__ import annotations

import sys

from pathlib import Path

from engines.ae_harness.agents.creator import AgentBundle, create_agent
from engines.ae_harness.assistant._bootstrap import (
    configure_runtime,
    print_summary,
    run_main,
)
from engines.ae_harness.event import HtmlReportRenderer
from engines.ae_harness.middleware import ObservationMiddleware
from engines.ae_harness.tools import build_adb_readonly_tools, build_adb_tools
from engines.ae_harness.tools.adb.render import render_grid_marks
from engines.ae_harness.workflow.sop import load_spec, run_sop

# 用哪个模型；换成 deepseek_chat_flash 可直连官方。
MODEL_SHORT = "govee_chat_flash"
ROLE_KEY = "sop_ui"

# 产物根目录：与单角色入口共用同一个 logs，按角色名区分文件。
LOG_DIR = Path(__file__).resolve().parents[1] / "logs"

# 默认步骤文件。
DEFAULT_SPEC = Path(__file__).resolve().parent / "sop" / "steps" / "ui_task.yaml"


async def build_agents() -> tuple[AgentBundle, AgentBundle, ObservationMiddleware]:
    """
    建执行者与验收者，共用一个观测中间件。

    执行者挂全量 adb 工具，验收者只挂只读工具。

    Returns:
        (执行者, 验收者, 观测中间件)；两个智能体共用同一个观测中间件，
        观测记录里带 agent 名，因此仍能分清是谁的。
    """
    observer = ObservationMiddleware()
    executor = create_agent("ui_executor", "UI_EXECUTOR_PROMPT", MODEL_SHORT, observers=[observer])
    for tool in build_adb_tools():
        await executor.agent.toolkit.add_tool(tool)

    verifier = create_agent("ui_verifier", "UI_VERIFIER_PROMPT", MODEL_SHORT, observers=[observer])
    for tool in build_adb_readonly_tools():
        await verifier.agent.toolkit.add_tool(tool)
    return executor, verifier, observer


def _parse_args(argv: list[str]) -> tuple[Path, str]:
    """
    解析命令行参数。

    Args:
        argv: 去掉程序名后的参数列表。

    Returns:
        (步骤文件路径, 任务描述覆盖；空串表示用文件里的)。
    """
    spec_path = DEFAULT_SPEC
    rest: list[str] = []
    index = 0
    while index < len(argv):
        if argv[index] == "--spec" and index + 1 < len(argv):
            spec_path = Path(argv[index + 1]).expanduser()
            index += 2
            continue
        rest.append(argv[index])
        index += 1
    return spec_path, " ".join(rest).strip()


async def main() -> None:
    """
    读步骤文件并跑一次流程。

    命令行：
        --spec <path>   指定步骤 YAML，默认用 sop/steps/ui_task.yaml
        其余文本          作为任务描述覆盖 YAML 里的 task
    """
    spec_path, task_override = _parse_args(sys.argv[1:])
    spec = load_spec(spec_path)
    if task_override:
        spec.task = task_override

    print(f"步骤文件：{spec_path}")
    print(f"流程：{spec.name}（{len(spec.steps)} 步）")
    for index, step in enumerate(spec.steps, 1):
        print(f"  {index}. {step.subject}")

    executor, verifier, observer = await build_agents()
    renderer = HtmlReportRenderer(step_extras={"adb_screenshot_grid": render_grid_marks})
    result = await run_sop(
        executor.agent,
        verifier.agent,
        spec,
        log_dir=LOG_DIR,
        role=ROLE_KEY,
        renderer=renderer,
        api_key_env=executor.api_key_env,
        observations=observer.records,
        role_api_keys={
            executor.agent.name: executor.api_key_env,
            verifier.agent.name: verifier.api_key_env,
        },
    )

    print("\n=== 流程结果 ===")
    print("阶段:", result.phase)
    for index, outcome in enumerate(result.steps, 1):
        mark = "通过" if outcome.passed else "未通过"
        print(f"  第 {index} 步 {outcome.subject}：{mark}（{outcome.attempts} 次尝试）")
        if outcome.message:
            print(f"    {outcome.message[:160]}")
    if result.record is not None:
        print_summary(result.record)


def _run() -> None:
    """入口包装：配置运行时后执行主协程。"""
    configure_runtime()
    run_main(main)


if __name__ == "__main__":
    _run()
