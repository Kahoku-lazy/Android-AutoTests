"""
模块功能：➡️ 助手测试对话栏。写库只在本模块，运行交给 backend_bridge 🏁
Python 调试：➡️ python -m backend.apps.ai_assistant.services.assistant_threads 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 ai_assistant 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from __future__ import annotations

import secrets

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
    "list_messages",
    "list_threads",
    "mark_interrupted_running",
    "message_rows",
    "queue_turn",
    "rename_thread",
    "send_message",
]


def _local_iso(value) -> str:
    """把本地时间输出成带偏移的 ISO 8601；空值给空串。

    Args:
        value: 模型时间字段（本项目 USE_TZ=False，通常是 naive 本地时间）。

    Returns:
        形如 `2026-11-16T17:55:30+08:00` 的字符串；无值时为 ""。

    Raises:
        无。
    """
    if value is None:
        return ""
    zone = ZoneInfo(settings.TIME_ZONE)
    if timezone.is_naive(value):
        value = value.replace(tzinfo=zone)
    return value.astimezone(zone).isoformat()


def new_thread_fields(assistant_id: str) -> dict:
    """准备一条空对话栏的字段，不写库、不创建 Agent。

    Args:
        assistant_id: 助手编号。

    Returns:
        含 thread_id 与 idle 状态的字段字典。
    """
    return {
        "thread_id": secrets.token_hex(8),
        "assistant_id": assistant_id,
        "status": AIAssistantThread.STATUS_IDLE,
    }


def list_threads(assistant_id: str):
    """列出某助手的对话栏，新的在前。"""
    return AIAssistantThread.objects.filter(assistant_id=assistant_id).order_by(
        "-created_at", "-id"
    )


def get_thread(thread_id: str) -> AIAssistantThread | None:
    """按栏编号取值；不存在返回 None。"""
    return AIAssistantThread.objects.filter(thread_id=thread_id).first()


def thread_log_dir(assistant_id: str, thread_id: str):
    """该栏日志目录。只拼固定根，不接受调用方传入的路径。"""
    from engines.backend_bridge.reports import ASSISTANT_LOG_ROOT

    return ASSISTANT_LOG_ROOT / assistant_id / thread_id


def is_safe_report_id(report_id: str) -> bool:
    """报告编号只能是单层目录名：非空、不是 . 或 ..、且不含路径分隔。"""
    from pathlib import Path

    if not report_id:
        return False
    stamp = Path(report_id).name
    return stamp != "" and stamp not in {".", ".."} and stamp == report_id


def resolve_thread_report(thread: AIAssistantThread, report_id: str):
    """把报告编号解析成栏目录内的 HTML。跳出目录则返回 None。"""
    from pathlib import Path

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
    """列出该栏已记到消息上的报告。进行中的一轮标记为还在写。"""
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
    """按写入顺序返回该栏消息。"""
    return thread.messages.order_by("id")


def message_rows(thread: AIAssistantThread) -> list[dict]:
    """把该栏消息整理成前端字段：角色、正文、本地 ISO 时间。

    Args:
        thread: 对话栏实例。

    Returns:
        按写入顺序的消息字典列表，`created_at` 为带偏移的 ISO 8601 字符串。

    Raises:
        无。
    """
    return [
        {
            "role": item.role,
            "content": item.content,
            "created_at": _local_iso(item.created_at),
        }
        for item in list_messages(thread)
    ]


def _snapshot_for(card: AIAssistant) -> dict:
    """从当前名片与运营配置组装首次发送快照。不把快照写回名片。"""
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
    """在后台跑这一轮。测试里不启动线程。"""
    import sys
    import threading

    if "pytest" in sys.modules:
        return
    threading.Thread(
        target=_run_turn,
        args=(thread.thread_id,),
        daemon=True,
        name=f"assistant-{thread.thread_id}",
    ).start()


def _run_turn(thread_id: str) -> None:
    """取栏的快照，复用该栏实例，把最终文本写回。取消与失败分开记。"""
    import asyncio

    from django.db import close_old_connections

    from engines.ae_harness.middleware.control import RunCancelled
    from engines.backend_bridge.agents.thread_run import thread_agent

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
    try:
        agent = asyncio.run(thread_agent(thread.thread_id, thread.snapshot))
        reply, report_id, usages, model = asyncio.run(
            _reply(agent, user_text, assistant_id=thread.assistant_id, thread_id=thread.thread_id)
        )
        _record_chat_usages(thread.thread_id, usages, model)
        finish_message(thread, reply, status=AIAssistantThread.STATUS_DONE, report_id=report_id)
    except RunCancelled:
        finish_message(thread, "已取消", status=AIAssistantThread.STATUS_CANCELLED)
    except Exception as exc:
        finish_message(thread, f"执行异常: {exc}", status=AIAssistantThread.STATUS_INTERRUPTED)
    finally:
        close_old_connections()


def _record_chat_usages(thread_id: str, usages: list, model: str) -> None:
    """助手对话的逐次用量入账。失败只记日志，不改对话结果。"""
    from backend.apps.usage_ledger.api import record_run_usages
    from utils.logs import backend_log

    try:
        record_run_usages(usages, execution_id=thread_id, model=model, source="chat")
    except Exception:
        backend_log.exception("chat usage ledger write failed thread=%s", thread_id)


async def _reply(
    agent: object, content: str, *, assistant_id: str, thread_id: str
) -> tuple[str, str, list, str]:
    """把用户句交给该栏实例，边跑边记事件。

    Returns:
        (最终文本, 时间戳目录名)。目录名不是绝对路径。
    """
    from agentscope.message import UserMsg

    from engines.ae_harness.event import AgentEventRecorder, HtmlReportRenderer
    from engines.backend_bridge.reports import ASSISTANT_LOG_ROOT

    root = ASSISTANT_LOG_ROOT / assistant_id / thread_id
    recorder = AgentEventRecorder(root, str(getattr(agent, "name", "assistant") or "assistant"))
    recorder.begin(content)
    try:
        async for event in agent.reply_stream(UserMsg(name="user", content=content)):
            recorder.on_event(event)
    finally:
        record = recorder.finish(0)
        HtmlReportRenderer().save(record)
    usages = [item.as_dict() for item in record.usages]
    model = str(getattr(getattr(agent, "model", None), "model", "") or "")
    return record.final_text or "", record.html_path.parent.name, usages, model


def send_message(thread: AIAssistantThread, content: str) -> AIAssistantMessage:
    """记下用户句。首次发送时冻结当时名片；不在这里调用模型。

    Args:
        thread: 对话栏。
        content: 用户输入，已去空白。

    Returns:
        刚写入的用户消息。

    Raises:
        AssistantRoleMissingError: 首次发送时引用的运营配置已不存在。
    """
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
    """写入助手最终文本并更新栏状态。report_id 只存时间戳目录名。"""
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
    """重命名对话栏。空标题表示回到前端默认的「对话 N」。

    Args:
        thread: 待改名的对话栏。
        title: 新标题，调用方已去空白；这里再按模型上限截断。

    Returns:
        更新后的对话栏。
    """
    thread.title = (title or "").strip()[:80]
    thread.save(update_fields=["title", "updated_at"])
    return thread


def delete_thread(thread: AIAssistantThread) -> None:
    """删除对话栏及其消息。进行中的轮次由调用方先请求取消。

    Args:
        thread: 待删除的对话栏；消息随外键级联删除。
    """
    thread.delete()


def cancel_thread(thread: AIAssistantThread) -> bool:
    """把栏标为用户取消。调用方负责置位取消令牌。"""
    if thread.status != AIAssistantThread.STATUS_RUNNING:
        return False
    thread.status = AIAssistantThread.STATUS_CANCELLED
    thread.save(update_fields=["status", "updated_at"])
    return True


def mark_interrupted_running() -> int:
    """进程启动时把仍在跑的栏标为已中断。

    Returns:
        被改写的栏数。
    """
    running = AIAssistantThread.objects.filter(status=AIAssistantThread.STATUS_RUNNING)
    count = 0
    for thread in running:
        thread.status = AIAssistantThread.STATUS_INTERRUPTED
        thread.save(update_fields=["status"])
        count += 1
    return count
