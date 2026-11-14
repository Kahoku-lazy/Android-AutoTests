"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/ae_harness/event/__init__.py 🏁
模块功能：➡️ 运行观测门面：记录器、报告渲染器与用量记录 🏁
Python 调试：➡️ python -m engines.ae_harness.event 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. AgentEventRecorder: 订阅 reply_stream，产出一轮记录并落 JSONL。
2. HtmlReportRenderer: 把记录渲染成自包含 HTML。
3. TokenUsage / UsageSummary / summarize: 一次模型调用一条的用量记录与汇总，供审计与后续上报。
🏁
关联模块：➡️
1. engines.ae_harness.event.record: 记录实现。
2. engines.ae_harness.event.render: 渲染实现。
3. engines.ae_harness.event.usage: 用量记录形状与汇总。
🏁
测试：➡️
1. tests/engines/ae_harness/test_usage.py: 用量记录形状与汇总口径
2. 见 engines.ae_harness.assistant.agent_executor
🏁
"""

from __future__ import annotations

from .record import AgentEventRecorder, RunRecord, StepRecord
from .render import HtmlReportRenderer
from .usage import TokenUsage, UsageSummary, summarize

__all__ = [
    "AgentEventRecorder",
    "HtmlReportRenderer",
    "RunRecord",
    "StepRecord",
    "TokenUsage",
    "UsageSummary",
    "summarize",
]
