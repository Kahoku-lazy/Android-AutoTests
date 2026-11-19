"""
python -m 调试路径: backend.apps.report_generator.report_inventory

本模块的业务功能如下：
1. build_report_inventory: 报告台账入口——取两来源候选并组装 {summary, total, items} 负载。
2. assemble_inventory: 纯逻辑组装——候选行的过滤、排序、限量与报告数量统计，不访问数据库。

数据源口径（DB 登记即索引，不扫磁盘）：
- SOP 报告：终态任务且 result 里带 report_run/report_name 定位（执行完成才登记）。
- 智能体报告：正常完成的助手对话轮次（助手消息带非空 report_id）。
未执行/执行中/取消/中断的任务与轮次不进入台账。
"""

from __future__ import annotations

import json

from datetime import datetime, timezone

from backend.apps.ai_assistant.models import AIAssistant, AIAssistantMessage
from backend.apps.task_list.case_identity import case_identity_label
from backend.apps.task_list.models import Task
from backend.models.constants import TaskStatus

# 与 platform-load-budget 对齐：每来源最多扫 1000 条，合并后最多返回 500 条。
_SCAN_LIMIT = 1000
_LIST_LIMIT = 500

# 只有这些终态的任务才可能带报告定位；success 是历史口径，一并承认。
_TERMINAL_STATUSES = frozenset({TaskStatus.COMPLETED, TaskStatus.FAILED, "success"})

# 智能体报告的一句话结果摘要长度。
_SUMMARY_LIMIT = 80

_EMPTY_SUMMARY = {"total_reports": 0, "sop_reports": 0, "agent_reports": 0}


def build_report_inventory(
    user_id: str | None,
    *,
    source: str = "",
    keyword: str = "",
    start_date: str = "",
    end_date: str = "",
) -> dict:
    """
    组装当前用户可见的报告台账负载；不写库。

    Args:
        user_id: 当前用户编号；缺失或非数字时返回空负载。
        source: 来源过滤，sop / agent / 空串（全部）。
        keyword: 关键字，匹配用例名称、任务 ID、助手名称或助手编号。
        start_date: 起始日期（ISO），按报告生成时间过滤。
        end_date: 结束日期（ISO），按报告生成时间过滤。

    Returns:
        含 summary（报告数量三计数）、total（返回行数）、items（报告行）的字典。
    """
    if not user_id:
        return {"summary": dict(_EMPTY_SUMMARY), "total": 0, "items": []}
    try:
        int(user_id)
    except (ValueError, TypeError):
        return {"summary": dict(_EMPTY_SUMMARY), "total": 0, "items": []}

    sop_rows = _fetch_sop_candidates()
    agent_rows, assistant_names = _fetch_agent_candidates()
    return assemble_inventory(
        sop_rows,
        agent_rows,
        assistant_names,
        source=source,
        keyword=keyword,
        start_date=start_date,
        end_date=end_date,
    )


def assemble_inventory(
    sop_rows: list[dict],
    agent_rows: list[dict],
    assistant_names: dict[str, str],
    *,
    source: str = "",
    keyword: str = "",
    start_date: str = "",
    end_date: str = "",
) -> dict:
    """
    把两来源候选行组装成报告台账负载；纯逻辑，不访问数据库。

    Args:
        sop_rows: SOP 候选行（任务轻量列 + result 正文）。
        agent_rows: 智能体候选行（助手消息 + 栏身份）。
        assistant_names: 助手编号到显示名的映射；缺失回落空串。
        source: 来源过滤，sop / agent / 空串（全部）。
        keyword: 关键字，小写包含匹配。
        start_date: 起始日期（ISO）。
        end_date: 结束日期（ISO）。

    Returns:
        含 summary、total、items 的字典；items 按生成时间倒序且不超过返回上限。
    """
    items: list[dict] = []
    for row in sop_rows:
        item = _sop_item(row)
        if item is not None:
            items.append(item)
    for row in agent_rows:
        item = _agent_item(row, assistant_names)
        if item is not None:
            items.append(item)

    needle = keyword.strip().lower()
    kept = [
        item
        for item in items
        if _source_ok(item, source)
        and _keyword_ok(item, needle)
        and _date_ok(item, start_date, end_date)
    ]
    kept.sort(key=_moment_key, reverse=True)

    n_sop = sum(1 for item in kept if item["source"] == "sop")
    n_agent = len(kept) - n_sop
    returned = kept[:_LIST_LIMIT]
    for item in returned:
        item.pop("_moment", None)
    return {
        "summary": {
            "total_reports": len(kept),
            "sop_reports": n_sop,
            "agent_reports": n_agent,
        },
        "total": len(returned),
        "items": returned,
    }


