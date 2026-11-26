from __future__ import annotations

import asyncio
import sys
import traceback

from collections.abc import Awaitable, Callable

import agentscope

__all__ = ["configure_runtime", "print_summary", "run_main"]

LOG_LEVEL = "WARNING"


def configure_runtime() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):
            pass  # silent-except
    agentscope.setup_logger(LOG_LEVEL)


def print_summary(record: object) -> None:
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
    try:
        asyncio.run(main())
    except SystemExit:
        raise
    except BaseException:
        print("\n=== 未处理异常 ===", file=sys.stderr)
        traceback.print_exc()
        raise
