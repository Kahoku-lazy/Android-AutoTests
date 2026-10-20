"""ai-assistant API — 跨模块调用的公共接口。

遵循防火墙 #2：所有跨模块写操作必须通过本文件的函数。
"""

import base64
import hashlib
import json

from cryptography.fernet import Fernet
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.ai_assistant.deepseek_billing import task_deepseek_cost
from apps.ai_assistant.models import (
    AIAgent,
    AITask,
    AITaskAttachment,
)
from models.constants import AgentStatus, TaskStatus
from utils.logs import backend_log

__all__ = [
    # Agent 操作
    "create_agent",
    "update_agent",
    "delete_agent",
    "reveal_agent_key",
    # 平台唯一智能体
    "get_platform_agent",
    "get_agent",
    # 任务操作
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
    "dispatch_device",
    "build_planner_user_input",
    "build_sop_run_input",
    "parse_task_result",
    "task_result_preview",
    "resolve_assistant_name",
    "serialize_agent_task_row",
    "serialize_agent_task_detail",
    "dump_task_run_payload",
    "task_deepseek_cost",
    # 加密工具
    "encrypt_key",
    "decrypt_key",
    "mask_key",
    # 多线路模型配置加密工具
    "decrypt_route_configs",
    "mask_route_configs",
    # 跨模块接口
    "get_provider_config",
    # 跨模块只读助手（供 dashboard 等使用，fix-cross-app-firewall）
    "filter_agents_for_user",
]


# ── 跨模块只读助手 ──


def filter_agents_for_user(queryset, user_id: str | None):
    """Scope agent list：超级管理员全量；普通用户 = 超级管理员拥有的共享智能体 ∪ 自己拥有的（遗留）。"""
    if not user_id:
        return queryset.none()
    try:
        is_super = get_user_model().objects.filter(pk=int(user_id), is_superuser=True).exists()
    except (ValueError, TypeError):
        is_super = False
    if is_super:
        return queryset
    superuser_ids = list(
        get_user_model().objects.filter(is_superuser=True).values_list("id", flat=True)
    )
    return queryset.filter(Q(owner_id=user_id) | Q(owner_id__in=superuser_ids))


# ── Agent 写操作（Batch 1 起从 views 下沉，遵循防火墙 #2）──

_AGENT_CREATE_DEFAULTS = {
    "avatar": "🤖",
    "model_provider": "dashscope",
    "model_name": "qwen-max",
}


def _identity_route_config(name: str, avatar: str) -> dict:
    """把基本信息里的名称/头像写进控制设备线路（卡片与任务列表的显示源）。"""
    return {"device_control": {"name": name, "avatar": avatar}}


def create_agent(user_id: int, data: dict) -> AIAgent:
    """创建 Agent：只收基本信息，模型/线路用默认值（改由后台维护）。"""
    name = data.get("name", "")
    avatar = data.get("avatar", _AGENT_CREATE_DEFAULTS["avatar"])
    return AIAgent.objects.create(
        owner_id=int(user_id),
        name=name,
        avatar=avatar,
        tags=data.get("tags", ""),
        description=data.get("description", ""),
        model_provider=_AGENT_CREATE_DEFAULTS["model_provider"],
        model_name=_AGENT_CREATE_DEFAULTS["model_name"],
        route_configs=_identity_route_config(name, avatar),
        key_revealed=False,
    )


def update_agent(agent: AIAgent, data: dict) -> AIAgent:
    """更新基本信息；名称/头像镜像写入控制设备线路，模型配置与 health 保持不变。"""
    data = dict(data)  # 避免修改调用方（Serializer.validated_data）的字典
    for field in ("name", "avatar", "tags", "description"):
        if field in data:
            setattr(agent, field, data[field])

    configs = dict(agent.route_configs or {})
    route = dict(configs.get("device_control") or {})
    identity_changed = False
    for field in ("name", "avatar"):
        if field in data:
            route[field] = data[field]
            identity_changed = True
    if identity_changed:
        configs["device_control"] = route
        agent.route_configs = configs
    agent.save()
    return agent


