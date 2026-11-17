"""
文件名: ➡️ thread_run.py 🏁
路径: ➡️ engines/backend_bridge/agents/thread_run.py 🏁
模块功能：➡️ 按对话栏复用一个角色实例，并按栏登记取消 🏁
Python 调试：➡️ python -m engines.backend_bridge.agents.thread_run 🏁
时间：➡️ 2026-11-16 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-16 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. thread_agent: 同一栏首次取时创建，之后复用。
2. request_thread_cancel: 只取消指定栏。
3. 不读库，不打印。
🏁
关联模块：➡️
1. engines.backend_bridge.agents.card_agent: 导入 build_card_agent。
2. engines.ae_harness.middleware.control: 导入 CancelToken。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_assistant_thread.py: 同栏复用、新栏不复用
🏁
"""

from __future__ import annotations

from engines.ae_harness.middleware.control import CancelMiddleware, CancelToken
from engines.backend_bridge.agents.card_agent import build_card_agent

__all__ = [
    "drop_thread",
    "request_thread_cancel",
    "thread_agent",
    "thread_cancel_token",
]

_AGENTS: dict[str, object] = {}
_CANCELS: dict[str, CancelToken] = {}


async def thread_agent(thread_id: str, snapshot: dict) -> object:
    """
    取该对话栏的角色。没有则按 snapshot 创建。

    Args:
        thread_id: 对话栏编号。
        snapshot: 首次发送时的连接参数、提示词与工具勾选。

    Returns:
        该栏的同一个角色实例。

    Raises:
        ValueError: 栏编号为空，或 snapshot 缺连接参数。
    """
    key = thread_id.strip()
    if not key:
        raise ValueError("thread_id 不能为空")
    current = _AGENTS.get(key)
    if current is not None:
        return current
    bundle = await build_card_agent(
        name=str(snapshot.get("name") or "assistant"),
        provider=str(snapshot["provider"]),
        api_key_env=str(snapshot["api_key_env"]),
        model_name=str(snapshot["model_name"]),
        base_url=str(snapshot.get("base_url") or ""),
        system_prompt=str(snapshot.get("system_prompt") or ""),
        tools=list(snapshot.get("tools") or []),
        observers=[CancelMiddleware(thread_cancel_token(key))],
    )
    _AGENTS[key] = bundle.agent
    return bundle.agent


def thread_cancel_token(thread_id: str) -> CancelToken:
    """
    取该栏的取消令牌，没有则新建。

    Args:
        thread_id: 对话栏编号。

    Returns:
        该栏专用的取消令牌。
    """
    key = thread_id.strip()
    token = _CANCELS.get(key)
    if token is None:
        token = CancelToken(reason="用户取消")
        _CANCELS[key] = token
    return token


def request_thread_cancel(thread_id: str) -> bool:
    """
    置位该栏的取消令牌。

    Args:
        thread_id: 对话栏编号。

    Returns:
        找到并置位返回 True；该栏没有令牌则 False。
    """
    token = _CANCELS.get(thread_id.strip())
    if token is None:
        return False
    token.cancel("用户取消")
    return True


def drop_thread(thread_id: str) -> None:
    """
    丢掉该栏的内存实例与取消令牌。

    Args:
        thread_id: 对话栏编号。
    """
    key = thread_id.strip()
    _AGENTS.pop(key, None)
    _CANCELS.pop(key, None)
