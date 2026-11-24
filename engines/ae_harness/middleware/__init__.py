"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/ae_harness/middleware/__init__.py 🏁
模块功能：➡️ 中间件门面：只读观测、模型调用重试、运行控制 🏁
Python 调试：➡️ python -m engines.ae_harness.middleware 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 2.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 只读观测：ObservationMiddleware / ObservationRecord，采样事件流看不到的信息。
2. 可靠性：ModelRetryMiddleware，失败重试同一动作，流式只在首块之前重试。
3. 运行控制：RunBudget / CancelToken 与两个中间件，只做提前中止。
🏁
关联模块：➡️
1. engines.ae_harness.middleware.observer: 只读观测实现。
2. engines.ae_harness.middleware.retry: 重试实现。
3. engines.ae_harness.middleware.control: 预算与取消实现。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

from .control import (
    BudgetExceeded,
    BudgetMiddleware,
    CancelMiddleware,
    CancelToken,
    RunBudget,
    RunCancelled,
)
from .observer import KIND_COMPRESS, KIND_SYSTEM_PROMPT, ObservationMiddleware, ObservationRecord
from .retry import ModelRetryMiddleware, RetrySettings, is_transient_model_error

__all__ = [
    "KIND_COMPRESS",
    "KIND_SYSTEM_PROMPT",
    "BudgetExceeded",
    "BudgetMiddleware",
    "CancelMiddleware",
    "CancelToken",
    "ModelRetryMiddleware",
    "ObservationMiddleware",
    "ObservationRecord",
    "RetrySettings",
    "RunBudget",
    "RunCancelled",
    "is_transient_model_error",
]
