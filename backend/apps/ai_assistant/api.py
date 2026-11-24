"""登记数据对外入口。视图和其它 App 只从这里导入。"""

from django.db import IntegrityError, transaction

from backend.apps.ai_assistant.models import (
    AIAssistant,
    AIAssistantThread,
    AIModelConfig,
    AIRole,
    AISopWorkflow,
    AssistantAuthorGrant,
    AssistantEvalRun,
    AssistantLiveRun,
    AssistantLiveSample,
    AssistantRelease,
    ModelUseGrant,
)
from backend.apps.ai_assistant.services.agent_configs import (
    RoleConflictError,
    RoleIdExhaustedError,
    delete_role,
    get_role,
    list_roles,
    prepare_role,
    replace_kinds,
    update_role,
)
from backend.apps.ai_assistant.services.assistant_cards import (
    AssistantIdExhaustedError,
    AssistantInUseError,
    AssistantRevisionConflict,
    AssistantRoleMissingError,
    AvatarRejectedError,
    delete_assistant,
    get_assistant,
    list_assistants,
    prepare_create,
    update_assistant,
)
from backend.apps.ai_assistant.services.assistant_threads import (
    cancel_thread,
    delete_thread,
    finish_message,
    get_thread,
    is_safe_report_id,
    list_messages,
    list_thread_logs,
    list_threads,
    message_rows,
    new_thread_fields,
    rename_thread,
    resolve_thread_report,
    send_message,
)
from backend.apps.ai_assistant.services.discover import discover_model_names
from backend.apps.ai_assistant.services.model_configs import (
    ModelConfigMissingError,
    delete_model_config,
    get_model_config,
    list_model_configs,
    prepare_model_config,
    update_model_config,
)
from backend.apps.ai_assistant.services.sop_workflows import (
    KIND_CASE,
    KIND_REQUIREMENT,
    KIND_UI,
    ORCHESTRATION_GOAL,
    ORCHESTRATION_SOP,
    ORCHESTRATION_TEAM,
    WorkflowAssistantMissingError,
    WorkflowBindingError,
    WorkflowNameError,
    WorkflowPairError,
    WorkflowRoleMissingError,
    get_workflow,
    list_workflows,
    prepare_workflow,
    resolve_workflow,
)

__all__ = [
    "AISopWorkflow",
    "AssistantIdExhaustedError",
    "AssistantInUseError",
    "AssistantRevisionConflict",
    "publish_assistant",
    "record_eval",
    "create_live_run",
    "append_live_sample",
    "finish_live_run",
    "live_run_detail",
    "get_live_run",
    "workflow_requires_eval",
    "eval_passed",
    "start_live_eval",
    "evaluate_target",
    "publish_workflow",
    "AssistantRoleMissingError",
    "AvatarRejectedError",
    "ModelConfigMissingError",
    "RoleConflictError",
    "RoleIdExhaustedError",
    "KIND_CASE",
    "KIND_REQUIREMENT",
    "KIND_UI",
    "ORCHESTRATION_GOAL",
    "ORCHESTRATION_SOP",
    "ORCHESTRATION_TEAM",
    "WorkflowAssistantMissingError",
    "WorkflowBindingError",
    "WorkflowNameError",
    "WorkflowPairError",
    "WorkflowRoleMissingError",
    "cancel_thread",
    "create_assistant",
    "can_select_model",
    "grant_assistant_author",
    "grant_model_use",
    "list_selectable_model_configs",
    "revoke_model_use",
    "has_assistant_author_grant",
    "revoke_assistant_author",
    "create_thread",
    "finish_message",
    "create_model_config",
    "create_role",
    "create_sop_workflow",
    "delete_assistant",
    "delete_model_config",
    "delete_role",
    "delete_sop_workflow",
    "delete_thread",
    "discover_model_names",
    "get_assistant",
    "get_thread",
    "get_model_config",
    "get_role",
    "get_sop_workflow",
    "list_assistants",
    "list_messages",
    "list_thread_logs",
    "message_rows",
    "resolve_thread_report",
    "is_safe_report_id",
    "list_threads",
    "list_model_configs",
    "list_roles",
    "list_sop_workflows",
    "rename_thread",
    "replace_kinds",
    "resolve_sop_release",
    "resolve_sop_workflow",
    "send_message",
    "update_assistant",
    "update_model_config",
    "update_role",
    "update_sop_workflow",
]


