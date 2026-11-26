import base64
import json
import re

from django.db import transaction
from django.db.models import Count
from django.utils import timezone

from backend.apps.task_list.case_identity import case_identity_label, case_identity_rows
from backend.apps.task_list.models import Task, TaskAttachment
from backend.apps.task_list.task_cost import task_cost
from backend.models.constants import TaskKind, TaskStatus
from utils.logs import backend_log

__all__ = [
    "create_task",
    "add_task_attachment",
    "list_task_attachments",
    "copy_task_attachments",
    "set_config_load_message",
    "rerun_task",
    "start_task",
    "touch_heartbeat",
    "finalize_task",
    "claim_terminal",
    "cancel_running_task",
    "delete_task",
    "clear_agent_tasks",
    "task_stats",
    "task_stats_by_agent",
    "recover_orphaned_tasks",
    "sweep_stale_tasks",
    "begin_drain",
    "is_draining",
    "count_running_tasks",
    "dispatch_device",
    "dispatch_case_authoring",
    "build_case_requirement",
    "case_project_code",
    "build_planner_user_input",
    "build_sop_run_input",
    "parse_task_result",
    "task_result_preview",
    "serialize_agent_task_row",
    "serialize_agent_task_detail",
    "dump_task_run_payload",
    "task_cost",
    "store_task_media",
    "get_task_media",
]

_DRAINING = False


def begin_drain() -> None:
    global _DRAINING
    _DRAINING = True


def is_draining() -> bool:
    return _DRAINING


def running_task_ids() -> list[int]:
    return list(Task.objects.filter(status=TaskStatus.RUNNING).values_list("id", flat=True))


def count_running_tasks() -> int:
    return Task.objects.filter(status=TaskStatus.RUNNING).count()


def _status_buckets(counts: dict[str, int]) -> dict:
    success = counts.get(TaskStatus.COMPLETED, 0) + counts.get("success", 0)
    running = counts.get(TaskStatus.RUNNING, 0)
    pending = counts.get(TaskStatus.PENDING, 0)
    total = sum(counts.values())
    finished = max(total - running - pending, 0)
    rate = round(success / finished * 100, 1) if finished else 0.0
    return {
        "total": total,
        "running": running,
        "pending": pending,
        "success": success,
        "failed": counts.get(TaskStatus.FAILED, 0),
        "interrupted": counts.get(TaskStatus.INTERRUPTED, 0),
        "cancelled": counts.get(TaskStatus.CANCELLED, 0),
        "finished": finished,
        "success_rate": rate,
    }


def task_stats(tasks) -> dict:
    counts = {
        str(row["status"] or ""): int(row["count"])
        for row in tasks.values("status").annotate(count=Count("id"))
    }
    return _status_buckets(counts)


def task_stats_by_agent(tasks, agents) -> list[dict]:
    grouped: dict[int, dict[str, int]] = {}
    for row in tasks.values("agent_id", "status").annotate(count=Count("id")):
        agent_id = int(row["agent_id"])
        status = str(row["status"] or "")
        bucket = grouped.setdefault(agent_id, {})
        bucket[status] = bucket.get(status, 0) + int(row["count"])
    names = assistant_names_by_agent([agent.id for agent in agents])
    result: list[dict] = []
    for agent in agents:
        result.append(
            {
                "id": agent.id,
                "name": names.get(agent.id) or agent.name,
                **_status_buckets(grouped.get(int(agent.id), {})),
            }
        )
    return result


SWEEP_STALE_SECONDS = 45


def sweep_stale_tasks(stop_timeout_ids: set[int] | None = None) -> int:
    from datetime import timedelta

    cutoff = timezone.now() - timedelta(seconds=SWEEP_STALE_SECONDS)
    marked = set(stop_timeout_ids or ())
    stale = list(Task.objects.filter(status=TaskStatus.RUNNING).filter(models_q_heartbeat(cutoff)))
    recovered = 0
    for task in stale:
        rollup_task_cost(task.id)
        cause = "stop_timeout" if task.id in marked else "process_lost"
        reason = (
            "停机等待超时，任务线程被终止"
            if cause == "stop_timeout"
            else "进程退出时任务仍在执行，结果未写回"
        )
        claimed = claim_terminal(
            task.id,
            status=TaskStatus.INTERRUPTED,
            result=dump_task_run_payload(
                {
                    "status": "interrupted",
                    "cause": cause,
                    "reason": reason,
                    "summary": reason,
                    "failed_steps": [category_step("interrupted", reason)],
                }
            ),
            release_device=True,
        )
        if claimed is not None:
            recovered += 1
    return recovered


