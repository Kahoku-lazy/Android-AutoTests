from __future__ import annotations

import secrets

from pathlib import Path
from zoneinfo import ZoneInfo

from django.conf import settings
from django.utils import timezone

from backend.apps.ai_assistant.models import (
    AIAssistant,
    AIAssistantMessage,
    AIAssistantThread,
    AIRole,
)
from backend.apps.ai_assistant.services.assistant_cards import AssistantRoleMissingError

__all__ = [
    "AssistantRoleMissingError",
    "cancel_thread",
    "create_thread",
    "delete_thread",
    "get_thread",
    "is_safe_report_id",
    "list_messages",
    "list_threads",
    "mark_interrupted_running",
    "message_rows",
    "queue_turn",
    "rename_thread",
    "send_message",
]


def _local_iso(value) -> str:
    if value is None:
        return ""
    zone = ZoneInfo(settings.TIME_ZONE)
    if timezone.is_naive(value):
        value = value.replace(tzinfo=zone)
    return value.astimezone(zone).isoformat()


def new_thread_fields(assistant_id: str) -> dict:
    return {
        "thread_id": secrets.token_hex(8),
        "assistant_id": assistant_id,
        "status": AIAssistantThread.STATUS_IDLE,
    }


def list_threads(assistant_id: str):
    return AIAssistantThread.objects.filter(assistant_id=assistant_id).order_by(
        "-created_at", "-id"
    )


def get_thread(thread_id: str) -> AIAssistantThread | None:
    return AIAssistantThread.objects.filter(thread_id=thread_id).first()


def thread_log_dir(assistant_id: str, thread_id: str):
    from engines.backend_bridge.reports import ASSISTANT_LOG_ROOT

    return ASSISTANT_LOG_ROOT / assistant_id / thread_id


def is_safe_report_id(report_id: str) -> bool:
    if not report_id:
        return False
    stamp = Path(report_id).name
    return bool(stamp) and stamp not in {".", ".."} and stamp == report_id


def resolve_thread_report(thread: AIAssistantThread, report_id: str):
    if not is_safe_report_id(report_id):
        return None
    stamp = Path(report_id).name
    root = thread_log_dir(thread.assistant_id, thread.thread_id).resolve()
    folder = (root / stamp).resolve()
    if root not in folder.parents:
        return None
    matches = list(folder.glob("*.html"))
    return matches[0] if matches else None


def list_thread_logs(thread: AIAssistantThread) -> list[dict]:
    rows = []
    writing = thread.status == AIAssistantThread.STATUS_RUNNING
    for message in thread.messages.filter(role=AIAssistantMessage.ROLE_ASSISTANT).order_by("id"):
        if not message.report_id:
            continue
        rows.append(
            {
                "report_id": message.report_id,
                "summary": message.content[:80],
                "created_at": _local_iso(message.created_at),
                "writing": False,
            }
        )
    if writing:
        rows.append({"report_id": "", "summary": "还在写", "created_at": "", "writing": True})
    return rows


def list_messages(thread: AIAssistantThread):
    return thread.messages.order_by("id")


def message_rows(thread: AIAssistantThread) -> list[dict]:
    return [
        {
            "role": item.role,
            "content": item.content,
            "created_at": _local_iso(item.created_at),
        }
        for item in list_messages(thread)
    ]


def _snapshot_for(card: AIAssistant) -> dict:
    if card.release_state != "published":
        raise AssistantRoleMissingError("助手尚未发布")
    role = AIRole.objects.select_related("model_config").filter(role_id=card.role_id).first()
    if role is None:
        raise AssistantRoleMissingError("Agent 配置不存在")
    config = role.model_config
    return {
        "name": role.name,
        "provider": config.provider,
        "api_key_env": config.api_key_env,
        "model_name": config.model_name,
        "base_url": config.base_url,
        "system_prompt": role.system_prompt,
        "tools": list(card.tools or []),
    }


def queue_turn(thread: AIAssistantThread) -> None:
    import sys
    import threading

    if getattr(settings, "TESTING", False) or "pytest" in sys.modules:
        return
    threading.Thread(
        target=_run_turn,
        args=(thread.thread_id,),
        daemon=True,
        name=f"assistant-{thread.thread_id}",
    ).start()