def _fetch_sop_candidates() -> list[dict]:
    """
    取终态任务的轻量列与 result 正文，供纯逻辑侧解析报告定位。

    Returns:
        候选行字典列表，最多 _SCAN_LIMIT 条，按结束时间倒序。
    """
    rows = (
        Task.objects.filter(status__in=sorted(_TERMINAL_STATUSES))
        .only(
            "id",
            "title",
            "status",
            "device_serial",
            "device_label",
            "case_identity",
            "kind",
            "result",
            "started_at",
            "finished_at",
            "created_at",
        )
        .order_by("-finished_at", "-id")[:_SCAN_LIMIT]
    )
    return [
        {
            "task_id": row.id,
            "title": row.title or "",
            "status": row.status or "",
            "device_serial": row.device_serial or "",
            "device_label": row.device_label or "",
            "case_identity": row.case_identity,
            "kind": row.kind or "",
            "result": row.result or "",
            "started_at": row.started_at,
            "finished_at": row.finished_at,
            "created_at": row.created_at,
        }
        for row in rows
    ]


def _fetch_agent_candidates() -> tuple[list[dict], dict[str, str]]:
    """
    取带 report_id 的助手消息与其栏身份，并批量取助手显示名。

    Returns:
        (候选行字典列表, 助手编号到显示名的映射)；候选最多 _SCAN_LIMIT 条。
    """
    messages = (
        AIAssistantMessage.objects.filter(role=AIAssistantMessage.ROLE_ASSISTANT)
        .exclude(report_id="")
        .select_related("thread")
        .order_by("-created_at", "-id")[:_SCAN_LIMIT]
    )
    rows = [
        {
            "assistant_id": message.thread.assistant_id,
            "thread_id": message.thread.thread_id,
            "report_id": message.report_id,
            "content": message.content or "",
            "created_at": message.created_at,
        }
        for message in messages
    ]
    ids = {row["assistant_id"] for row in rows}
    names = dict(
        AIAssistant.objects.filter(assistant_id__in=ids).values_list("assistant_id", "display_name")
    )
    return rows, names


def _sop_item(row: dict) -> dict | None:
    """
    把一条任务候选行收成 SOP 报告行；非终态或无报告定位时返回 None。

    Args:
        row: 任务候选行。

    Returns:
        SOP 报告行字典；不符合入列条件时返回 None。
    """
    status = str(row.get("status") or "").lower()
    if status not in _TERMINAL_STATUSES:
        return None
    run, name = _report_locator(row.get("result"))
    if not run or not name:
        return None
    started = row.get("started_at")
    finished = row.get("finished_at")
    return {
        "source": "sop",
        "report_run": run,
        "report_name": name,
        "task_id": row.get("task_id"),
        "task_title": row.get("title") or "",
        "case_label": ""
        if row.get("kind") == "requirement_breakdown"
        else case_identity_label(row.get("case_identity")),
        "device": ""
        if row.get("kind") in {"case_authoring", "requirement_breakdown"}
        else (row.get("device_label") or "").strip() or (row.get("device_serial") or "").strip(),
        "workflow_kind": row.get("kind") or "",
        "module_count": _module_count(row.get("result")),
        "status": status,
        "started_at": _iso(started or row.get("created_at")),
        "finished_at": _iso(finished),
        "duration": _duration(started, finished),
        "_moment": finished or row.get("created_at") or started,
    }