def models_q_heartbeat(cutoff):
    from django.db.models import Q

    return Q(heartbeat_at__isnull=True) | Q(heartbeat_at__lt=cutoff)


def recover_orphaned_tasks() -> int:
    return sweep_stale_tasks()


def create_task(
    *,
    title: str,
    goal: str,
    attachment: str = "",
    attachment_filename: str = "",
    device_serial: str = "",
    device_label: str = "",
    case_title: str = "",
    case_identity: dict | None = None,
    task_kind: str = TaskKind.DEVICE_CONTROL,
    created_by: str = "",
    workflow_id: int | None = None,
    release_version: int | None = None,
    orchestration: str = "",
    kind: str = "",
) -> Task:
    return Task.objects.create(
        title=title,
        task_kind=task_kind,
        created_by=str(created_by or ""),
        goal=goal,
        attachment=attachment,
        attachment_filename=attachment_filename,
        device_serial=device_serial,
        device_label=device_label,
        case_title=case_title,
        case_identity=case_identity or {},
        workflow_id=workflow_id,
        release_version=release_version,
        orchestration=orchestration,
        kind=kind,
        status=TaskStatus.PENDING,
    )


def add_task_attachment(
    task: Task,
    *,
    kind: str,
    filename: str,
    body: str,
    sort_order: int,
    stored_path: str = "",
) -> TaskAttachment:
    return TaskAttachment.objects.create(
        task=task,
        kind=kind,
        filename=filename,
        body=body,
        sort_order=sort_order,
        stored_path=stored_path,
    )


def list_task_attachments(task: Task) -> list[TaskAttachment]:
    return list(task.file_attachments.all())


def copy_task_attachments(source: Task, dest: Task) -> list[TaskAttachment]:
    created: list[TaskAttachment] = []
    for row in list_task_attachments(source):
        created.append(
            add_task_attachment(
                dest,
                kind=row.kind,
                filename=row.filename,
                body=row.body,
                sort_order=row.sort_order,
                stored_path="",
            )
        )
    return created


def materialize_config_file(task: Task) -> tuple[str, bool]:
    import tempfile

    from backend.apps.task_list.upload_cleanup import UPLOAD_DIR

    config = next(
        (row for row in list_task_attachments(task) if row.kind == TaskAttachment.KIND_CONFIG),
        None,
    )
    if config is None:
        raise ValueError("任务没有 YAML 配置")
    if config.stored_path:
        path = UPLOAD_DIR / config.stored_path
        if path.is_file():
            return str(path), False
    handle = tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w", encoding="utf-8")
    handle.write(config.body)
    handle.close()
    return handle.name, True


def build_sop_run_input(task: Task) -> str:
    serial = (task.device_serial or "").strip()
    return f"本次要操作的设备 serial 是：{serial}。每一步的设备动作都必须带上它。"


def build_case_requirement(task: Task, limit: int = 80000) -> str:
    rows = [
        row
        for row in list_task_attachments(task)
        if row.kind == TaskAttachment.KIND_DOCUMENT and (row.body or "").strip()
    ]
    text = "\n\n".join(
        f"## {row.filename or '需求文档'}\n{(row.body or '').strip()}" for row in rows
    )
    if len(text) > limit:
        text = text[:limit] + f"\n\n[... 需求正文超过 {limit} 字，已截断 ...]"
    return text


def case_project_code(task: Task) -> str:
    found = re.search(r"[A-Z]{1,4}\d{3,}[A-Z0-9]*", task.title or "")
    return found.group(0) if found else "PROJ"


def set_config_load_message(task: Task, message: str) -> None:
    (
        TaskAttachment.objects.filter(task=task, kind=TaskAttachment.KIND_CONFIG)
        .order_by("sort_order", "id")
        .update(load_message=message)
    )


def workflow_id_of(task: Task) -> int:
    raw = parse_task_result(task.result).get("workflow_id")
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return 0
    return value if value > 0 else 0


