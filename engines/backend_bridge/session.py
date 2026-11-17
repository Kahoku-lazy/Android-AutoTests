"""
文件名: ➡️ session.py 🏁
路径: ➡️ engines/backend_bridge/session.py 🏁
模块功能：➡️ 平台 UI 执行会话：同一对话连接复用一个角色，逐轮出报告 🏁
Python 调试：➡️ python -m engines.backend_bridge.session 🏁
时间：➡️ 2026-11-14 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-14 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. UiExecutorSession: 持有一个已装配角色与它的观测中间件，按轮运行并各自出一份报告。
2. open_session: 新建会话；session_for: 同一连接键复用同一个会话，换设备只改字段。
3. 设备序列号随每轮消息带上，不改工具的全局状态。
🏁
关联模块：➡️
1. engines.backend_bridge.agents: 导入 build_ui_executor，装配执行角色。
2. engines.backend_bridge.result: 导入 UiRunResult，一轮的结果形状。
3. engines.ae_harness.event: 导入记录器、渲染器与用量汇总。
🏁
测试：➡️
1. tests/engines/backend_bridge/unit/test_session.py: 复用、换设备、逐轮报告
🏁
"""

from __future__ import annotations

import time

from pathlib import Path

from agentscope.message import UserMsg

from engines.ae_harness.event import AgentEventRecorder, HtmlReportRenderer, summarize
from engines.backend_bridge import event_log
from engines.backend_bridge.agents import UI_EXECUTOR_ROLE, build_ui_executor
from engines.backend_bridge.reports import REPORT_ROOT
from engines.backend_bridge.result import UiRunResult

__all__ = ["UiExecutorSession", "open_session", "session_for"]

_SERIAL_PREFIX = "当前设备序列号："
_SESSIONS: dict[str, "UiExecutorSession"] = {}


class UiExecutorSession:
    """
    一次平台对话连接上的执行角色。

    角色只装配一次，后续每轮复用同一个实例，因此对话上下文是连续的；
    每轮单独出一份 JSONL 与 HTML 报告，报告目录按轮次时间戳区分。
    """

    def __init__(
        self, serial: str, bundle: object, observer: object, *, session_id: str = ""
    ) -> None:
        """
        记录设备与已装配的角色。

        Args:
            serial: 当前设备序列号；换设备只改这个字段，不重建角色。
            bundle: `build_ui_executor` 返回的角色 bundle。
            observer: 与角色配套的观测中间件。
            session_id: 前端本次对话的连接键。
        """
        self.serial = serial
        self.session_id = session_id
        self._bundle = bundle
        self._observer = observer

    @property
    def api_key_env(self) -> str:
        """
        当前角色使用的密钥环境变量名。

        Returns:
            密钥环境变量名；取不到时为空串。
        """
        return str(getattr(self._bundle, "api_key_env", "") or "")

    def set_serial(self, serial: str) -> None:
        """
        切换本会话使用的设备。

        Args:
            serial: 新的设备序列号。
        """
        self.serial = serial.strip()

    async def run_turn(self, message: str, *, report_root: Path | None = None) -> UiRunResult:
        """
        跑一轮对话并产出一份报告。

        Args:
            message: 用户这一轮说的话。
            report_root: 报告根目录；不传则用 `REPORT_ROOT`。

        Returns:
            本轮的结果（最终文本、产物路径、用量）。

        Raises:
            OSError: 报告目录无法创建或写入。
        """
        role = UI_EXECUTOR_ROLE.role_key
        root = report_root if report_root is not None else REPORT_ROOT
        agent = self._bundle.agent

        recorder = AgentEventRecorder(
            root,
            role,
            api_key_env=self.api_key_env,
            observations=self._observer.records,
        )
        schemas = {
            item["function"]["name"]: item["function"]
            for item in await agent.toolkit.get_tool_schemas()
        }
        recorder.begin(message, schemas=schemas)

        prompt = message if not self.serial else f"{_SERIAL_PREFIX}{self.serial}\n{message}"
        model = str(getattr(getattr(agent, "model", None), "model", "") or "")
        event_log.mark(self.session_id, "开始", model)
        turn_log = event_log.TurnLogger()
        begin = time.perf_counter()
        try:
            async for event in agent.reply_stream(UserMsg(name="user", content=prompt)):
                recorder.on_event(event)
                line = turn_log.feed(event)
                if line:
                    event_log.log_event(line)
        finally:
            event_log.mark(self.session_id, "结束", model)
        cost_s = round(time.perf_counter() - begin, 2)

        record = recorder.finish(cost_s)
        HtmlReportRenderer().save(record)
        totals = summarize(record.usages)
        summary = totals.as_dict()
        return UiRunResult(
            final_text=record.final_text,
            report_path=record.html_path,
            log_path=record.log_path,
            model=str(getattr(getattr(agent, "model", None), "model", "") or ""),
            tokens={
                "input": summary["input"],
                "output": summary["output"],
                "cache_hit": summary["cache_hit"],
                "cache_creation": summary["cache_creation"],
            },
            by_api_key_env=dict(totals.by_api_key_env),
            usages=[item.as_dict() for item in record.usages],
            cost_s=cost_s,
        )


