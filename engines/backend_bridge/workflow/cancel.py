"""
文件名: ➡️ cancel.py 🏁
路径: ➡️ engines/backend_bridge/workflow/cancel.py 🏁
模块功能：➡️ 平台运行取消：按任务号登记取消令牌，供后端在半途置位 🏁
Python 调试：➡️ python -m engines.backend_bridge.workflow.cancel 🏁
时间：➡️ 2026-11-15 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-15 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. bind_cancel: 为一次任务登记取消令牌，返回可共享的令牌。
2. request_cancel: 从别的线程置位取消；令牌不存在时返回 False。
3. clear_cancel: 运行结束后清掉登记，避免下次运行误取消。
4. cancel_controls: 把令牌包成中间件，交给一次运行的 controls。
🏁
关联模块：➡️
1. engines.ae_harness.middleware.control: 导入 CancelToken / CancelMiddleware，取消判定只用现成实现。
2. engines.backend_bridge.workflow.bound_sop: 调用方，把 controls 交给 run_sop。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_sop_cancel.py: 登记、置位、清理与中间件装配
🏁
"""

from __future__ import annotations

from engines.ae_harness.middleware.control import CancelMiddleware, CancelToken

__all__ = [
    "bind_cancel",
    "cancel_controls",
    "clear_cancel",
    "request_cancel",
]

# 任务号 → 取消令牌。取值/写入/删除都是单条字典操作，在 GIL 下原子，
# 不需要额外加锁；真正的跨线程同步由 CancelToken 内部的 Event 负责。
_TOKENS: dict[int, CancelToken] = {}


def bind_cancel(task_id: int, *, reason: str = "用户取消") -> CancelToken:
    """
    为一次任务登记取消令牌。

    Args:
        task_id: 平台任务 id；0 表示不登记，返回一个游离令牌。
        reason: 该令牌被取消时写进异常消息的原因。

    Returns:
        与任务号绑定的取消令牌；同一任务重复登记会复用同一个令牌。
    """
    if not task_id:
        return CancelToken(reason=reason)
    key = int(task_id)
    existing = _TOKENS.get(key)
    if existing is not None:
        return existing
    token = CancelToken(reason=reason)
    _TOKENS[key] = token
    return token


def request_cancel(task_id: int, reason: str = "用户取消") -> bool:
    """
    置位某个任务的取消令牌。

    Args:
        task_id: 平台任务 id。
        reason: 取消原因，写进异常消息。

    Returns:
        找到并置位返回 True；该任务没有在跑则返回 False。
    """
    token = _TOKENS.get(int(task_id or 0))
    if token is None:
        return False
    token.cancel(reason)
    return True


def clear_cancel(task_id: int) -> None:
    """
    清掉某个任务的取消登记。

    Args:
        task_id: 平台任务 id。
    """
    _TOKENS.pop(int(task_id or 0), None)


def cancel_controls(task_id: int) -> list:
    """
    把该任务的取消令牌包成中间件。

    Args:
        task_id: 平台任务 id；没有登记时返回空列表。

    Returns:
        中间件列表，可直接并入一次运行的 `controls`。
    """
    token = _TOKENS.get(int(task_id or 0))
    return [CancelMiddleware(token)] if token is not None else []
