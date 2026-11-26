from __future__ import annotations

import time

from pathlib import Path

from engines.ae_harness.agents.messages import user_message
from engines.ae_harness.event import (
    AgentEventRecorder,
    AlignedReportRenderer,
    AlignedRun,
    RawEventDump,
    summarize,
)
from engines.ae_harness.tools.adb.core import lock_serial, unlock_serial
from engines.backend_bridge import event_log
from engines.backend_bridge.agents import UI_EXECUTOR_ROLE, build_ui_executor
from engines.backend_bridge.agents.run_params import apply_run_params
from engines.backend_bridge.device_guard import require_online
from engines.backend_bridge.reports import REPORT_ROOT
from engines.backend_bridge.result import UiRunResult

__all__ = ["UiExecutorSession", "open_session", "require_online", "session_for"]

_SERIAL_PREFIX = "当前设备序列号："
_SERIAL_HINT = "设备已由平台指定并锁定：所有设备动作直接使用该序列号，不需要枚举或切换设备。"
_SHOT_HINT = (
    "截图复用规则：点击后截一张图确认结果即可；若下一步仍在同一画面，"
    "直接以这张图定位，不要重复截图；画面可能变化（动画、弹窗、跳转）时必须重新截图。"
)
_READY_HINT = (
    "启动就绪规则：启动应用时把 with_screen 设为 true，工具会在应用就绪后把首屏一起返回；"
    "返回 ready=true 时不要再连拍截图等加载，直接按这张图定位；"
    "ready=false 或 timed_out=true 时才连拍截图等加载。"
)
_SESSIONS: dict[str, "UiExecutorSession"] = {}


class UiExecutorSession:
    def __init__(
        self,
        serial: str,
        bundle: object,
        observer: object,
        *,
        session_id: str = "",
        system_prompt: str = "",
    ) -> None:
        self.serial = serial
        self.session_id = session_id
        self.system_prompt = system_prompt
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
        prompt = (
            message
            if not self.serial
            else (
                f"{_SERIAL_PREFIX}{self.serial}\n{_SERIAL_HINT}\n"
                f"{_SHOT_HINT}\n{_READY_HINT}\n{message}"
            )
        )
        model = str(getattr(getattr(agent, "model", None), "model", "") or "")
        raw = RawEventDump(recorder.log_path.with_name(f"{recorder.log_path.stem}.raw.jsonl"))
        raw.begin(
            {
                "role": role,
                "agent": str(getattr(agent, "name", "") or ""),
                "serial": self.serial,
                "model": model,
                "api_key_env": self.api_key_env,
                "tool_schemas": list(schemas.values()),
                "input": prompt,
            }
        )
        aligned = AlignedRun(recorder.log_path.with_name(f"{recorder.log_path.stem}.aligned.json"))
        aligned.begin(
            {
                "role": role,
                "agent": str(getattr(agent, "name", "") or ""),
                "model": model,
                "api_key_env": self.api_key_env,
                "serial": self.serial,
            },
            {
                "system_prompt": self.system_prompt,
                "tool_schemas": list(schemas.values()),
                "user_message": prompt,
            },
        )
        self._observer.attach(aligned.observe)

        event_log.mark(self.session_id, "开始", model)
        turn_log = event_log.TurnLogger()
        begin = time.perf_counter()
        token = lock_serial(self.serial)
        try:
            async for event in agent.reply_stream(user_message(prompt)):
                recorder.on_event(event)
                raw.feed(event)
                aligned.feed(event)
                line = turn_log.feed(event)
                if line:
                    event_log.log_event(line)
        finally:
            unlock_serial(token)
            event_log.mark(self.session_id, "结束", model)
        cost_s = round(time.perf_counter() - begin, 2)

        record = recorder.finish(cost_s)
        raw.end(
            {
                "cost_s": record.cost_s,
                "final_text": record.final_text,
                "summary": record.summary,
                "usages": [item.as_dict() for item in record.usages],
                "log_path": record.log_path.as_posix(),
                "html_path": record.html_path.as_posix(),
                "raw_path": raw.path.as_posix(),
            }
        )
        raw.close()
        aligned.end(
            {
                "cost_s": record.cost_s,
                "final_text": record.final_text,
                "tokens": record.summary.get("tokens", {}),
                "usages": [item.as_dict() for item in record.usages],
                "log_path": record.log_path.as_posix(),
                "html_path": record.html_path.as_posix(),
                "raw_path": raw.path.as_posix(),
                "aligned_path": aligned.path.as_posix(),
            }
        )
        AlignedReportRenderer().save(aligned.document, record.html_path)
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
    capture_messages: bool = False,
) -> UiExecutorSession:
    clean = require_online(serial)
    bundle, observer = await build_ui_executor(
        system_prompt=system_prompt,
        provider=provider,
        api_key_env=api_key_env,
        model_name=model_name,
        base_url=base_url,
        controls=controls,
        capture_messages=capture_messages,
    )
    apply_run_params(bundle.agent)
    return UiExecutorSession(
        clean, bundle, observer, session_id=session_id, system_prompt=system_prompt
    )


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
