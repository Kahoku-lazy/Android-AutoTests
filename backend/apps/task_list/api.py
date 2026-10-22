"""task-list API — task creation, dispatch, billing and read models."""

import json

from django.db import transaction
from django.utils import timezone

from backend.apps.ai_assistant.api import filter_agents_for_user, resolve_assistant_name
from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list.deepseek_billing import task_deepseek_cost
from backend.apps.task_list.models import Task, TaskAttachment
from backend.models.constants import TaskStatus

__all__ = [
    "create_task",
    "add_task_attachment",
    "list_task_attachments",
    "copy_task_attachments",
    "set_config_load_message",
    "rerun_task",
    "start_task",
    "finalize_task",
    "cancel_running_task",
    "delete_task",
    "clear_agent_tasks",
    "recover_orphaned_tasks",
    "begin_drain",
    "is_draining",
    "count_running_tasks",
    "dispatch_device",
    "build_planner_user_input",
    "build_sop_run_input",
    "parse_task_result",
    "task_result_preview",
    "serialize_agent_task_row",
    "serialize_agent_task_detail",
    "dump_task_run_payload",
    "task_deepseek_cost",
    "store_task_media",
    "get_task_media",
]

# 停机排空标志：进程内生效，重启后自然复位。置位后不再领取新的 pending 任务。
_DRAINING = False

# 每个任务最多保留的不同截图数。40 张对多用例任务不够（实测第 2 条用例起一张不剩），
# 300 张覆盖 191 张截图的整轮任务；同画面按 sha256 去重，实际行数通常远小于截图次数。
TASK_MEDIA_LIMIT = 300


def begin_drain() -> None:
    """置位停机排空标志：调用后 dispatch_device 不再领取新任务。"""
    global _DRAINING
    _DRAINING = True


def is_draining() -> bool:
    """当前进程是否处于停机排空状态。"""
    return _DRAINING


def count_running_tasks() -> int:
    """当前进程可见的 running 任务数，供停机排空轮询。"""
    return Task.objects.filter(status=TaskStatus.RUNNING).count()


def recover_orphaned_tasks() -> int:
    """启动恢复：遗留 running → interrupted，回写费用后按设备拉起 pending。

    仅服务进程启动时调用（见 apps.TaskListConfig._run_startup_recovery）；管理命令不触发。
    写库归口本模块（D3 契约：写操作只经 api.py）。
    """
    running = list(Task.objects.filter(status=TaskStatus.RUNNING))
    finished_at = timezone.now()
    for task in running:
        rollup_task_cost(task.id)
        task.status = TaskStatus.INTERRUPTED
        task.result = "执行中断：服务重启导致任务线程终止"
        task.finished_at = finished_at
        task.save(update_fields=["status", "result", "finished_at"])
    serials = (
        Task.objects.filter(status=TaskStatus.PENDING)
        .exclude(device_serial="")
        .values_list("device_serial", flat=True)
        .distinct()
    )
    for serial in serials:
        dispatch_device(serial)
    return len(running)