def resolve_rerun_workflow_id(task: Task) -> int:
    found = workflow_id_of(task)
    if found:
        return found
    serial = (task.device_serial or "").strip()
    if not serial:
        return 0
    earlier = Task.objects.filter(
        task_kind=task.task_kind,
        device_serial=serial,
        title=task.title or "",
        case_identity=task.case_identity or {},
        id__lt=task.id,
    ).order_by("-id")
    for row in earlier[:20]:
        found = workflow_id_of(row)
        if found:
            return found
    return 0


def rerun_task(task: Task) -> Task:
    created = create_task(
        title=task.title or "",
        goal=task.goal or "",
        attachment=task.attachment or "",
        attachment_filename=task.attachment_filename or "",
        device_serial=task.device_serial or "",
        device_label=task.device_label or "",
        case_title=task.case_title or "",
        case_identity=task.case_identity or {},
        task_kind=task.task_kind,
        created_by=task.created_by,
        workflow_id=task.workflow_id,
        release_version=task.release_version,
        orchestration=task.orchestration or "",
        kind=task.kind or "",
    )
    workflow_id = resolve_rerun_workflow_id(task)
    if workflow_id:
        created.result = dump_task_run_payload({"workflow_id": workflow_id})
        created.save(update_fields=["result"])
    copy_task_attachments(task, created)
    return created


def touch_heartbeat(task_id: int) -> None:
    Task.objects.filter(pk=task_id, status=TaskStatus.RUNNING).update(heartbeat_at=timezone.now())


def start_task(task: Task) -> Task:
    task.status = TaskStatus.RUNNING
    task.started_at = timezone.now()
    task.save(update_fields=["status", "started_at"])
    return task


def build_planner_user_input(task) -> str:
    return json.dumps(
        {
            "任务标题": getattr(task, "title", None) or "",
            "任务目标": getattr(task, "goal", None) or "",
            "附件文本内容": getattr(task, "attachment", None) or "",
            "设备ID": getattr(task, "device_serial", None) or "",
        },
        ensure_ascii=False,
    )


def dispatch_device(serial: str) -> Task | None:
    serial = (serial or "").strip()
    if not serial:
        return None
    if _DRAINING:
        waiting = (
            Task.objects.filter(device_serial=serial, status=TaskStatus.PENDING)
            .order_by("id")
            .first()
        )
        if waiting is not None:
            backend_log.warning("停机排空拒绝派发 task_id=%s device_serial=%s", waiting.id, serial)
        return None

    with transaction.atomic():
        locked = (
            Task.objects.select_for_update()
            .filter(
                device_serial=serial,
                status__in=[TaskStatus.PENDING, TaskStatus.RUNNING],
            )
            .order_by("id")
        )
        if locked.filter(status=TaskStatus.RUNNING).exists():
            return None
        next_task = locked.filter(status=TaskStatus.PENDING).first()
        if next_task is None:
            return None
        claimed = start_task(next_task)
        task_id = claimed.id

        def _spawn() -> None:
            from backend.apps.task_list.task_runner import spawn_task_thread

            spawn_task_thread(task_id, 0)

        transaction.on_commit(_spawn)
        return claimed


def dispatch_case_authoring(task: Task) -> Task | None:
    if _DRAINING:
        return None
    with transaction.atomic():
        locked = Task.objects.select_for_update().filter(pk=task.pk).first()
        if locked is None or locked.status != TaskStatus.PENDING:
            return None
        claimed = start_task(locked)
        task_id = claimed.id

        def _spawn() -> None:
            from backend.apps.task_list.task_runner import spawn_task_thread

            spawn_task_thread(task_id, 0)

        transaction.on_commit(_spawn)
        return claimed


def claim_terminal(
    task_id: int,
    *,
    status: str,
    result: str = "",
    usage: dict | None = None,
    costs: dict | None = None,
    release_device: bool = True,
) -> Task | None:
    with transaction.atomic():
        locked = Task.objects.select_for_update().filter(pk=task_id).first()
        if locked is None:
            return None
        if locked.status != TaskStatus.RUNNING:
            _apply_usage(locked, usage, costs)
            return None
        locked.status = status
        if result:
            locked.result = merge_task_result(locked.result, result)
        locked.finished_at = timezone.now()
        fields = ["status", "result", "finished_at"]
        fields.extend(_apply_usage(locked, usage, costs))
        locked.save(update_fields=fields)
        serial = (locked.device_serial or "").strip()
        claimed_id = locked.id
    task = Task.objects.get(pk=claimed_id)
    _record_bug_safely(task)
    if release_device and serial:
        dispatch_device(serial)
    return task


