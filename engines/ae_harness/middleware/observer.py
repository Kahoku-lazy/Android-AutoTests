"""
文件名: ➡️ observer.py 🏁
路径: ➡️ engines/ae_harness/middleware/observer.py 🏁
模块功能：➡️ 只读观测中间件：采样本轮最终 system prompt 与上下文压缩决策 🏁
Python 调试：➡️ python -m engines.ae_harness.middleware.observer 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. ObservationRecord: 一条观测记录——类型、绝对时刻、载荷。
2. ObservationMiddleware: 实现 on_system_prompt 与 on_compress_context 两个只读 hook。
3. 投递方式：注入了 emit 回调就交给它，否则写进自有 records 列表；本模块不认识事件层。
4. 只读承诺：变换式 hook 原样返回，Onion 型 hook 必调下游，不实现 list_tools。
🏁
关联模块：➡️
1. 无本地依赖：只依赖 agentscope.middleware 与标准库，不导入同包任何模块。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_observer.py: 透传一致、压缩两态、无 list_tools、两条投递路径
🏁
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from time import perf_counter
from typing import Any

from agentscope.middleware import MiddlewareBase

__all__ = [
    "KIND_COMPRESS",
    "KIND_SYSTEM_PROMPT",
    "ObservationMiddleware",
    "ObservationRecord",
]

KIND_COMPRESS = "compress_context"
KIND_SYSTEM_PROMPT = "system_prompt"

# 压缩指令只做防爆截断：它是提示词片段，不是判定依据。
_INSTRUCTION_LIMIT = 500
_STAMP_FORMAT = "%Y-%m-%d_%H-%M-%S.%f"


def _stamp() -> str:
    """
    取当前绝对时刻。

    Returns:
        `YYYY-MM-DD_HH-MM-SS.mmm` 形式的时间戳。
    """
    return datetime.now().strftime(_STAMP_FORMAT)[:-3]


def _agent_name(agent: object) -> str:
    """
    取智能体名称，用作观测记录的归属。

    Args:
        agent: 智能体实例。

    Returns:
        智能体名称；取不到时为空串。
    """
    return str(getattr(agent, "name", "") or "")


def _context_len(agent: object) -> int | None:
    """
    读智能体上下文的消息条数。

    取不到时返回 None 而不是抛错：本模块只观测，不能因结构变化打断运行。

    Args:
        agent: 智能体实例。

    Returns:
        消息条数；结构不符时为 None。
    """
    context = getattr(getattr(agent, "state", None), "context", None)
    try:
        return len(context)  # type: ignore[arg-type]
    except TypeError:
        return None


def _hint_text(instructions: object) -> str:
    """
    把压缩指令取成文本。

    Args:
        instructions: HintBlock 或 None。

    Returns:
        指令正文；超过上限时截断并标注总长，未传入时为空串。
    """
    hint = getattr(instructions, "hint", None)
    if hint is None:
        return ""
    if isinstance(hint, str):
        text = hint
    elif isinstance(hint, list):
        text = "".join(str(getattr(block, "text", "") or "") for block in hint)
    else:
        text = str(hint)
    text = text.strip()
    if len(text) > _INSTRUCTION_LIMIT:
        return f"{text[:_INSTRUCTION_LIMIT]}…（共 {len(text)} 字符）"
    return text


@dataclass
class ObservationRecord:
    """
    一条观测记录。

    Attributes:
        kind: 观测类型：`compress_context` 或 `system_prompt`。
        at: 发生时刻。
        payload: 该类型的载荷，键随类型不同。
    """

    kind: str
    at: str
    payload: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, object]:
        """
        转成可直接落盘的字典。

        Returns:
            类型、时刻与载荷拍平后的映射。
        """
        return {"kind": self.kind, "at": self.at, **self.payload}


class ObservationMiddleware(MiddlewareBase):
    """
    只读观测中间件：只在 hook 上采样，不改变任何行为。

    准入边界见 `/.agents/docs/engines/ae_harness_agents/ae_harness_agents_agent_creation.md` 的「观测中间件准入清单」。

    Attributes:
        records: 未注入回调时存放观测记录；注入回调时保持为空。
    """

    def __init__(self, emit: Callable[[ObservationRecord], None] | None = None) -> None:
        """
        确定记录投递方式：注入回调则交给回调，否则进自有容器。

        Args:
            emit: 记录投递回调；不传则写入自有 `records`。
        """
        self._emit = emit
        self.records: list[ObservationRecord] = []

    def _record(self, record: ObservationRecord) -> None:
        """
        投递一条记录。

        Args:
            record: 待投递的记录。

        Returns:
            无。
        """
        if self._emit is not None:
            self._emit(record)
            return
        self.records.append(record)

    async def on_system_prompt(self, agent: object, current_prompt: str) -> str:
        """
        记录本轮最终 system prompt 全文，并原样返回。

        框架以 `await` 调用本 hook，因此必须是异步方法。

        Args:
            agent: 组装提示词的智能体。
            current_prompt: 组装完成的 system prompt。

        Returns:
            与入参逐字符相同的提示词；本 hook 是变换式，返回值会被采用。
        """
        text = str(current_prompt or "")
        self._record(
            ObservationRecord(
                kind=KIND_SYSTEM_PROMPT,
                at=_stamp(),
                payload={
                    "agent": _agent_name(agent),
                    "length": len(text),
                    "text": text,
                },
            )
        )
        return current_prompt

    async def on_compress_context(
        self,
        agent: object,
        input_kwargs: dict,
        next_handler: Callable[..., Any],
    ) -> None:
        """
        记录一次上下文压缩的决策与结果，不改变压缩本身。

        阈值与窗口只读配置，不额外调用模型数 token：那会产生额外开销，
        也可能触发网络请求，超出只读观测的边界。

        Args:
            agent: 正在压缩上下文的智能体。
            input_kwargs: 含 `context_config` 与 `instructions`。
            next_handler: 下一层处理；必须且只调用一次。

        Returns:
            无。
        """
        begin = perf_counter()
        config = input_kwargs.get("context_config") or getattr(agent, "context_config", None)
        instructions = input_kwargs.get("instructions")
        before = _context_len(agent)
        ratio = getattr(config, "trigger_ratio", None)
        window = getattr(getattr(agent, "model", None), "context_size", None)
        threshold = ratio * window if (ratio is not None and window) else None

        await next_handler(**input_kwargs)

        after = _context_len(agent)
        compressed = None if (before is None or after is None) else after < before
        self._record(
            ObservationRecord(
                kind=KIND_COMPRESS,
                at=_stamp(),
                payload={
                    "agent": _agent_name(agent),
                    "messages_before": before,
                    "messages_after": after,
                    "compressed": compressed,
                    "trigger_ratio": ratio,
                    "context_size": window,
                    "threshold": threshold,
                    "instructions": _hint_text(instructions),
                    "cost_ms": round((perf_counter() - begin) * 1000, 1),
                },
            )
        )


if __name__ == "__main__":
    import asyncio

    observer = ObservationMiddleware()
    asyncio.run(observer.on_system_prompt(None, "你是执行者。"))
    print(observer.records[0].as_dict())  # noqa: T201 - 模块自测入口