def grant_assistant_author(user_id: int) -> AssistantAuthorGrant:
    """授予助手作者。同一账号重复授予时返回原记录。

    Args:
        user_id: 被授予账号的主键。调用方负责确认操作者是超级管理员。

    Returns:
        该账号的授权记录。

    Raises:
        ValueError: 账号主键不是正整数。
    """
    if int(user_id) <= 0:
        raise ValueError("账号不存在")
    grant, _ = AssistantAuthorGrant.objects.get_or_create(user_id=int(user_id))
    return grant


def revoke_assistant_author(user_id: int) -> bool:
    """收回助手作者。没有授权时也算成功。

    Args:
        user_id: 被收回账号的主键。

    Returns:
        本次是否真的删除了一条授权。
    """
    deleted, _ = AssistantAuthorGrant.objects.filter(user_id=int(user_id)).delete()
    return deleted > 0


def has_assistant_author_grant(user_id: int) -> bool:
    """该账号是否有单独授予的作者记录。不含超级管理员天然资格。"""
    return AssistantAuthorGrant.objects.filter(user_id=int(user_id)).exists()


def create_assistant(
    display_name: str, role_id: str, *, avatar: bytes | None = None, tools: list | None = None
):
    """创建助手名片。写库只在本文件。"""
    latest = (
        AIAssistant.objects.order_by("-created_at", "-id").values_list("marker", flat=True).first()
    )
    fields = prepare_create(
        display_name,
        role_id,
        latest_marker=latest,
        is_taken=lambda candidate: AIAssistant.objects.filter(assistant_id=candidate).exists(),
        avatar=avatar,
        tools=tools,
    )
    try:
        return AIAssistant.objects.create(**fields)
    except IntegrityError as exc:
        raise AssistantIdExhaustedError("助手编号冲突") from exc


def create_model_config(data: dict):
    """新增一条模型配置。同一密钥下的同名模型拒绝重复。

    新配置默认只有超级管理员能主动使用。
    """
    config = AIModelConfig.objects.create(**prepare_model_config(data))
    from django.contrib.auth import get_user_model

    for user_id in get_user_model().objects.filter(is_superuser=True).values_list("id", flat=True):
        ModelUseGrant.objects.get_or_create(user_id=int(user_id), model_config=config)
    return config


def grant_model_use(user_id: int, model_config_id: int) -> ModelUseGrant:
    """把一个模型加入某人的主动使用名单。重复授予返回原记录。"""
    config = get_model_config(model_config_id)
    grant, _ = ModelUseGrant.objects.get_or_create(user_id=int(user_id), model_config=config)
    return grant


def revoke_model_use(user_id: int, model_config_id: int) -> bool:
    """从某人的主动使用名单移除一个模型。没有记录也算成功。"""
    deleted, _ = ModelUseGrant.objects.filter(
        user_id=int(user_id),
        model_config_id=int(model_config_id),
    ).delete()
    return deleted > 0


def can_select_model(user_id: int, model_config_id: int) -> bool:
    """这个人能否主动选择该模型。空名单对任何模型都返回 False。"""
    if not user_id:
        return False
    return ModelUseGrant.objects.filter(
        user_id=int(user_id),
        model_config_id=int(model_config_id),
    ).exists()


def list_selectable_model_configs(user_id: int):
    """返回这个人名单内的聊天模型。向量、语音类没有对话入口。"""
    if not user_id:
        return AIModelConfig.objects.none()
    return list_model_configs("chat").filter(use_grants__user_id=int(user_id)).distinct()


def create_role(
    name: str, model_config_id: int, system_prompt: str = "", *, kinds: list[str] | None = None
):
    """创建 Agent 配置。名称冲突时换一个短标识再试一次。

    类型标签与配置同事务写入：配置建不成功，标签也不会留下。
    """
    for attempt in range(2):
        try:
            with transaction.atomic():
                role = AIRole.objects.create(**prepare_role(name, model_config_id, system_prompt))
                replace_kinds(role, list(kinds or []))
        except IntegrityError as exc:
            if attempt == 0 and not AIRole.objects.filter(name=name).exists():
                continue
            raise RoleConflictError("名称已存在") from exc
        return (
            AIRole.objects.select_related("model_config").prefetch_related("kinds").get(pk=role.pk)
        )
    raise RoleConflictError("名称已存在")


def create_sop_workflow(
    name: str,
    executor_assistant_id: str = "",
    verifier_assistant_id: str = "",
    *,
    orchestration: str = ORCHESTRATION_SOP,
    kind: str = KIND_UI,
    leader_assistant_id: str = "",
    members: list[dict] | None = None,
) -> AISopWorkflow:
    """创建工作流。写库只在本文件。"""
    workflow = AISopWorkflow.objects.create(
        **prepare_workflow(
            name,
            orchestration,
            kind,
            executor_assistant_id,
            verifier_assistant_id,
            leader_assistant_id,
            members,
        )
    )
    return workflow