def _apply_usage(task: Task, usage: dict | None, costs: dict | None) -> list[str]:
    fields: list[str] = []
    if usage:
        task.input_tokens = int(usage.get("input_tokens") or 0)
        task.output_tokens = int(usage.get("output_tokens") or 0)
        task.cache_input_tokens = int(usage.get("cache_input_tokens") or 0)
        task.model_usage = usage.get("models") or {}
        task.by_role = usage.get("by_role") or {}
        fields += ["input_tokens", "output_tokens", "cache_input_tokens", "model_usage", "by_role"]
    if costs:
        from decimal import Decimal

        task.cost_input = Decimal(str(costs.get("cost_input") or 0))
        task.cost_cache = Decimal(str(costs.get("cost_cache") or 0))
        task.cost_output = Decimal(str(costs.get("cost_output") or 0))
        task.cost_total = Decimal(str(costs.get("cost_total") or 0))
        fields += ["cost_input", "cost_cache", "cost_output", "cost_total"]
    if fields and task.status != TaskStatus.RUNNING:
        task.save(update_fields=fields)
    return fields


def finalize_task(
    task: Task,
    *,
    status: str,
    result: str = "",
    usage: dict | None = None,
    costs: dict | None = None,
    release_device: bool = True,
) -> Task:
    if task.status == TaskStatus.RUNNING:
        claimed = claim_terminal(
            task.id,
            status=status,
            result=result,
            usage=usage,
            costs=costs,
            release_device=release_device,
        )
        if claimed is not None:
            return claimed
        task.refresh_from_db()
        return task
    task.status = status
    if result:
        task.result = merge_task_result(task.result, result)
    task.finished_at = timezone.now()
    fields = ["status", "result", "finished_at"]
    fields.extend(_apply_usage(task, usage, costs))
    task.save(update_fields=fields)
    _record_bug_safely(task)
    serial = (task.device_serial or "").strip()
    if release_device and serial:
        dispatch_device(serial)
    return task


def _record_bug_safely(task: Task) -> None:
    try:
        from backend.apps.bug_manager.api import record_task_bugs

        record_task_bugs(task)
    except Exception:  # noqa: BLE001 - BUG 台账是后处理，不能影响任务终态
        backend_log.exception("record bug tickets failed task=%s", task.id)


def cancel_running_task(task: Task) -> Task:
    if task.status == TaskStatus.PENDING:
        raise ValueError("排队中的任务不能关闭")
    if task.status != TaskStatus.RUNNING:
        raise ValueError("只有运行中的任务可以关闭")
    from engines.backend_bridge.workflow.cancel import request_cancel

    request_cancel(task.id)
    finalized = finalize_task(
        task, status=TaskStatus.CANCELLED, result="用户关闭", release_device=False
    )
    from backend.apps.task_list.task_runner import schedule_cancel_release

    schedule_cancel_release(finalized.id, finalized.device_serial or "", 0)
    return finalized


def delete_task(task: Task) -> None:
    from backend.apps.task_list.media_storage import get_media_storage

    task_id = task.id
    serial = (task.device_serial or "").strip()
    queued = task.status in {TaskStatus.PENDING, TaskStatus.RUNNING}
    task.delete()
    get_media_storage().delete_task(task_id)
    if queued and serial:
        dispatch_device(serial)


def clear_agent_tasks(agent=None) -> int:
    from backend.apps.task_list.media_storage import get_media_storage

    del agent
    task_ids = list(Task.objects.values_list("id", flat=True))
    deleted, _ = Task.objects.all().delete()
    storage = get_media_storage()
    for task_id in task_ids:
        storage.delete_task(task_id)
    return deleted


def merge_task_result(current: str, incoming: str) -> str:
    base = parse_task_result(current)
    extra = parse_task_result(incoming)
    if not extra and (incoming or "").strip() and not base:
        return incoming
    merged = {**base, **{key: value for key, value in extra.items() if value not in ("", None)}}
    if base.get("workflow_id") and not merged.get("workflow_id"):
        merged["workflow_id"] = base["workflow_id"]
    if not merged:
        return incoming
    return dump_task_run_payload(merged)