async def open_session(
    serial: str,
    *,
    system_prompt: str,
    provider: str,
    api_key_env: str,
    model_name: str,
    base_url: str = "",
    session_id: str = "",
    controls: list | None = None,
) -> UiExecutorSession:
    """
    新建一个平台执行会话。

    Args:
        serial: 当前设备序列号；可为空，表示沿用工具默认设备。
        system_prompt: 系统提示词正文，由平台运营配置传入。
        provider: 厂商名，由平台运营配置传入。
        api_key_env: 密钥环境变量名，由平台运营配置传入。
        model_name: 正式模型名，由平台运营配置传入。
        base_url: 基础地址；空串时用厂商默认。
        session_id: 前端本次对话的连接键。
        controls: 额外的中间件（重试 / 预算 / 取消）；不传则只挂观测。

    Returns:
        已装配好角色的会话。

    Raises:
        ValueError: 厂商与密钥名不匹配，密钥没配，或系统提示词为空。
    """
    bundle, observer = await build_ui_executor(
        system_prompt=system_prompt,
        provider=provider,
        api_key_env=api_key_env,
        model_name=model_name,
        base_url=base_url,
        controls=controls,
    )
    return UiExecutorSession(serial.strip(), bundle, observer, session_id=session_id)


async def session_for(
    session_id: str,
    serial: str,
    *,
    system_prompt: str,
    provider: str,
    api_key_env: str,
    model_name: str,
    base_url: str = "",
    controls: list | None = None,
) -> UiExecutorSession:
    """
    按连接键取会话。没有则创建；已有则只更新设备。

    Args:
        session_id: 前端本次对话的连接键。
        serial: 当前设备序列号。
        system_prompt: 系统提示词正文；仅在新建时生效。
        provider: 厂商名；仅在新建时生效。
        api_key_env: 密钥环境变量名；仅在新建时生效。
        model_name: 正式模型名；仅在新建时生效。
        base_url: 基础地址；仅在新建时生效。

    Returns:
        该连接上的同一个会话。

    Raises:
        ValueError: 连接键为空，或新建时系统提示词为空。
    """
    key = session_id.strip()
    if not key:
        raise ValueError("session_id 不能为空")
    current = _SESSIONS.get(key)
    if current is None:
        current = await open_session(
            serial,
            system_prompt=system_prompt,
            provider=provider,
            api_key_env=api_key_env,
            model_name=model_name,
            base_url=base_url,
            session_id=key,
            controls=controls,
        )
        _SESSIONS[key] = current
        return current
    current.set_serial(serial)
    return current


def drop_session(session_id: str) -> None:
    """
    丢弃一个会话（测试与显式重置用）。

    Args:
        session_id: 连接键。
    """
    _SESSIONS.pop(session_id.strip(), None)