def _run_turn(thread_id: str) -> None:
    from django.db import close_old_connections

    from backend.apps.ai_assistant.services.agent_loop import run_in_loop
    from engines.ae_harness.middleware.control import RunCancelled

    close_old_connections()
    thread = get_thread(thread_id)
    if thread is None or thread.status != AIAssistantThread.STATUS_RUNNING:
        return
    user_text = (
        thread.messages.filter(role=AIAssistantMessage.ROLE_USER)
        .order_by("-id")
        .values_list("content", flat=True)
        .first()
        or ""
    )
    snapshot = thread.snapshot if isinstance(thread.snapshot, dict) else {}
    report_title = (thread.title or "").strip()
    if not report_title:
        report_title = (
            AIAssistant.objects.filter(assistant_id=thread.assistant_id)
            .values_list("display_name", flat=True)
            .first()
            or ""
        )
    try:
        reply, report_id, usages, model = run_in_loop(
            _turn(
                thread.thread_id,
                user_text,
                assistant_id=thread.assistant_id,
                snapshot=snapshot,
                report_title=report_title,
            )
        )
        _record_chat_usages(thread.thread_id, usages, model)
        finish_message(thread, reply, status=AIAssistantThread.STATUS_DONE, report_id=report_id)
    except RunCancelled:
        finish_message(thread, "已取消", status=AIAssistantThread.STATUS_CANCELLED)
    except Exception as exc:
        finish_message(thread, f"执行异常: {exc}", status=AIAssistantThread.STATUS_INTERRUPTED)
    finally:
        close_old_connections()


async def _turn(
    thread_id: str,
    user_text: str,
    *,
    assistant_id: str,
    snapshot: dict,
    report_title: str = "",
) -> tuple[str, str, list, str]:
    from engines.backend_bridge.agents.thread_run import thread_agent, thread_observer

    agent = await thread_agent(thread_id, snapshot)
    return await _reply(
        agent,
        user_text,
        assistant_id=assistant_id,
        thread_id=thread_id,
        snapshot=snapshot,
        observer=thread_observer(thread_id),
        report_title=report_title,
    )


def _record_chat_usages(thread_id: str, usages: list, model: str) -> None:
    from backend.apps.usage_ledger.api import record_run_usages
    from utils.logs import backend_log

    try:
        record_run_usages(usages, execution_id=thread_id, model=model, source="chat")
    except Exception:
        backend_log.exception("chat usage ledger write failed thread=%s", thread_id)


async def _dump_meta(
    agent: object, content: str, *, assistant_id: str, thread_id: str, snapshot: dict
) -> dict:
    model = getattr(agent, "model", None)
    try:
        schemas = await agent.toolkit.get_tool_schemas()
    except Exception:  # noqa: BLE001 - 调试清单取不到不影响这一轮对话
        schemas = []
    return {
        "assistant_id": assistant_id,
        "thread_id": thread_id,
        "agent": str(getattr(agent, "name", "") or ""),
        "model": str(getattr(model, "model", "") or ""),
        "provider": str(snapshot.get("provider") or ""),
        "base_url": str(snapshot.get("base_url") or ""),
        "api_key_env": str(snapshot.get("api_key_env") or ""),
        "system_prompt": str(snapshot.get("system_prompt") or ""),
        "tool_schemas": schemas,
        "input": content,
    }


def _dump_end(record: object, raw_path) -> dict:
    return {
        "cost_s": record.cost_s,
        "final_text": record.final_text,
        "summary": record.summary,
        "usages": [item.as_dict() for item in record.usages],
        "log_path": record.log_path.as_posix(),
        "html_path": record.html_path.as_posix(),
        "raw_path": raw_path.as_posix(),
    }