def parse_task_result(raw: str) -> dict:
    text = (raw or "").strip()
    if not text:
        return {}
    try:
        obj = json.loads(text)
    except json.JSONDecodeError:
        return {"summary": text}
    if isinstance(obj, dict):
        return obj
    return {"summary": str(obj)}


def task_result_preview(raw: str, limit: int = 120) -> str:
    obj = parse_task_result(raw)
    summary = obj.get("reason") or obj.get("summary") or obj.get("message") or ""
    if not summary and isinstance(obj.get("completed"), list) and obj["completed"]:
        summary = f"已完成 {len(obj['completed'])} 项"
    if not summary:
        summary = (raw or "").strip()
    summary = " ".join(str(summary).split())
    if len(summary) > limit:
        return summary[:limit] + "…"
    return summary


def _attachment_names(task: Task) -> list[str]:
    names = [row.filename for row in list_task_attachments(task) if row.filename]
    if names:
        return names
    legacy = (task.attachment_filename or "").strip()
    return [legacy] if legacy else []


TASK_LIST_FIELDS = (
    "id",
    "title",
    "task_kind",
    "goal",
    "status",
    "result",
    "device_serial",
    "device_label",
    "case_title",
    "attachment_filename",
    "created_at",
    "started_at",
    "finished_at",
    "cost_total",
)


def assistant_names_by_agent(agent_ids) -> dict[int, str]:
    del agent_ids
    return {}


def _report_locator(task: Task) -> dict:
    try:
        payload = json.loads(task.result or "{}")
    except (TypeError, ValueError):
        return {"report_run": "", "report_name": ""}
    if not isinstance(payload, dict):
        return {"report_run": "", "report_name": ""}
    return {
        "report_run": str(payload.get("report_run") or ""),
        "report_name": str(payload.get("report_name") or ""),
    }


def _workflow_name(payload: dict) -> str:
    from backend.apps.ai_assistant import api as assistant_api

    raw_id = payload.get("workflow_id")
    try:
        workflow_id = int(raw_id)
    except (TypeError, ValueError):
        workflow_id = 0
    if workflow_id:
        try:
            return assistant_api.get_sop_workflow(workflow_id).name
        except assistant_api.AISopWorkflow.DoesNotExist:
            pass
    executor = str(payload.get("executor_run_name") or "")
    verifier = str(payload.get("verifier_run_name") or "")
    return " / ".join(part for part in (executor, verifier) if part)


def workflow_filter_options() -> list[dict]:
    from backend.apps.ai_assistant import api as assistant_api

    return [
        {"id": workflow.id, "name": workflow.name}
        for workflow in assistant_api.list_sop_workflows()
    ]


def serialize_agent_task_row(task: Task, *, assistant_name: str | None = None) -> dict:
    names = _attachment_names(task)
    payload = parse_task_result(task.result)
    workflow_name = _workflow_name(payload)
    if assistant_name is None:
        assistant_name = workflow_name
    return {
        "id": task.id,
        "title": task.title,
        "task_kind": task.task_kind,
        "workflow_ref": task.workflow_id,
        "orchestration": task.orchestration or "",
        "kind": task.kind or "",
        "goal": task.goal,
        "status": task.status,
        "result": task_result_preview(task.result),
        "device_serial": task.device_serial,
        "device_label": task.device_label or "",
        "case_title": task.case_title or "",
        "case_label": case_identity_label(task.case_identity),
        "case_rows": case_identity_rows(task.case_identity),
        "attachment_filename": names[0] if names else "",
        "attachment_names": names,
        "assistant_name": assistant_name,
        "workflow_id": payload.get("workflow_id") or None,
        "workflow_name": workflow_name,
        "created_at": str(task.created_at) if task.created_at else "",
        "started_at": str(task.started_at) if task.started_at else "",
        "finished_at": str(task.finished_at) if task.finished_at else "",
        "deepseek_cost": task_cost(task),
        **_report_locator(task),
    }


def _sop_binding(task: Task) -> dict:
    payload = parse_task_result(task.result)
    return {
        "executor_assistant_id": str(payload.get("executor_assistant_id") or ""),
        "verifier_assistant_id": str(payload.get("verifier_assistant_id") or ""),
        "executor_run_name": str(payload.get("executor_run_name") or ""),
        "verifier_run_name": str(payload.get("verifier_run_name") or ""),
    }


