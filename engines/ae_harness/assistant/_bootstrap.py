"""
文件名: ➡️ _bootstrap.py 🏁
路径: ➡️ engines/ae_harness/assistant/_bootstrap.py 🏁
模块功能：➡️ 角色入口的运行时引导：编码、日志级别、汇总打印、异常包装 🏁
Python 调试：➡️ python -m engines.ae_harness.assistant._bootstrap 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. configure_runtime: 统一 stdout 编码与框架日志级别。
2. print_summary: 打印一轮运行汇总。
3. run_main: 跑入口协程，把未处理异常打印出来再抛。
4. 本模块只服务 assistant/ 下的角色入口，不对外复用。
🏁
关联模块：➡️
1. engines.ae_harness.assistant.agent_executor / agent_verifier: 两个入口共用本骨架。
2. engines.ae_harness.event.record: RunRecord 的字段来源。
🏁
测试：➡️
1. 见两个入口的实跑。
🏁
"""

from __future__ import annotations

import asyncio
import sys
import traceback

from collections.abc import Awaitable, Callable

import agentscope

__all__ = ["configure_runtime", "print_summary", "run_main"]

# 框架日志级别：INFO 会把每次图片裁剪都刷到 stderr，默认降到 WARNING。
LOG_LEVEL = "WARNING"


def configure_runtime() -> None:
    """
    统一 stdout 编码与框架日志级别。

    Windows 控制台默认 GBK，模型输出含特殊字符会编码失败。
    """
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            # 明确选择忽略：stdout 已被重定向或已关闭时不支持重设编码，
            # 保持原编码照常输出，比因此中断角色入口更合适。
            pass
    agentscope.setup_logger(LOG_LEVEL)


def print_summary(record: object) -> None:
    """
    打印一轮运行汇总。

    Args:
        record: `AgentEventRecorder.finish` 返回的整轮记录。
    """
    summary = record.summary
    by_tool = ", ".join(f"{name}×{count}" for name, count in sorted(summary["by_tool"].items()))
    print("\n=== 汇总 ===")
    print(
        f"耗时 {record.cost_s:.2f} s | 工具调用 {summary['tool_calls']} 次 | "
        f"失败 {summary['failed']} 次 | 截图 {summary['screenshots']} 次"
    )
    print(f"分布 {by_tool or '无'}")
    print(f"目录 {record.directory}")
    print(f"日志 {record.log_path}")
    print(f"报告 {record.html_path}")


def run_main(main: Callable[[], Awaitable[None]]) -> None:
    """
    跑入口协程，把未处理异常打印出来。

    Args:
        main: 入口协程函数。

    Raises:
        SystemExit: 原样透传。
        BaseException: 打印 traceback 后原样抛出，保持失败退出码。
    """
    try:
        asyncio.run(main())
    except SystemExit:
        raise
    except BaseException:
        print("\n=== 未处理异常 ===", file=sys.stderr)
        traceback.print_exc()
        raise