def delete_agent(agent: AIAgent) -> None:
    """删除 Agent（级联删除其工具/对话/消息）。"""
    agent.delete()


def reveal_agent_key(agent: AIAgent) -> dict:
    """一次性查看 API Key。返回 {api_key, revealed, hint}。"""
    if not agent.api_key:
        raise ValueError("未配置 API Key")
    if agent.key_revealed:
        decrypted = decrypt_key(agent.api_key)
        return {
            "api_key": mask_key(decrypted),
            "revealed": False,
            "hint": "API Key 仅支持一次性查看，已过期",
        }
    decrypted = decrypt_key(agent.api_key)
    agent.key_revealed = True
    agent.save(update_fields=["key_revealed", "updated_at"])
    return {
        "api_key": decrypted,
        "revealed": True,
        "hint": "请立即复制保存，此 Key 仅显示一次",
    }


def get_platform_agent() -> AIAgent | None:
    """返回平台唯一智能体（超级管理员拥有的活跃共享智能体，无则回退首个活跃智能体）。"""
    from django.contrib.auth import get_user_model

    qs = AIAgent.objects.filter(status=AgentStatus.ACTIVE)
    superuser_ids = list(
        get_user_model().objects.filter(is_superuser=True).values_list("id", flat=True)
    )
    if superuser_ids:
        agent = qs.filter(owner_id__in=superuser_ids).order_by("id").first()
        if agent:
            return agent
    return qs.order_by("id").first()


def get_agent(agent_id: int) -> AIAgent | None:
    """按 id 取智能体；不存在返回 None（提交入口用于校验）。"""
    try:
        return AIAgent.objects.filter(id=int(agent_id)).first()
    except (TypeError, ValueError):
        return None


# ── 任务操作（任务发布）──


def recover_orphaned_tasks() -> int:
    """启动恢复：遗留 running → failed，再按设备拉起 pending。返回失败行数。

    仅服务进程启动时调用（见 apps.AiAssistantConfig._run_startup_recovery）；管理命令不触发。
    写库归口本模块（D3 契约：写操作只经 api.py）。
    """
    recovered = AITask.objects.filter(status=TaskStatus.RUNNING).update(
        status=TaskStatus.FAILED,
        result="执行中断：服务重启导致任务线程终止",
        finished_at=timezone.now(),
    )
    serials = (
        AITask.objects.filter(status=TaskStatus.PENDING)
        .exclude(device_serial="")
        .values_list("device_serial", flat=True)
        .distinct()
    )
    for serial in serials:
        dispatch_device(serial)
    return recovered


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
) -> AITask:
    """创建任务（任务发布）；device_serial 须已在提交时固化。"""
    return AITask.objects.create(
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
    task: AITask,
    *,
    kind: str,
    filename: str,
    body: str,
    sort_order: int,
    stored_path: str = "",
) -> AITaskAttachment:
    """写入一条任务附件。调用方只经本函数落库。"""
    return AITaskAttachment.objects.create(
        task=task,
        kind=kind,
        filename=filename,
        body=body,
        sort_order=sort_order,
        stored_path=stored_path,
    )


def list_task_attachments(task: AITask) -> list[AITaskAttachment]:
    """按排序返回任务附件。"""
    return list(task.file_attachments.all())


def copy_task_attachments(source: AITask, dest: AITask) -> list[AITaskAttachment]:
    """把源任务的附件行复制到新任务，不复制磁盘原件，加载结论清空。"""
    created: list[AITaskAttachment] = []
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


