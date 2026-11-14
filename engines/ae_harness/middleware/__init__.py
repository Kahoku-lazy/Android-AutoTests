"""
文件名: ➡️ __init__.py 🏁
路径: ➡️ engines/ae_harness/middleware/__init__.py 🏁
模块功能：➡️ 观测中间件包入口：只提供 hook 入口，采集事件流看不到的信息 🏁
Python 调试：➡️ python -m engines.ae_harness.middleware 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. ObservationMiddleware: 只读观测中间件，采样 on_compress_context 与 on_system_prompt。
2. ObservationRecord: 一条观测记录；投递方式由构造时是否注入 emit 回调决定。
3. 本包只做观测：不参与编排、不改模型、不改工具行为、不落盘、不渲染。
4. 准入边界见 engines/ae_harness/agents/AGENTS.md 的「观测中间件准入清单」。
5. 本包不导入同包其它模块，由事件层单向引用，避免观测链路出现环。
🏁
关联模块：➡️
1. 无本地依赖：只依赖 agentscope.middleware 与标准库。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_observer.py: 只读承诺与两条投递路径
🏁
"""

from __future__ import annotations

from .observer import (
    KIND_COMPRESS,
    KIND_SYSTEM_PROMPT,
    ObservationMiddleware,
    ObservationRecord,
)

__all__ = [
    "KIND_COMPRESS",
    "KIND_SYSTEM_PROMPT",
    "ObservationMiddleware",
    "ObservationRecord",
]