async def _reply(
    agent: object,
    content: str,
    *,
    assistant_id: str,
    thread_id: str,
    snapshot: dict | None = None,
    observer: object | None = None,
    report_title: str = "",
) -> tuple[str, str, list, str]:
    import time

    from agentscope.message import UserMsg

    from engines.ae_harness.event import (
        AgentEventRecorder,
        AlignedReportRenderer,
        AlignedRun,
        RawEventDump,
    )
    from engines.backend_bridge.reports import ASSISTANT_LOG_ROOT

    binding = dict(snapshot or {})
    role = str(getattr(agent, "name", "assistant") or "assistant")
    model_name = str(binding.get("model_name") or "")
    root = ASSISTANT_LOG_ROOT / assistant_id / thread_id
    recorder = AgentEventRecorder(
        root,
        role,
        api_key_env=str(binding.get("api_key_env") or ""),
        role_models={role: model_name} if model_name else None,
    )
    recorder.begin(content)
    meta = await _dump_meta(
        agent,
        content,
        assistant_id=assistant_id,
        thread_id=thread_id,
        snapshot=binding,
    )
    raw = RawEventDump(recorder.log_path.with_name(f"{recorder.log_path.stem}.raw.jsonl"))
    raw.begin(meta)
    aligned = AlignedRun(recorder.log_path.with_name(f"{recorder.log_path.stem}.aligned.json"))
    aligned.begin(
        {
            "role": role,
            "agent": meta["agent"],
            "model": meta["model"],
            "api_key_env": meta["api_key_env"],
            "assistant_id": assistant_id,
            "thread_id": thread_id,
            "report_title": report_title,
        },
        {
            "system_prompt": meta["system_prompt"],
            "tool_schemas": meta["tool_schemas"],
            "user_message": content,
        },
    )
    if observer is not None:
        observer.attach(aligned.observe)
    started = time.perf_counter()
    try:
        async for event in agent.reply_stream(UserMsg(name="user", content=content)):
            recorder.on_event(event)
            raw.feed(event)
            aligned.feed(event)
    finally:
        record = recorder.finish(round(time.perf_counter() - started, 2))
        raw.end(_dump_end(record, raw.path))
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
    usages = [item.as_dict() for item in record.usages]
    model = str(getattr(getattr(agent, "model", None), "model", "") or "")
    return record.final_text or "", record.html_path.parent.name, usages, model


def send_message(thread: AIAssistantThread, content: str) -> AIAssistantMessage:
    if not thread.snapshot:
        card = AIAssistant.objects.filter(assistant_id=thread.assistant_id).first()
        if card is None:
            raise AssistantRoleMissingError("助手不存在")
        thread.snapshot = _snapshot_for(card)
    thread.messages.create(role=AIAssistantMessage.ROLE_USER, content=content)
    thread.status = AIAssistantThread.STATUS_RUNNING
    thread.save(update_fields=["snapshot", "status", "updated_at"])
    queue_turn(thread)
    return thread.messages.order_by("-id").first()


def finish_message(
    thread: AIAssistantThread,
    content: str,
    *,
    status: str,
    report_id: str = "",
) -> None:
    if not AIAssistantThread.objects.filter(pk=thread.pk).exists():
        return
    thread.messages.create(
        role=AIAssistantMessage.ROLE_ASSISTANT,
        content=content,
        report_id=report_id,
    )
    thread.status = status
    thread.save(update_fields=["status", "updated_at"])


def rename_thread(thread: AIAssistantThread, title: str) -> AIAssistantThread:
    thread.title = (title or "").strip()[:80]
    thread.save(update_fields=["title", "updated_at"])
    return thread


def delete_thread(thread: AIAssistantThread) -> None:
    thread.delete()


def cancel_thread(thread: AIAssistantThread) -> bool:
    if thread.status != AIAssistantThread.STATUS_RUNNING:
        return False
    thread.status = AIAssistantThread.STATUS_CANCELLED
    thread.save(update_fields=["status", "updated_at"])
    return True


def mark_interrupted_running() -> int:
    running = AIAssistantThread.objects.filter(status=AIAssistantThread.STATUS_RUNNING)
    count = 0
    for thread in running:
        thread.status = AIAssistantThread.STATUS_INTERRUPTED
        thread.save(update_fields=["status"])
        count += 1
    return count