def update_sop_workflow(
    workflow: AISopWorkflow,
    name: str,
    executor_assistant_id: str = "",
    verifier_assistant_id: str = "",
    *,
    leader_assistant_id: str = "",
    members: list[dict] | None = None,
) -> AISopWorkflow:
    """编辑 SOP 工作流的名称与两侧名片。

    先算完整字段字典再赋值，校验失败时记录不会有任何字段被改。

    Args:
        workflow: 已存在的工作流记录。
        name: 新名称。
        executor_assistant_id: 新执行助手编号。
        verifier_assistant_id: 新验收助手编号。

    Returns:
        回写后的同一条工作流记录。

    Raises:
        WorkflowNameError: 名称为空。
        WorkflowAssistantMissingError: 任一侧名片不存在。
    """
    fields = prepare_workflow(
        name,
        workflow.orchestration,
        workflow.kind,
        executor_assistant_id,
        verifier_assistant_id,
        leader_assistant_id,
        members,
    )
    for key, value in fields.items():
        setattr(workflow, key, value)
    workflow.save(update_fields=[*fields, "updated_at"])
    return workflow


def delete_sop_workflow(workflow: AISopWorkflow) -> None:
    """删除一条 SOP 工作流。

    只删工作流记录；助手名片、Agent 配置与历史任务都不动。

    Args:
        workflow: 要删除的工作流记录。调用方负责先取出记录。
    """
    workflow.delete()


def list_sop_workflows() -> list[AISopWorkflow]:
    """列出全部 SOP 工作流。"""
    return list_workflows()


def get_sop_workflow(workflow_id: int) -> AISopWorkflow:
    """按主键取工作流。不存在时抛 DoesNotExist。"""
    return get_workflow(workflow_id)


def resolve_sop_workflow(workflow_id: int) -> dict:
    """读取该工作流最新已发布版本。没有版本时沿用现读，供旧测试过渡。"""
    release = (
        AssistantRelease.objects.filter(target_kind="workflow", target_id=str(workflow_id))
        .order_by("-version")
        .first()
    )
    if release is None:
        return resolve_workflow(get_workflow(workflow_id))
    return _resolved_from_release(release)


def resolve_sop_release(workflow_id: int, version: int) -> dict:
    """按任务记下的版本号读取。版本不存在时失败，不回退到当前名片。"""
    release = AssistantRelease.objects.filter(
        target_kind="workflow",
        target_id=str(workflow_id),
        version=int(version),
    ).first()
    if release is None:
        raise LookupError("任务记录的发布版本不存在")
    return _resolved_from_release(release)


def _resolved_from_release(release: AssistantRelease) -> dict:
    payload = release.payload
    return {
        "executor": payload.get("executor") or {},
        "verifier": payload.get("verifier") or {},
        "version": release.version,
    }


def _release_payload_for_assistant(card: AIAssistant) -> dict:
    """复制助手当前运行内容。只保留密钥环境变量名。"""
    role = AIRole.objects.select_related("model_config").filter(role_id=card.role_id).first()
    config = role.model_config if role is not None else None
    return {
        "role_id": card.role_id,
        "system_prompt": role.system_prompt if role is not None else "",
        "tools": list(card.tools or []),
        "model_config_id": config.id if config is not None else None,
        "model_name": config.model_name if config is not None else "",
        "provider": config.provider if config is not None else "",
        "api_key_env": config.api_key_env if config is not None else "",
    }


def _next_release(kind: str, target_id: str, payload: dict) -> AssistantRelease:
    """追加一个不可变版本。已有版本不改。"""
    latest = (
        AssistantRelease.objects.filter(target_kind=kind, target_id=target_id)
        .order_by("-version")
        .values_list("version", flat=True)
        .first()
    )
    return AssistantRelease.objects.create(
        target_kind=kind,
        target_id=target_id,
        version=int(latest or 0) + 1,
        payload=payload,
    )


def _fingerprint(payload: dict) -> str:
    import hashlib
    import json

    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def _selected_tool_names(tools: list | None) -> list[str]:
    """从工具勾选里取出名字。预设为全部时视为包含写操作。"""
    names: list[str] = []
    for item in tools or []:
        if not isinstance(item, dict):
            continue
        names.extend(str(name) for name in item.get("add") or [])
        if item.get("preset") == "all":
            names.append("adb_tap")
    return names


