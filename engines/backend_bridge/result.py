"""
文件名: ➡️ result.py 🏁
路径: ➡️ engines/backend_bridge/result.py 🏁
模块功能：➡️ 平台一次运行的产物与用量结果对象 🏁
Python 调试：➡️ python -m engines.backend_bridge.result 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. UiRunResult: 一次运行的最终文本、报告与日志路径、模型名与四类 token 合计。
2. 单独成模块：会话层与运行入口都要用它，放在任一方的模块里都会形成循环导入。
🏁
关联模块：➡️
1. 无本地依赖：只依赖标准库 dataclasses 与 pathlib。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

__all__ = ["UiRunResult"]


@dataclass(frozen=True)
class UiRunResult:
    """
    一次平台运行的产物与用量。

    调用方拿到它就能取报告、取日志、写账；不需要认识事件记录对象。

    Attributes:
        final_text: 智能体最后一条回复的正文。
        report_path: 本次运行的 HTML 报告路径。
        log_path: 本次运行的 JSONL 事件日志路径。
        model: 本次运行实际调用的模型名，入账时用作模型标识。
        tokens: 四类 token 合计（input / output / cache_hit / cache_creation）。
        by_api_key_env: 密钥环境变量名到该组调用次数的映射。
        usages: 逐次调用的用量明细（每项是可直接序列化的字典）。
        cost_s: 本次运行的墙钟耗时秒数。
    """

    final_text: str
    report_path: Path
    log_path: Path
    model: str = ""
    tokens: dict = field(default_factory=dict)
    by_api_key_env: dict = field(default_factory=dict)
    usages: list = field(default_factory=list)
    cost_s: float = 0.0