def serialize_agent_task_detail(task: Task) -> dict:
    rows = list_task_attachments(task)
    if rows:
        documents = [
            {"filename": row.filename, "body": row.body}
            for row in rows
            if row.kind == TaskAttachment.KIND_DOCUMENT
        ]
        config = next((row for row in rows if row.kind == TaskAttachment.KIND_CONFIG), None)
        attachment = documents[0]["body"] if documents else ""
        attachment_filename = config.filename if config else ""
        load_message = config.load_message if config else ""
        yaml_body = config.body if config else ""
        planner_input = ""
    else:
        documents = []
        attachment = task.attachment or ""
        attachment_filename = task.attachment_filename or ""
        load_message = ""
        yaml_body = ""
        planner_input = build_planner_user_input(task)
    return {
        "id": task.id,
        "title": task.title,
        "task_kind": task.task_kind,
        "goal": task.goal,
        "status": task.status,
        "device_serial": task.device_serial,
        "device_label": task.device_label or "",
        "case_title": task.case_title or "",
        "assistant_name": "",
        "attachment_filename": attachment_filename,
        "attachment": attachment,
        "attachment_names": _attachment_names(task),
        "documents": documents,
        "yaml_body": yaml_body,
        "load_message": load_message,
        "planner_input": planner_input,
        "created_at": str(task.created_at) if task.created_at else "",
        "started_at": str(task.started_at) if task.started_at else "",
        "finished_at": str(task.finished_at) if task.finished_at else "",
        "input_tokens": task.input_tokens,
        "output_tokens": task.output_tokens,
        "cache_input_tokens": task.cache_input_tokens,
        "model_usage": task.model_usage or {},
        "deepseek_cost": task_cost(task),
        "run": parse_task_result(task.result),
        **_sop_binding(task),
    }


_MISSING_STEP_TEXT = "未记录"


def step_text(value: object) -> str:
    text = " ".join(str(value or "").split())
    return text or _MISSING_STEP_TEXT


def failed_step_rows(steps: list, kind: str) -> list[dict]:
    rows = []
    for index, item in enumerate(steps, start=1):
        if getattr(item, "passed", False):
            continue
        rows.append(
            {
                "seq": index,
                "name": step_text(getattr(item, "subject", "")),
                "expected": step_text(getattr(item, "expected", "")),
                "actual": step_text(getattr(item, "message", "")),
                "attempts": int(getattr(item, "attempts", 0) or 0),
                "kind": kind,
            }
        )
    return rows


def category_step(kind: str, actual: str, *, name: str = "") -> dict:
    names = {
        "provider": "模型拒绝",
        "device": "设备命令失败",
        "platform": "平台错误",
        "interrupted": "任务中断",
    }
    expected = "该步应完成" if kind in {"provider", "device"} else "每步都有验收结论"
    if kind == "interrupted":
        expected = "流程应跑完"
    return {
        "seq": 1,
        "name": name or names.get(kind, "平台错误"),
        "expected": expected,
        "actual": step_text(actual),
        "attempts": 0,
        "kind": kind,
    }


def dump_task_run_payload(payload: dict) -> str:
    return json.dumps(payload, ensure_ascii=False)


def insert_task_events(task_id: int, rows: list[dict]) -> None:
    from backend.apps.task_list.models import TaskEvent

    if not rows:
        return
    TaskEvent.objects.bulk_create([TaskEvent(task_id=task_id, **row) for row in rows])


def store_task_media(task_id: int, packed: dict, defaults: dict) -> int | None:
    from backend.apps.task_list.media_storage import get_media_storage
    from backend.apps.task_list.models import TaskMedia

    sha256 = str(packed.get("sha256") or "")
    data = packed.get("data") or b""
    if not sha256 or not data:
        return None
    found = TaskMedia.objects.filter(task_id=task_id, sha256=sha256).first()
    if found is not None:
        return found.id
    storage = get_media_storage()
    key = storage.save(task_id, sha256, data)
    created = TaskMedia.objects.create(
        task_id=task_id,
        sha256=sha256,
        media_type=str(packed.get("media_type") or "image/webp"),
        byte_size=len(data),
        width=packed.get("width"),
        height=packed.get("height"),
        storage_key=key,
        thumb_b64="",
        **defaults,
    )
    return created.id


