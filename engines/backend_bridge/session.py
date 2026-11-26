from __future__ import annotations

import time

from pathlib import Path

from engines.ae_harness.agents.messages import user_message
from engines.ae_harness.event import AgentEventRecorder, HtmlReportRenderer, summarize
from engines.backend_bridge import event_log
from engines.backend_bridge.agents import UI_EXECUTOR_ROLE, build_ui_executor
from engines.backend_bridge.reports import REPORT_ROOT
from engines.backend_bridge.result import UiRunResult

__all__ = ["UiExecutorSession", "open_session", "session_for"]

_SERIAL_PREFIX = "当前设备序列号："
_SESSIONS: dict[str, "UiExecutorSession"] = {}


class UiExecutorSession:
    def __init__(
        self, serial: str, bundle: object, observer: object, *, session_id: str = ""
    ) -> None:
        self.serial = serial
        self.session_id = session_id
        self._bundle = bundle
        self._observer = observer

    @property
    def api_key_env(self) -> str:
        return str(getattr(self._bundle, "api_key_env", "") or "")

    def set_serial(self, serial: str) -> None:
        self.serial = serial.strip()

    async def run_turn(self, message: str, *, report_root: Path | None = None) -> UiRunResult:
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
            async for event in agent.reply_stream(user_message(prompt)):
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
    _SESSIONS.pop(session_id.strip(), None)
