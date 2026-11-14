"""
文件名: ➡️ run.py 🏁
路径: ➡️ engines/backend_bridge/run.py 🏁
模块功能：➡️ 平台运行入口：跑一次 UI 执行任务，产出报告并返回结构化结果 🏁
Python 调试：➡️ python -m engines.backend_bridge.run 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. run_ui_task: 一次性运行入口——建临时会话、跑一轮、返回结果；不打印、不交互。
2. UiRunResult: 结果形状定义在 result.py，这里原样导出，调用方只认这一个名字。
3. 需要多轮上下文时用 session.py 的会话，不必反复调本入口。
🏁
关联模块：➡️
1. engines.backend_bridge.session: 导入 open_session，一次性运行建临时会话。
2. engines.backend_bridge.result: 导入 UiRunResult，结果形状唯一来源。
3. engines.backend_bridge.reports: 报告路径唯一来源（经由 session 使用）。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_run.py: 结果字段、目录按需创建、不打印
2. 真机冒烟：报告落在 logs/agents/backend_bridge/ 下
🏁
"""

from __future__ import annotations

from pathlib import Path

from engines.backend_bridge.result import UiRunResult
from engines.backend_bridge.session import open_session

__all__ = ["UiRunResult", "run_ui_task"]


async def run_ui_task(
    task: str,
    *,
    model_short: str | None = None,
    report_root: Path | None = None,
    controls: list | None = None,
) -> UiRunResult:
    """
    跑一次平台 UI 执行任务。

    全程不向标准输出写任何内容：结果通过返回值交给调用方。

    Args:
        task: 自然语言任务描述。
        model_short: 模型短名；不传则用平台角色的默认值。
        report_root: 报告根目录；不传则用配置里的平台报告根。
        controls: 额外的中间件（重试 / 预算 / 取消）；不传则只挂观测。

    Returns:
        本次运行的产物路径与用量汇总。

    Raises:
        ValueError: 模型短名不存在或密钥没配。
        FileNotFoundError: 提示词文件不存在。
        OSError: 报告目录无法创建或写入。
    """
    session = await open_session("", model_short=model_short, controls=controls)
    return await session.run_turn(task, report_root=report_root)


if __name__ == "__main__":
    import asyncio

    result = asyncio.run(run_ui_task("只回复 OK 两个字母，不要调用任何工具。"))
    print(result.report_path)  # noqa: T201 - 模块自测入口
