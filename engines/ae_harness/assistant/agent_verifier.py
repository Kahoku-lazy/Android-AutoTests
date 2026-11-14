"""
文件名: ➡️ agent_verifier.py 🏁
路径: ➡️ engines/ae_harness/assistant/agent_verifier.py 🏁
模块功能：➡️ Agent 验收入口：建验收角色，核对预期检查项是否成立 🏁
Python 调试：➡️ python -m engines.ae_harness.assistant.agent_verifier "当前在设置页" 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. build_agent: 按 UI_VERIFIER_PROMPT 建验收者，并挂上 adb 工具。
2. verify: 核对预期检查项是否成立，解析出 passed 与 message 两行。
3. main: 带参数核对单个检查项；不带参数进入交互模式，每个检查项产出一份报告。
🏁
关联模块：➡️
1. engines.ae_harness.agents.creator: create_agent。
2. engines.ae_harness.agents.config.prompts.UI_VERIFIER_PROMPT: 验收判据。
3. engines.ae_harness.event: 记录与渲染。
4. engines.ae_harness.assistant.agent_executor: 执行侧入口，与本文件配对使用。
🏁
测试：➡️
1. python -m engines.ae_harness.assistant.agent_verifier "当前屏幕能看到「设置」页面"
2. 产物在 engines/ae_harness/logs/<时间戳>/ 下。
🏁
"""

import re
import sys
import time

from pathlib import Path

from agentscope.message import UserMsg

from engines.ae_harness.agents.creator import AgentBundle, create_agent
from engines.ae_harness.assistant._bootstrap import configure_runtime, print_summary, run_main
from engines.ae_harness.event import AgentEventRecorder, HtmlReportRenderer
from engines.ae_harness.middleware import ObservationMiddleware
from engines.ae_harness.tools import build_adb_readonly_tools
from engines.ae_harness.tools.adb.render import render_grid_marks

# 用哪个模型；换成 deepseek_chat_flash 可直连官方。
MODEL_SHORT = "govee_chat_flash"
ROLE_KEY = "ui_verifier"
PROMPT_NAME = "UI_VERIFIER_PROMPT"

# 产物根目录；每轮在其下新建时间戳目录。
LOG_DIR = Path(__file__).resolve().parents[1] / "logs"

# 结论的两行约定。
_VERDICT_RE = re.compile(r"^\s*passed\s*[:：]\s*(true|false)\s*$", re.I | re.M)
_MESSAGE_RE = re.compile(r"^\s*message\s*[:：]\s*(.+)$", re.I | re.M)


def parse_verdict(text: str) -> tuple[bool, str]:
    """
    从验收输出里取出结论。

    Args:
        text: 验收者的最终回复正文。

    Returns:
        (是否通过, 说明)；没有 passed 行时按不通过处理。
    """
    verdict = _VERDICT_RE.search(text or "")
    if verdict is None:
        snippet = " ".join((text or "").split())[:300]
        return False, f"验收输出缺少 passed 行，按不通过处理。原始输出：{snippet}"
    passed = verdict.group(1).lower() == "true"
    message = _MESSAGE_RE.search(text or "")
    return passed, (message.group(1).strip() if message else "")


async def build_agent() -> tuple[AgentBundle, ObservationMiddleware]:
    """
    建一个只挂只读工具的验收者，并附带一个只读观测中间件。

    只读工具集从工具层面杜绝写操作，提示词里的约束只是第二道防线。

    Returns:
        智能体 bundle 与观测中间件；观测中间件已挂到智能体上，记录写进它的 records。
    """
    observer = ObservationMiddleware()
    bundle = create_agent(ROLE_KEY, PROMPT_NAME, MODEL_SHORT, observers=[observer])
    for tool in build_adb_readonly_tools():
        await bundle.agent.toolkit.add_tool(tool)
    return bundle


async def verify(
    bundle: AgentBundle,
    observer: ObservationMiddleware,
    renderer: HtmlReportRenderer,
    check: str,
) -> tuple[bool, str]:
    """
    核对一个预期检查项是否成立：记录事件、渲染报告、解析结论。

    Args:
        bundle: 已装配好的验收者与其模型身份。
        observer: 观测中间件；它的记录会被写进本次产物。
        renderer: 报告渲染器，可跨检查项复用。
        check: 任务要求的一个预期检查项。

    Returns:
        (是否成立, 说明)。
    """
    agent = bundle.agent
    prompt = (
        "请核对下面这个预期检查项是否实际成立。\n\n"
        f"【预期检查项】\n{check}\n\n"
        "按角色要求自己取证，最后只输出 passed 与 message 两行。"
    )
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
    recorder.begin(check, schemas=schemas)
    begin = time.perf_counter()
    async for event in agent.reply_stream([UserMsg(name="user", content=prompt)]):
        recorder.on_event(event)
    cost_s = round(time.perf_counter() - begin, 2)
    record = recorder.finish(cost_s)
    renderer.save(record)

    passed, message = parse_verdict(record.final_text)
    print("\n=== 结论 ===")
    print(f"{'通过' if passed else '不通过'}")
    print(message or "（无说明）")
    print_summary(record)
    return passed, message


async def main() -> None:
    """
    带参数核对单个检查项；不带参数进入交互模式。

    交互模式下输入 exit / quit 退出，每个检查项产出一份报告。
    """
    bundle, observer = await build_agent()
    renderer = HtmlReportRenderer(step_extras={"adb_screenshot_grid": render_grid_marks})

    check = " ".join(sys.argv[1:]).strip()
    if check:
        await verify(bundle, observer, renderer, check)
        return

    print("验收入口，已挂载 adb 工具。日志查询工具尚未接入。")
    print("输入一个预期检查项后回车核对；输入 exit 退出。")
    while True:
        try:
            line = input("\n验收> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not line or line.lower() in {"exit", "quit"}:
            break
        await verify(bundle, observer, renderer, line)


def _run() -> None:
    """入口包装：配置运行时后执行主协程。"""
    configure_runtime()
    run_main(main)


if __name__ == "__main__":
    _run()
