"""
文件名: ➡️ platform_agents.py 🏁
路径: ➡️ backend/apps/ai_assistant/platform_agents.py 🏁
模块功能：➡️ 把平台智能体接进 AI 助手对话：卡片清单与一轮对话 🏁
Python 调试：➡️ python -m backend.apps.ai_assistant.platform_agents 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. PLATFORM_CARDS: 平台侧对话卡片，与引擎侧单智能体清单合并后一起展示。
2. is_platform_key: 判断某个编排键是否属于平台侧。
3. stream_turn: 跑一轮平台对话，把 token 用量写进账本，返回本轮文本。
🏁
关联模块：➡️
1. engines.backend_bridge.session: 导入 session_for，按连接复用平台角色。
2. backend.apps.usage_ledger.api: 导入 record_run_usages，用量写既有账本。
🏁
测试：➡️
1. tests/ai_assistant/unit/test_platform_agents.py: 卡片、键判定、入账调用
🏁
"""

from __future__ import annotations

import asyncio

from dataclasses import dataclass

from backend.apps.usage_ledger.api import record_run_usages

__all__ = ["PlatformCard", "is_platform_key", "list_cards", "stream_turn"]

# 平台侧对话卡片的稳定键；不能与引擎侧单智能体清单的键重名。
PLATFORM_KEY = "platform_ui"


@dataclass(frozen=True)
class PlatformCard:
    """
    一张平台侧对话卡片。

    Attributes:
        key: 稳定键，前端用它选择编排。
        name: 显示名。
        summary: 一句说明。
        released_at: 上线日期（YYYY-MM-DD），供页面判断新旧。
    """

    key: str
    name: str
    summary: str
    released_at: str


_CARDS = (
    PlatformCard(
        key=PLATFORM_KEY,
        name="UI 执行（平台）",
        summary="平台侧执行角色：看页面并操作设备，每次运行留存 HTML 报告与 token 账。",
        released_at="2026-11-14",
    ),
)


def list_cards() -> list[dict]:
    """
    返回平台侧卡片（已转成接口需要的字段）。

    Returns:
        含 key / name / summary / released_at 的字典列表。
    """
    return [
        {
            "key": card.key,
            "name": card.name,
            "summary": card.summary,
            "released_at": card.released_at,
        }
        for card in _CARDS
    ]


def is_platform_key(key: str) -> bool:
    """
    判断编排键是否属于平台侧。

    Args:
        key: 编排键。

    Returns:
        属于平台侧返回 True。
    """
    return any(card.key == key for card in _CARDS)


def stream_turn(*, key: str, serial: str, message: str, session_id: str) -> str:
    """
    跑一轮平台对话，并把这一轮的用量写进账本。

    入账失败不阻断对话：账本不是对话的前置条件。

    Args:
        key: 编排键，必须是平台侧键。
        serial: 当前设备序列号。
        message: 用户这一轮说的话。
        session_id: 前端本次对话的连接键。

    Returns:
        本轮回复文本。

    Raises:
        ValueError: 编排键不属于平台侧，或连接键为空。
    """
    from engines.backend_bridge.session import session_for

    if not is_platform_key(key):
        raise ValueError(f"不是平台编排键：{key}")

    async def run() -> tuple[str, list[dict], str, str]:
        session = await session_for(session_id, serial)
        result = await session.run_turn(message)
        return result.final_text, result.usages, result.model, str(result.report_path.parent.name)

    text, usages, model, execution_id = asyncio.run(run())
    record_run_usages(usages, execution_id=execution_id, model=model)
    return text
