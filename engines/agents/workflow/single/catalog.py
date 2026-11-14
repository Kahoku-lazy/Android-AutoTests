"""
文件名: ➡️ catalog.py 🏁
路径: ➡️ engines/agents/workflow/single/catalog.py 🏁
模块功能：➡️ 单智能体编排清单：稳定键、显示名与一句说明 🏁
Python 调试：➡️ python -m engines.agents.workflow.single.catalog 🏁
时间：➡️ 2026-11-11 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. SingleAgentCard: 一张可被页面读取的编排卡片。
2. list_single_agents / get_single_agent: 列清单与按键取值。
🏁
关联模块：➡️
1. 无本地依赖：本模块只放清单数据。
🏁
测试：➡️
1. tests/engines/agents/unit/test_single_agent_workflow.py: 清单当前为空，未知键报错
🏁
"""

from __future__ import annotations

from dataclasses import dataclass

__all__ = ["SingleAgentCard", "get_single_agent", "list_single_agents"]


@dataclass(frozen=True)
class SingleAgentCard:
    """
    一张单智能体编排卡片。

    Attributes:
        key: 稳定键，接口与页面用它选择编排。
        name: 显示名。
        summary: 一句说明。
        released_at: 上线日期（YYYY-MM-DD），供页面判断新旧；不是运行时生成。
    """

    key: str
    name: str
    summary: str
    released_at: str


_CARDS: tuple[SingleAgentCard, ...] = ()
"""当前无引擎侧编排卡片：平台对话角色已迁到 engines/backend_bridge。

保留本清单与 `get_single_agent` 的校验：将来要再暴露一张引擎侧编排，
在 `_CARDS` 里加一条即可，接口与页面无需改动。
"""


def list_single_agents() -> tuple[SingleAgentCard, ...]:
    """
    返回全部单智能体编排。

    Returns:
        卡片元组。当前为空——平台对话角色在 `engines/backend_bridge`。
    """
    return _CARDS


def get_single_agent(key: str) -> SingleAgentCard:
    """
    按稳定键取一张卡片。

    Args:
        key: 编排键；未登记的键一律报错。

    Returns:
        对应卡片。

    Raises:
        KeyError: 键不存在。消息列出可选键。
    """
    for card in _CARDS:
        if card.key == key:
            return card
    known = ", ".join(card.key for card in _CARDS) or "无"
    raise KeyError(f"未知单智能体编排 {key!r}；可选：{known}")
