"""登记数据对外入口。视图和其它 App 只从这里导入。"""

from django.db import IntegrityError, transaction

from backend.apps.ai_assistant.models import (
    AIAssistant,
    AIAssistantThread,
    AIModelConfig,
    AIRole,
    AISopWorkflow,
)
from backend.apps.ai_assistant.services.agent_configs import (
    RoleConflictError,
    RoleIdExhaustedError,
    delete_role,
    get_role,
    list_roles,
    prepare_role,
    update_role,
)
from backend.apps.ai_assistant.services.assistant_cards import (
    AssistantIdExhaustedError,
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
    WorkflowAssistantMissingError,
    WorkflowNameError,
    WorkflowRoleMissingError,
    get_workflow,
    list_workflows,
    prepare_workflow,
    resolve_workflow,
)

__all__ = [
    "AISopWorkflow",
    "AssistantIdExhaustedError",
    "AssistantRoleMissingError",
    "AvatarRejectedError",
    "ModelConfigMissingError",
    "RoleConflictError",
    "RoleIdExhaustedError",
    "WorkflowAssistantMissingError",
    "WorkflowNameError",
    "WorkflowRoleMissingError",
    "cancel_thread",
    "create_assistant",
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
    "list_threads",
    "list_model_configs",
    "list_roles",
    "list_sop_workflows",
    "rename_thread",
    "resolve_sop_workflow",
    "send_message",
    "update_assistant",
    "update_model_config",
    "update_role",
    "update_sop_workflow",
]


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
    """新增一条模型配置。同一密钥下的同名模型拒绝重复。"""
    return AIModelConfig.objects.create(**prepare_model_config(data))


def create_role(name: str, model_config_id: int, system_prompt: str = ""):
    """创建 Agent 配置。名称冲突时换一个短标识再试一次。"""
    for attempt in range(2):
        try:
            with transaction.atomic():
                role = AIRole.objects.create(**prepare_role(name, model_config_id, system_prompt))
        except IntegrityError as exc:
            if attempt == 0 and not AIRole.objects.filter(name=name).exists():
                continue
            raise RoleConflictError("名称已存在") from exc
        return AIRole.objects.select_related("model_config").get(pk=role.pk)
    raise RoleConflictError("名称已存在")


def create_sop_workflow(
    name: str, executor_assistant_id: str, verifier_assistant_id: str
) -> AISopWorkflow:
    """创建 SOP 工作流。写库只在本文件。"""
    return AISopWorkflow.objects.create(
        **prepare_workflow(name, executor_assistant_id, verifier_assistant_id)
    )


def update_sop_workflow(
    workflow: AISopWorkflow,
    name: str,
    executor_assistant_id: str,
    verifier_assistant_id: str,
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
    fields = prepare_workflow(name, executor_assistant_id, verifier_assistant_id)
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
    """现读工作流两侧名片。只读，不写工作流表。"""
    return resolve_workflow(get_workflow(workflow_id))


def create_thread(assistant_id: str):
    """新建空对话栏。助手不存在时抛 DoesNotExist。"""
    if not AIAssistant.objects.filter(assistant_id=assistant_id).exists():
        raise AIAssistant.DoesNotExist(assistant_id)
    return AIAssistantThread.objects.create(**new_thread_fields(assistant_id))