def start_live_eval(kind: str, target_id: str) -> AssistantLiveRun:
    """创建一次待运行的评测。目标流和团队流直接拒绝，不落运行。"""
    if kind == "workflow":
        workflow = get_workflow(int(target_id))
        if not workflow_requires_eval(workflow):
            raise ValueError("该组合还没有可观察的运行过程，不能评测")
        payload = workflow_eval_payload(workflow)
    elif kind == "assistant":
        card = get_assistant(target_id)
        if card is None:
            raise LookupError("助手不存在")
        payload = _release_payload_for_assistant(card)
    else:
        raise ValueError("评测对象不正确")
    from backend.apps.ai_assistant.services.eval_samples import sample_ids

    ids = [item for item in sample_ids() if item.startswith("A" if kind == "assistant" else "S")]
    return create_live_run(kind, str(target_id), payload, ids)


def evaluate_target(kind: str, target_id: str) -> dict:
    """对一条助手或工作流草稿跑当前样本。不调用真实模型，也不碰设备。"""
    from backend.apps.ai_assistant.services.eval_rulers import grade
    from backend.apps.ai_assistant.services.eval_samples import load_samples

    if kind == "assistant":
        card = get_assistant(target_id)
        if card is None:
            raise LookupError("助手不存在")
        payload = _release_payload_for_assistant(card)
        names = _selected_tool_names(card.tools)
    elif kind == "workflow":
        workflow = get_workflow(int(target_id))
        if not workflow_requires_eval(workflow):
            raise ValueError("该组合还没有可观察的运行过程，不能评测")
        payload = {
            "executor_assistant_id": workflow.executor_assistant_id,
            "verifier_assistant_id": workflow.verifier_assistant_id,
            "orchestration": workflow.orchestration,
            "kind": workflow.kind,
        }
        verifier = AIAssistant.objects.filter(assistant_id=workflow.verifier_assistant_id).first()
        names = _selected_tool_names(verifier.tools if verifier else [])
    else:
        raise ValueError("评测对象不正确")
    failures: list[dict] = []
    for sample in load_samples():
        if sample.get("kind") != kind:
            continue
        result = dict(sample.get("scripted") or {})
        if kind == "assistant":
            result["tools"] = names
        for item in grade(result, sample["expect"]):
            failures.append({**item, "sample": sample["id"]})
    record_eval(kind, str(target_id), payload, failures)
    return {"passed": not failures, "failures": failures}


def create_live_run(
    kind: str, target_id: str, payload: dict, sample_ids: list[str]
) -> AssistantLiveRun:
    """创建一次待运行的真模型评测。过程随后逐条追加。"""
    return AssistantLiveRun.objects.create(
        target_kind=kind,
        target_id=str(target_id),
        fingerprint=_fingerprint(payload),
        sample_ids=list(sample_ids),
        status=AssistantLiveRun.STATUS_PENDING,
        progress_total=len(sample_ids),
    )


def append_live_sample(
    run_id: int, sample_id: str, title: str, passed: bool, failures: list[dict], steps: list[dict]
) -> AssistantLiveSample:
    """落一条已结束样本，并把运行推进到进行中。"""
    run = AssistantLiveRun.objects.get(pk=run_id)
    sample = AssistantLiveSample.objects.create(
        run=run,
        sample_id=sample_id,
        title=title,
        passed=passed,
        failures=failures,
        steps=steps,
    )
    run.status = AssistantLiveRun.STATUS_RUNNING
    run.phase = "running"
    run.progress_done = run.samples.count()
    run.save(update_fields=["status", "phase", "progress_done", "updated_at"])
    return sample


def finish_live_run(
    run_id: int, *, status: str, failures: list[dict] | None = None, error: str = ""
) -> None:
    """收尾一次评测。失败清单只在完成时写入。"""
    run = AssistantLiveRun.objects.get(pk=run_id)
    run.status = status
    run.phase = "done" if status == AssistantLiveRun.STATUS_DONE else "failed"
    run.failures = list(failures or [])
    run.error = error
    run.progress_done = run.samples.count()
    run.save(update_fields=["status", "phase", "failures", "error", "progress_done", "updated_at"])


def live_run_detail(run_id: int) -> dict | None:
    """一次评测的进度与过程。只出展示字段，不带密钥和图片。"""
    run = get_live_run(run_id)
    if run is None:
        return None
    return {
        "id": run.pk,
        "status": run.status,
        "phase": run.phase,
        "progress_done": run.progress_done,
        "progress_total": run.progress_total,
        "error": run.error,
        "samples": [
            {
                "sample": sample.sample_id,
                "title": sample.title,
                "passed": sample.passed,
                "failures": [
                    {"ruler": item.get("ruler", ""), "text": item.get("text", "")}
                    for item in sample.failures
                ],
                "steps": [
                    {
                        "role": step.get("role", ""),
                        "text": step.get("text", ""),
                        "tool": step.get("tool", ""),
                        "input": step.get("input", {}),
                    }
                    for step in sample.steps
                ],
            }
            for sample in run.samples.all()
        ],
    }


