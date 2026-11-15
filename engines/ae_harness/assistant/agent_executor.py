"""
文件名: ➡️ agent_executor.py 🏁
路径: ➡️ engines/ae_harness/assistant/agent_executor.py 🏁
模块功能：➡️ UI 控制试验入口：建执行者、跑任务，并按轮次产出报告 🏁
Python 调试：➡️ python -m engines.ae_harness.assistant.agent_executor "点击设置" 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 6.1.0 🏁
修改时间: ➡️ 2026-11-15 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. build_agent: 按 UI_EXECUTOR_PROMPT 建执行者，挂上 16 个 adb 工具；知识库模块存在时再挂只读检索工具。
2. run_task: 跑一轮任务，用 AgentEventRecorder 记录、HtmlReportRenderer 出页面。
3. main: 带参数执行单任务；不带参数进入交互模式，每轮各产出一份报告。
🏁
关联模块：➡️
1. engines.ae_harness.agents.creator: create_agent。
2. engines.ae_harness.tools: build_adb_tools。
3. engines.ae_harness.event: 记录与渲染。
4. engines.ae_harness.tools.adb.render: 网格锚点展示。
🏁
测试：➡️
1. python -m engines.ae_harness.assistant.agent_executor "告诉我现在在哪个应用"
2. 产物在 engines/ae_harness/logs/<时间戳>/ 下。
🏁
"""

import sys
import time

from pathlib import Path

from agentscope.message import UserMsg

from engines.ae_harness.agents.creator import AgentBundle, create_agent
from engines.ae_harness.assistant._bootstrap import configure_runtime, print_summary, run_main
from engines.ae_harness.event import AgentEventRecorder, HtmlReportRenderer
from engines.ae_harness.middleware import ObservationMiddleware
from engines.ae_harness.tools import build_adb_tools
from engines.ae_harness.tools.adb.render import render_grid_marks

try:  # 知识库是独立模块：整目录删除后这里自动跳过，不影响执行者其它能力
    from engines.ae_harness.knowledge import build_knowledge_tools
except ModuleNotFoundError as exc:  # pragma: no cover - 取决于知识库目录是否存在
    if not (exc.name or "").startswith("engines.ae_harness.knowledge"):
        raise
    build_knowledge_tools = None  # type: ignore[assignment]

# 用哪个模型；换成 deepseek_chat_flash 可直连官方。
MODEL_SHORT = "govee_chat_flash"
ROLE_KEY = "ui_executor"
PROMPT_NAME = "UI_EXECUTOR_PROMPT"

# 产物根目录；每轮在其下新建时间戳目录。
LOG_DIR = Path(__file__).resolve().parents[1] / "logs"


async def build_agent() -> tuple[AgentBundle, ObservationMiddleware]:
    """
    建一个挂好 adb 工具的 UI 执行者，并附带一个只读观测中间件。

    Returns:
        智能体 bundle 与观测中间件；观测中间件已挂到智能体上，记录写进它的 records。
    """
    observer = ObservationMiddleware()
    bundle = create_agent(ROLE_KEY, PROMPT_NAME, MODEL_SHORT, observers=[observer])
    for tool in build_adb_tools():
        await bundle.agent.toolkit.add_tool(tool)
    if build_knowledge_tools is not None:
        for tool in build_knowledge_tools():
            await bundle.agent.toolkit.add_tool(tool)
    return bundle, observer


async def run_task(
    bundle: AgentBundle,
    observer: ObservationMiddleware,
    renderer: HtmlReportRenderer,
    task: str,
) -> None:
    """
    执行一条任务：记录事件、渲染报告、打印结果。

    Args:
        bundle: 已装配好的执行者与其模型身份。
        observer: 观测中间件；它的记录会被写进本次产物。
        renderer: 报告渲染器，可跨轮复用。
        task: 自然语言任务描述。
    """
    agent = bundle.agent
    recorder = AgentEventRecorder(
        LOG_DIR,
        ROLE_KEY,
        api_key_env=bundle.api_key_env,
        observations=observer.records,
    )
    schemas = {
        item["function"]["name"]: item["function"]
        for item in await agent.toolkit.get_tool_schemas()
    }
    recorder.begin(task, schemas=schemas)
    begin = time.perf_counter()
    async for event in agent.reply_stream([UserMsg(name="user", content=task)]):
        recorder.on_event(event)
    cost_s = round(time.perf_counter() - begin, 2)
    record = recorder.finish(cost_s)
    renderer.save(record)

    print("\n=== 结果 ===")
    print(record.final_text)
    print_summary(record)


async def main() -> None:
    """
    带参数执行单任务；不带参数进入交互模式。

    交互模式下输入 exit / quit 退出，每轮各产出一份报告。
    """
    bundle, observer = await build_agent()
    renderer = HtmlReportRenderer(step_extras={"adb_screenshot_grid": render_grid_marks})

    task = " ".join(sys.argv[1:]).strip()
    if task:
        await run_task(bundle, observer, renderer, task)
        return

    print("UI 控制试验入口，已挂载 adb 工具。")
    print("输入任务后回车执行；输入 exit 退出。每轮产出一份报告。")
    while True:
        try:
            line = input("\n任务> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line or line.lower() in {"exit", "quit"}:
            break
        await run_task(bundle, observer, renderer, line)


def _run() -> None:
    """入口包装：配置运行时后执行主协程。"""
    configure_runtime()
    run_main(main)


if __name__ == "__main__":
    _run()
