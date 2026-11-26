from __future__ import annotations

import json

from pathlib import Path
from typing import Any

from agentscope.event import AgentEvent
from agentscope.message import Msg
from pydantic import TypeAdapter

from .raw import save_media

__all__ = ["AlignedRun"]

_ADAPTER = TypeAdapter(AgentEvent)
_SCHEMA = "agentscope.run/1"


class AlignedRun:
    def __init__(
        self,
        path: Path,
        *,
        media_dir: Path | None = None,
        include_events: bool = True,
    ) -> None:
        self.path = path
        self.media_dir = media_dir if media_dir is not None else path.parent / f"{path.stem}.media"
        self.include_events = bool(include_events)
        self._run: dict = {}
        self._inputs: dict = {}
        self._observations: list = []
        self._events: list = []
        self._steps: list = []
        self._step_replies: dict[int, list[str]] = {}
        self.document: dict = {}

    def begin(self, run: dict, inputs: dict | None = None) -> None:
        self._run = dict(run)
        self._inputs = dict(inputs or {})

    def bind_step_reply(self, index: int, reply_id: str) -> None:
        clean = str(reply_id or "")
        if not clean:
            return
        bucket = self._step_replies.setdefault(int(index), [])
        if clean not in bucket:
            bucket.append(clean)

    def set_steps(self, steps: list[dict]) -> None:
        self._steps = [dict(item) for item in steps]
        for item in self._steps:
            for reply_id in item.get("reply_ids") or []:
                self.bind_step_reply(int(item.get("index") or 0), reply_id)
        for item in self._steps:
            index = int(item.get("index") or 0)
            item["reply_ids"] = list(self._step_replies.get(index, item.get("reply_ids") or []))

    def feed(self, event: object) -> None:
        dump = event.model_dump(mode="python")
        kept = save_media(dump, self.media_dir, as_url=True)
        self._events.append(_ADAPTER.validate_python(kept))

    def observe(self, record: Any) -> None:
        payload = record.as_dict() if hasattr(record, "as_dict") else dict(record)
        self._observations.append(payload)

    def end(self, summary: dict | None = None) -> Path:
        payload = {
            "schema": _SCHEMA,
            "run": self._run,
            "input": self._inputs,
            "replies": self._replies(),
            "observations": self._observations,
            "summary": dict(summary or {}),
            "event_count": len(self._events),
            "events": (
                [item.model_dump(mode="python") for item in self._events]
                if self.include_events
                else []
            ),
        }
        if self._steps:
            payload["steps"] = list(self._steps)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
        )
        self.document = payload
        return self.path

    def _replies(self) -> list[dict]:
        grouped: dict[str, list] = {}
        unbound = 0
        for event in self._events:
            reply_id = str(getattr(event, "reply_id", "") or "")
            if not reply_id:
                unbound += 1
                continue
            grouped.setdefault(reply_id, []).append(event)
        rows = []
        for reply_id, events in grouped.items():
            name = str(getattr(events[0], "name", "") or self._run.get("agent") or "")
            msg = Msg(name=name, role="assistant", content=[])
            msg.id = reply_id
            unfolded: list[str] = []
            for event in events:
                try:
                    msg.append_event(event)
                except Exception:  # noqa: BLE001 - 单条折叠失败不该毁掉整份记录
                    unfolded.append(type(event).__name__)
            row = {
                "reply_id": reply_id,
                "agent": name,
                "unfolded": unfolded,
                "msg": msg.model_dump(mode="python"),
            }
            role = self._roles().get(name, "")
            if role:
                row["role"] = role
            rows.append(row)
        if unbound:
            rows.append({"reply_id": "", "agent": "", "unfolded": [], "detached": unbound})
        return rows

    def _roles(self) -> dict[str, str]:
        return {
            str(item.get("name") or ""): str(item.get("role") or "")
            for item in self._run.get("roles") or []
            if isinstance(item, dict)
        }