def get_live_run(run_id: int) -> AssistantLiveRun | None:
    """按主键取一次评测，带上已落库的样本。"""
    return AssistantLiveRun.objects.filter(pk=run_id).prefetch_related("samples").first()


def record_eval(kind: str, target_id: str, payload: dict, failures: list[dict]) -> AssistantEvalRun:
    """记下一次自测。样本标识取当前启用样本。"""
    from backend.apps.ai_assistant.services.eval_samples import sample_ids

    return AssistantEvalRun.objects.create(
        target_kind=kind,
        target_id=target_id,
        fingerprint=_fingerprint(payload),
        sample_ids=sample_ids(),
        failures=failures,
    )


def workflow_eval_payload(workflow: AISopWorkflow) -> dict:
    """SOP 评测与发布共用的指纹内容。不含名称。"""
    return {
        "orchestration": workflow.orchestration,
        "kind": workflow.kind,
        "executor_assistant_id": workflow.executor_assistant_id,
        "verifier_assistant_id": workflow.verifier_assistant_id,
    }


def workflow_requires_eval(workflow: AISopWorkflow) -> bool:
    """只有 SOP 走本评测。目标流和团队流保持原发布条件。"""
    return workflow.orchestration == ORCHESTRATION_SOP


def eval_passed(kind: str, target_id: str, payload: dict) -> bool:
    """最新一次完成的真模型评测是否对得上当前内容、当前样本集，且失败清单为空。

    旧的 scripted 自测记录不参与判定。
    """
    from backend.apps.ai_assistant.services.eval_samples import sample_ids

    latest = (
        AssistantLiveRun.objects.filter(
            target_kind=kind,
            target_id=target_id,
            status=AssistantLiveRun.STATUS_DONE,
        )
        .order_by("-id")
        .first()
    )
    if latest is None:
        return False
    return (
        latest.fingerprint == _fingerprint(payload)
        and latest.sample_ids == sample_ids()
        and latest.failures == []
    )


def publish_assistant(card: AIAssistant) -> AssistantRelease:
    """发布助手当前内容。评测门禁在视图层先判，这里只负责冻结。"""
    release = _next_release(
        AssistantRelease.KIND_ASSISTANT, card.assistant_id, _release_payload_for_assistant(card)
    )
    card.release_state = "published"
    card.revision += 1
    card.save(update_fields=["release_state", "revision", "updated_at"])
    return release


def publish_workflow(workflow: AISopWorkflow) -> AssistantRelease:
    """发布工作流。两侧名片没有已发布版本时拒绝。"""
    from backend.apps.ai_assistant.services.sop_workflows import WorkflowBindingError

    for assistant_id in (workflow.executor_assistant_id, workflow.verifier_assistant_id):
        if not assistant_id:
            continue
        card = AIAssistant.objects.filter(
            assistant_id=assistant_id, release_state="published"
        ).first()
        if card is None:
            raise WorkflowBindingError("两侧名片都要先发布")
    payload = {
        "name": workflow.name,
        "orchestration": workflow.orchestration,
        "kind": workflow.kind,
        "executor_assistant_id": workflow.executor_assistant_id,
        "verifier_assistant_id": workflow.verifier_assistant_id,
        "executor": _release_payload_for_assistant(
            AIAssistant.objects.get(assistant_id=workflow.executor_assistant_id)
        )
        if workflow.executor_assistant_id
        else {},
        "verifier": _release_payload_for_assistant(
            AIAssistant.objects.get(assistant_id=workflow.verifier_assistant_id)
        )
        if workflow.verifier_assistant_id
        else {},
    }
    release = _next_release(AssistantRelease.KIND_WORKFLOW, str(workflow.id), payload)
    workflow.release_state = "published"
    workflow.revision += 1
    workflow.save(update_fields=["release_state", "revision", "updated_at"])
    return release


def create_thread(assistant_id: str):
    """新建空对话栏。助手不存在时抛 DoesNotExist。"""
    if not AIAssistant.objects.filter(assistant_id=assistant_id).exists():
        raise AIAssistant.DoesNotExist(assistant_id)
    return AIAssistantThread.objects.create(**new_thread_fields(assistant_id))