def _agent_item(row: dict, assistant_names: dict[str, str]) -> dict | None:
    """
    把一条助手消息候选行收成智能体报告行；无 report_id 时返回 None。

    Args:
        row: 助手消息候选行。
        assistant_names: 助手编号到显示名的映射。

    Returns:
        智能体报告行字典；不符合入列条件时返回 None。
    """
    report_id = str(row.get("report_id") or "").strip()
    if not report_id:
        return None
    assistant_id = str(row.get("assistant_id") or "")
    content = " ".join(str(row.get("content") or "").split())
    return {
        "source": "agent",
        "assistant_id": assistant_id,
        "assistant_name": assistant_names.get(assistant_id, ""),
        "thread_id": str(row.get("thread_id") or ""),
        "report_id": report_id,
        "summary": content[:_SUMMARY_LIMIT],
        "created_at": _iso(row.get("created_at")),
        "_moment": row.get("created_at"),
    }


def _module_count(result: object) -> int:
    """从拆解结果读取模块数量。没有时返回 0。"""
    try:
        payload = json.loads(result or "{}")
    except (TypeError, ValueError):
        return 0
    if not isinstance(payload, dict):
        return 0
    try:
        return int(payload.get("module_count") or 0)
    except (TypeError, ValueError):
        return 0


def _report_locator(result: object) -> tuple[str, str]:
    """
    从任务 result 正文解析报告定位；解析失败或缺字段时返回两个空串。

    Args:
        result: 任务结果 JSON 文本。

    Returns:
        (report_run, report_name)。
    """
    try:
        payload = json.loads(result or "{}")
    except (TypeError, ValueError):
        return "", ""
    if not isinstance(payload, dict):
        return "", ""
    return str(payload.get("report_run") or ""), str(payload.get("report_name") or "")


def _source_ok(item: dict, source: str) -> bool:
    """来源过滤：只认 sop / agent，其余值按全部处理。"""
    if source in ("sop", "agent"):
        return item["source"] == source
    return True


def _keyword_ok(item: dict, needle: str) -> bool:
    """
    关键字匹配：SOP 行匹配用例名/任务标题/任务 ID；智能体行匹配助手名/编号。

    纯数字关键字按任务 ID 精确匹配（与 BUG 单关键字口径一致），
    保证「输入任务编号只剩该任务的报告行」。
    """
    if not needle:
        return True
    if needle.isdigit():
        return item["source"] == "sop" and str(item.get("task_id") or "") == needle
    if item["source"] == "sop":
        haystack = " ".join([item.get("case_label") or "", item.get("task_title") or ""])
    else:
        haystack = " ".join([item.get("assistant_name") or "", item.get("assistant_id") or ""])
    return needle in haystack.lower()


def _date_ok(item: dict, start_date: str, end_date: str) -> bool:
    """按报告生成时间的日期部分过滤；没有时间的行在设了日期过滤时不入列。"""
    if not start_date and not end_date:
        return True
    moment = item.get("_moment")
    if moment is None:
        return False
    day = moment.date().isoformat()
    if start_date and day < start_date:
        return False
    if end_date and day > end_date:
        return False
    return True


def _moment_key(item: dict) -> datetime:
    """排序键：生成时间；缺失时落到最小时间，排在最后。"""
    moment = item.get("_moment")
    if moment is None:
        return datetime.min.replace(tzinfo=timezone.utc)
    return moment


def _iso(value) -> str:
    """ISO 时间字符串；空值返回空串。"""
    return value.isoformat() if value else ""


def _duration(started, finished) -> str:
    """
    紧凑耗时文案：不足 1 分钟用秒，不足 1 小时用分秒，超过用时分。

    Args:
        started: 开始时刻，可能为空。
        finished: 结束时刻，可能为空。

    Returns:
        耗时文案；任一端缺失时返回「—」。
    """
    if not started or not finished:
        return "—"
    total = max(int((finished - started).total_seconds()), 0)
    hours, rem = divmod(total, 3600)
    minutes, seconds = divmod(rem, 60)
    if hours:
        return f"{hours}h{minutes:02d}m"
    if minutes:
        return f"{minutes}m{seconds:02d}s"
    return f"{seconds}s"