def create_task(
    agent: AIAgent,
    *,
    title: str,
    goal: str,
    attachment: str = "",
    attachment_filename: str = "",
    device_serial: str = "",
    device_label: str = "",
    case_title: str = "",
) -> Task:
    """创建任务（任务发布）；device_serial 须已在提交时固化。"""
    return Task.objects.create(
        agent=agent,
        title=title,
        goal=goal,
        attachment=attachment,
        attachment_filename=attachment_filename,
        device_serial=device_serial,
        device_label=device_label,
        case_title=case_title,
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
    """写入一条任务附件。调用方只经本函数落库。"""
    return TaskAttachment.objects.create(
        task=task,
        kind=kind,
        filename=filename,
        body=body,
        sort_order=sort_order,
        stored_path=stored_path,
    )


def list_task_attachments(task: Task) -> list[TaskAttachment]:
    """按排序返回任务附件。"""
    return list(task.file_attachments.all())


def copy_task_attachments(source: Task, dest: Task) -> list[TaskAttachment]:
    """把源任务的附件行复制到新任务，不复制磁盘原件，加载结论清空。"""
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
    """返回 YAML 路径。原件还在时用原件；否则用正文写成临时文件。

    Returns:
        (路径, 是否为临时文件)。临时文件由调用方用完删除。
    """
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
    """SOP 执行开场：只由设备序列号按固定模板生成，不拼目标与文档。"""
    serial = (task.device_serial or "").strip()
    return f"本次要操作的设备 serial 是：{serial}。每一步的设备动作都必须带上它。"


def set_config_load_message(task: Task, message: str) -> None:
    """把配置加载结论写到该任务的 YAML 附件行。"""
    (
        TaskAttachment.objects.filter(task=task, kind=TaskAttachment.KIND_CONFIG)
        .order_by("sort_order", "id")
        .update(load_message=message)
    )


def rerun_task(task: Task) -> Task:
    """失败任务克隆新建：复制标题/目标/附件/设备/agent/指定用例，不改原记录。

    调用方负责校验 status==failed，并在返回后 dispatch_device。
    """
    created = create_task(
        task.agent,
        title=task.title or "",
        goal=task.goal or "",
        attachment=task.attachment or "",
        attachment_filename=task.attachment_filename or "",
        device_serial=task.device_serial or "",
        device_label=task.device_label or "",
        case_title=task.case_title or "",
    )
    copy_task_attachments(task, created)
    return created


def start_task(task: Task) -> Task:
    """标记任务开始执行（异步执行线程启动时调用）。"""
    task.status = TaskStatus.RUNNING
    task.started_at = timezone.now()
    task.save(update_fields=["status", "started_at"])
    return task


def build_planner_user_input(task) -> str:
    """规划模型用户输入：四键中文 JSON（无 markdown 代码块）。"""
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
    """按设备抢槽：同 serial 至多一条 running；否则 start 最早 pending 并起线程。"""
    serial = (serial or "").strip()
    if not serial or _DRAINING:
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
        agent_id = claimed.agent_id

        def _spawn() -> None:
            from backend.apps.task_list.task_runner import spawn_task_thread

            spawn_task_thread(task_id, agent_id)

        transaction.on_commit(_spawn)
        return claimed


def finalize_task(
    task: Task,
    *,
    status: str,
    result: str = "",
    usage: dict | None = None,
) -> Task:
    """完成任务：状态/结果/完成时间 + 累计 token 用量（任务发布完成时调用）。

    usage 为工作流返回的任务级 token 累加器（含按模型拆分），空则只落状态/结果。
    """
    task.status = status
    task.result = result
    task.finished_at = timezone.now()
    fields = ["status", "result", "finished_at"]
    if usage:
        task.input_tokens = int(usage.get("input_tokens") or 0)
        task.output_tokens = int(usage.get("output_tokens") or 0)
        task.cache_input_tokens = int(usage.get("cache_input_tokens") or 0)
        task.model_usage = usage.get("models") or {}
        task.by_role = usage.get("by_role") or {}
        fields += ["input_tokens", "output_tokens", "cache_input_tokens", "model_usage", "by_role"]
    task.save(update_fields=fields)
    serial = (task.device_serial or "").strip()
    if serial:
        dispatch_device(serial)
    return task


def cancel_running_task(task: Task) -> Task:
    """关闭运行中的 SOP。排队中的任务拒绝关闭。不调用角色基类的中断方法。"""
    if task.status == TaskStatus.PENDING:
        raise ValueError("排队中的任务不能关闭")
    if task.status != TaskStatus.RUNNING:
        raise ValueError("只有运行中的任务可以关闭")
    from engines.agents.workflow.platform_run import request_cancel

    request_cancel(task.id)
    return finalize_task(task, status=TaskStatus.CANCELLED, result="用户关闭")


def delete_task(task: Task) -> None:
    """删除任务发布记录。"""
    task.delete()


def clear_agent_tasks(agent: AIAgent) -> int:
    """调试：清空该智能体下全部任务发布记录，返回删除条数。"""
    deleted, _ = Task.objects.filter(agent=agent).delete()
    return deleted


def parse_task_result(raw: str) -> dict:
    """解析任务 result 文本：JSON 对象原样返回，纯文本包成 {summary}。"""
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
    """列表卡片用的短摘要，避免把整份过程 JSON 下发。"""
    obj = parse_task_result(raw)
    summary = obj.get("summary") or obj.get("message") or obj.get("reason") or ""
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


def serialize_agent_task_row(task: Task) -> dict:
    """任务发布列表行。正文不下发。"""
    names = _attachment_names(task)
    return {
        "id": task.id,
        "title": task.title,
        "goal": task.goal,
        "status": task.status,
        "result": task_result_preview(task.result),
        "device_serial": task.device_serial,
        "device_label": task.device_label or "",
        "case_title": task.case_title or "",
        "attachment_filename": names[0] if names else "",
        "attachment_names": names,
        "assistant_name": resolve_assistant_name(getattr(task, "agent", None)),
        "created_at": str(task.created_at) if task.created_at else "",
        "started_at": str(task.started_at) if task.started_at else "",
        "finished_at": str(task.finished_at) if task.finished_at else "",
        "deepseek_cost": task_deepseek_cost(task),
    }


def serialize_agent_task_detail(task: Task) -> dict:
    """任务发布详情。新附件行不下发规划输入；历史单附件仍回退旧字段。"""
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
        "goal": task.goal,
        "status": task.status,
        "device_serial": task.device_serial,
        "device_label": task.device_label or "",
        "case_title": task.case_title or "",
        "assistant_name": resolve_assistant_name(getattr(task, "agent", None)),
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
        "deepseek_cost": task_deepseek_cost(task),
        "run": parse_task_result(task.result),
    }


def dump_task_run_payload(payload: dict) -> str:
    """过程结果落库为 JSON 文本。"""
    return json.dumps(payload, ensure_ascii=False)


def insert_task_events(task_id: int, rows: list[dict]) -> None:
    """批量写入任务事件。rows 已是模型字段。"""
    from backend.apps.task_list.models import TaskEvent

    if not rows:
        return
    TaskEvent.objects.bulk_create([TaskEvent(task_id=task_id, **row) for row in rows])


def store_task_media(task_id: int, sha256: str, defaults: dict) -> int | None:
    """按任务内 sha256 去重保存缩略图。超过上限且不是重复图时不存。"""
    from backend.apps.task_list.models import TaskMedia

    found = TaskMedia.objects.filter(task_id=task_id, sha256=sha256).first()
    if found is not None:
        return found.id
    if TaskMedia.objects.filter(task_id=task_id).count() >= TASK_MEDIA_LIMIT:
        return None
    created = TaskMedia.objects.create(task_id=task_id, sha256=sha256, **defaults)
    return created.id


def get_task_media(user_id: str | None, task_id: int, media_id: int):
    """按可见性取一张截图缩略图；任务不可见或图片不属于该任务时返回 None。"""
    from backend.apps.task_list.models import TaskMedia

    if not user_id:
        return None
    agents = filter_agents_for_user(AIAgent.objects.all(), user_id)
    return TaskMedia.objects.filter(task_id=task_id, id=media_id, task__agent__in=agents).first()


def add_usage_hourly(slot: dict, delta: dict) -> None:
    """按唯一槽位累加一次模型调用。agent_id 为 0 表示未知。"""
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


def rollup_task_cost(task_id: int) -> None:
    """用模型调用结束行的费用合计回写任务。"""
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