def materialize_config_file(task: AITask) -> tuple[str, bool]:
    """返回 YAML 路径。原件还在时用原件；否则用正文写成临时文件。

    Returns:
        (路径, 是否为临时文件)。临时文件由调用方用完删除。
    """
    import tempfile

    from apps.ai_assistant.upload_cleanup import UPLOAD_DIR

    config = next(
        (row for row in list_task_attachments(task) if row.kind == AITaskAttachment.KIND_CONFIG),
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


def build_sop_run_input(task: AITask) -> str:
    """SOP 执行开场：只由设备序列号按固定模板生成，不拼目标与文档。"""
    serial = (task.device_serial or "").strip()
    return f"本次要操作的设备 serial 是：{serial}。每一步的设备动作都必须带上它。"


def set_config_load_message(task: AITask, message: str) -> None:
    """把配置加载结论写到该任务的 YAML 附件行。"""
    (
        AITaskAttachment.objects.filter(task=task, kind=AITaskAttachment.KIND_CONFIG)
        .order_by("sort_order", "id")
        .update(load_message=message)
    )


def rerun_task(task: AITask) -> AITask:
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


def start_task(task: AITask) -> AITask:
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


def dispatch_device(serial: str) -> AITask | None:
    """按设备抢槽：同 serial 至多一条 running；否则 start 最早 pending 并起线程。"""
    serial = (serial or "").strip()
    if not serial:
        return None

    with transaction.atomic():
        locked = (
            AITask.objects.select_for_update()
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
            from apps.ai_assistant.task_runner import spawn_task_thread

            spawn_task_thread(task_id, agent_id)

        transaction.on_commit(_spawn)
        return claimed


def finalize_task(
    task: AITask,
    *,
    status: str,
    result: str = "",
    usage: dict | None = None,
) -> AITask:
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


def cancel_running_task(task: AITask) -> AITask:
    """关闭运行中的 SOP。排队中的任务拒绝关闭。不调用角色基类的中断方法。"""
    if task.status == TaskStatus.PENDING:
        raise ValueError("排队中的任务不能关闭")
    if task.status != TaskStatus.RUNNING:
        raise ValueError("只有运行中的任务可以关闭")
    from engines.agents.workflow.platform_run import request_cancel

    request_cancel(task.id)
    return finalize_task(task, status=TaskStatus.CANCELLED, result="用户关闭")


def delete_task(task: AITask) -> None:
    """删除任务发布记录。"""
    task.delete()


def clear_agent_tasks(agent: AIAgent) -> int:
    """调试：清空该智能体下全部任务发布记录，返回删除条数。"""
    deleted, _ = AITask.objects.filter(agent=agent).delete()
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


def resolve_assistant_name(agent: AIAgent | None) -> str:
    """当前控制设备线路名；空则回退智能体 name。"""
    if agent is None:
        return ""
    route = (agent.route_configs or {}).get("device_control") or {}
    route_name = str(route.get("name") or "").strip()
    if route_name:
        return route_name
    return str(agent.name or "").strip()


def _attachment_names(task: AITask) -> list[str]:
    names = [row.filename for row in list_task_attachments(task) if row.filename]
    if names:
        return names
    legacy = (task.attachment_filename or "").strip()
    return [legacy] if legacy else []


def serialize_agent_task_row(task: AITask) -> dict:
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


def serialize_agent_task_detail(task: AITask) -> dict:
    """任务发布详情。新附件行不下发规划输入；历史单附件仍回退旧字段。"""
    rows = list_task_attachments(task)
    if rows:
        documents = [
            {"filename": row.filename, "body": row.body}
            for row in rows
            if row.kind == AITaskAttachment.KIND_DOCUMENT
        ]
        config = next((row for row in rows if row.kind == AITaskAttachment.KIND_CONFIG), None)
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


# ── 加密工具（与 views.py 共享实现）──


def _get_cipher() -> Fernet:
    key = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
    return Fernet(base64.urlsafe_b64encode(key))


def encrypt_key(plain: str) -> str:
    """加密 API Key（供数据初始化/测试构造线路配置使用）。"""
    if not plain:
        return ""
    return _get_cipher().encrypt(plain.encode()).decode()


def decrypt_key(encrypted: str) -> str:
    """解密 API Key。解密失败时返回空字符串而非崩溃。"""
    if not encrypted:
        return ""
    try:
        return _get_cipher().decrypt(encrypted.encode()).decode()
    except Exception:
        backend_log.exception(
            "API key decryption failed — key may be corrupted or SECRET_KEY rotated"
        )
        return ""


def mask_key(key: str) -> str:
    """脱敏显示 API Key：保留前 3 位 + *** + 后 4 位。"""
    if not key or len(key) < 8:
        return "***"
    return key[:3] + "***" + key[-4:]


ROUTE_MODEL_ROLES = ("planner", "executor", "verifier")


def _copy_route_meta(src: dict, dest: dict) -> None:
    """保留线路级展示字段（name/avatar 等），不进入模型角色加密逻辑。"""
    for key, val in src.items():
        if key not in ROUTE_MODEL_ROLES:
            dest[key] = val


def _transform_route_configs(route_configs: dict, transform) -> dict:
    """对 route_configs 内每条线路模型的 api_key 应用 transform。"""
    result = {}
    for route, models in (route_configs or {}).items():
        if not isinstance(models, dict):
            continue
        result[route] = {}
        _copy_route_meta(models, result[route])
        for role in ROUTE_MODEL_ROLES:
            cfg = models.get(role)
            if not isinstance(cfg, dict):
                continue
            new_cfg = dict(cfg)
            if new_cfg.get("api_key"):
                new_cfg["api_key"] = transform(new_cfg["api_key"])
            result[route][role] = new_cfg
    return result


def decrypt_route_configs(route_configs: dict) -> dict:
    """解密 route_configs 内 api_key。"""
    return _transform_route_configs(route_configs, decrypt_key)


def mask_route_configs(route_configs: dict) -> dict:
    """脱敏 route_configs 内 api_key。"""
    return _transform_route_configs(route_configs, mask_key)


# ── 跨模块接口（避免直接导入 agent_scope 内部模块）──


def insert_task_events(task_id: int, rows: list[dict]) -> None:
    """批量写入任务事件。rows 已是模型字段。"""
    from apps.ai_assistant.models import AITaskEvent

    if not rows:
        return
    AITaskEvent.objects.bulk_create([AITaskEvent(task_id=task_id, **row) for row in rows])


def store_task_media(task_id: int, sha256: str, defaults: dict) -> int | None:
    """按任务内 sha256 去重保存缩略图。超过 40 张且不是重复图时不存。"""
    from apps.ai_assistant.models import AITaskMedia

    found = AITaskMedia.objects.filter(task_id=task_id, sha256=sha256).first()
    if found is not None:
        return found.id
    if AITaskMedia.objects.filter(task_id=task_id).count() >= 40:
        return None
    created = AITaskMedia.objects.create(task_id=task_id, sha256=sha256, **defaults)
    return created.id


def add_usage_hourly(slot: dict, delta: dict) -> None:
    """按唯一槽位累加一次模型调用。agent_id 为 0 表示未知。"""
    from decimal import Decimal

    from django.db import transaction

    from apps.ai_assistant.models import AIUsageHourly

    with transaction.atomic():
        row, created = AIUsageHourly.objects.get_or_create(
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

    from apps.ai_assistant.models import AITask, AITaskEvent

    totals = AITaskEvent.objects.filter(task_id=task_id, event_type="ModelCallEndEvent").aggregate(
        cost_input=Sum("cost_input"),
        cost_cache=Sum("cost_cache"),
        cost_output=Sum("cost_output"),
        cost_total=Sum("cost_total"),
    )
    AITask.objects.filter(id=task_id).update(
        cost_input=totals["cost_input"] or 0,
        cost_cache=totals["cost_cache"] or 0,
        cost_output=totals["cost_output"] or 0,
        cost_total=totals["cost_total"] or 0,
    )


def get_provider_config(provider: str, base_url: str = "", model_name: str = "") -> dict:
    """获取模型 provider 的 API 配置（base_url + api_key 模式）。
    供管理命令等跨模块调用，避免直接导入 agent_scope.provider_registry。
    """
    from apps.ai_assistant.provider_registry import get_provider_config as _get

    return _get(provider, base_url)