def _visible_media(user_id: str | None, task_id: int, media_id: int):
    from backend.apps.task_list.models import TaskMedia

    if not user_id:
        return None
    return TaskMedia.objects.filter(task_id=task_id, id=media_id).first()


def media_payload(media) -> dict | None:
    from backend.apps.task_list.media_storage import get_media_storage

    storage = get_media_storage()
    data = storage.open(media.storage_key) if media.storage_key else None
    if data is None and (media.thumb_b64 or "").strip():
        data = base64.b64decode(media.thumb_b64)
    if not data:
        return None
    return {
        "sha256": media.sha256,
        "media_type": media.media_type or "image/webp",
        "data": data,
    }


def get_media_by_id(task_id: int, media_id: int):
    from backend.apps.task_list.models import TaskMedia

    return TaskMedia.objects.filter(task_id=task_id, id=media_id).first()


def get_task_media(user_id: str | None, task_id: int, media_id: int) -> dict | None:
    media = _visible_media(user_id, task_id, media_id)
    if media is None:
        return None
    return media_payload(media)


def create_task_media_link(user_id: str | None, task_id: int, media_id: int) -> dict | None:
    from datetime import datetime
    from datetime import timezone as dt_timezone

    from backend.apps.task_list import media_links

    media = _visible_media(user_id, task_id, media_id)
    if media is None:
        return None
    expires, signature = media_links.sign(task_id, media_id)
    return {
        "url": media_links.build_path(task_id, media_id, expires, signature),
        "expires": expires,
        "expires_at": datetime.fromtimestamp(expires, tz=dt_timezone.utc).isoformat(),
    }


def add_usage_hourly(slot: dict, delta: dict) -> None:
    from decimal import Decimal

    from django.db import transaction

    from backend.apps.task_list.models import TaskUsageHourly

    with transaction.atomic():
        row, created = TaskUsageHourly.objects.get_or_create(
            stat_date=slot["stat_date"],
            stat_hour=slot["stat_hour"],
            model=slot["model"],
            role_name=slot["role_name"],
            agent_id=slot["agent_id"],
            defaults={
                "is_peak": slot["is_peak"],
                "role_kind": slot["role_kind"],
            },
        )
        if not created and row.role_kind != slot["role_kind"] and slot["role_kind"]:
            row.role_kind = slot["role_kind"]
        row.calls += 1
        row.input_tokens += int(delta["input_tokens"])
        row.cache_input_tokens += int(delta["cache_input_tokens"])
        row.cache_miss_tokens += int(delta["cache_miss_tokens"])
        row.output_tokens += int(delta["output_tokens"])
        row.cost_input += Decimal(delta["cost_input"])
        row.cost_cache += Decimal(delta["cost_cache"])
        row.cost_output += Decimal(delta["cost_output"])
        row.cost_total += Decimal(delta["cost_total"])
        row.is_peak = bool(slot["is_peak"])
        row.save()


def summarize_ledger_cost(task_id: int) -> tuple[dict, list[str]]:
    from decimal import Decimal

    from backend.apps.usage_ledger.api import summarize_execution_cost

    try:
        return summarize_execution_cost(str(task_id), "task")
    except Exception:
        return {
            "cost_input": Decimal("0"),
            "cost_cache": Decimal("0"),
            "cost_output": Decimal("0"),
            "cost_total": Decimal("0"),
        }, ["账本暂时不可用，费用未汇总"]


def rollup_task_cost(task_id: int) -> None:
    from django.db.models import Sum

    from backend.apps.task_list.models import Task, TaskEvent

    totals = TaskEvent.objects.filter(task_id=task_id, event_type="ModelCallEndEvent").aggregate(
        cost_input=Sum("cost_input"),
        cost_cache=Sum("cost_cache"),
        cost_output=Sum("cost_output"),
        cost_total=Sum("cost_total"),
    )
    Task.objects.filter(id=task_id).update(
        cost_input=totals["cost_input"] or 0,
        cost_cache=totals["cost_cache"] or 0,
        cost_output=totals["cost_output"] or 0,
        cost_total=totals["cost_total"] or 0,
    )
