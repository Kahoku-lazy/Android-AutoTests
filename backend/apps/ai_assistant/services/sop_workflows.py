"""SOP 工作流：只登记名称与两张名片编号，运行时现读名片。"""

from __future__ import annotations

from backend.apps.ai_assistant.models import AIAssistant, AIRole, AISopWorkflow

# 工作流表只允许这五列。解析结果不得写回。
WORKFLOW_FIELDS = (
    "name",
    "executor_assistant_id",
    "verifier_assistant_id",
    "created_at",
    "updated_at",
)


class WorkflowNameError(Exception):
    """名称为空。"""


class WorkflowAssistantMissingError(Exception):
    """某一侧的名片不存在。"""

    def __init__(self, side: str):
        self.side = side
        super().__init__(f"{side}名片不存在")


class WorkflowRoleMissingError(Exception):
    """名片仍在，但其引用的 Agent 配置已不存在。"""

    def __init__(self, side: str):
        self.side = side
        super().__init__(f"{side}引用的 Agent 配置不存在")


def _side_label(side: str) -> str:
    return "执行助手" if side == "executor" else "验收助手"


def _require_name(name: str) -> str:
    """去空白后确认名称非空。"""
    clean = (name or "").strip()
    if not clean:
        raise WorkflowNameError("名称不能为空")
    return clean


def _require_card(assistant_id: str, side: str) -> AIAssistant:
    """按编号取名片。不存在时说明是哪一侧。"""
    card = AIAssistant.objects.filter(assistant_id=assistant_id).first()
    if card is None:
        raise WorkflowAssistantMissingError(_side_label(side))
    return card


def prepare_workflow(name: str, executor_assistant_id: str, verifier_assistant_id: str) -> dict:
    """校验名称与两侧名片，返回待写入的字段。不写库。

    Args:
        name: 工作流名称。
        executor_assistant_id: 执行助手编号。
        verifier_assistant_id: 验收助手编号。

    Returns:
        只含名称与两个编号的字段字典。

    Raises:
        WorkflowNameError: 名称为空。
        WorkflowAssistantMissingError: 任一侧名片不存在。
    """
    return {
        "name": _require_name(name),
        "executor_assistant_id": _require_card(executor_assistant_id, "executor").assistant_id,
        "verifier_assistant_id": _require_card(verifier_assistant_id, "verifier").assistant_id,
    }


def list_workflows() -> list[AISopWorkflow]:
    """按创建顺序返回全部工作流。"""
    return list(AISopWorkflow.objects.order_by("id"))


def get_workflow(workflow_id: int) -> AISopWorkflow:
    """按主键取工作流。不存在时抛 DoesNotExist。"""
    return AISopWorkflow.objects.get(pk=workflow_id)


def _resolve_side(card: AIAssistant, side: str) -> dict:
    """把一张名片展开成运行参数。不写库。

    Raises:
        WorkflowRoleMissingError: 名片引用的 Agent 配置不存在。
    """
    role = AIRole.objects.select_related("model_config").filter(role_id=card.role_id).first()
    if role is None:
        raise WorkflowRoleMissingError(_side_label(side))
    config = role.model_config
    return {
        "assistant_id": card.assistant_id,
        "run_name": card.display_name,
        "system_prompt": role.system_prompt,
        "provider": config.provider,
        "api_key_env": config.api_key_env,
        "model_name": config.model_name,
        "base_url": config.base_url,
        "tools": list(card.tools or []),
    }


def resolve_workflow(workflow: AISopWorkflow) -> dict:
    """现读工作流两侧名片与其引用的 Agent 配置。

    两侧显示名相同时，验收侧运行名追加自己的 assistant_id，避免用量按角色名叠成一条。
    本函数不写工作流表。

    Args:
        workflow: 已存在的工作流记录。

    Returns:
        含 executor / verifier 两侧运行参数的字典。

    Raises:
        WorkflowAssistantMissingError: 任一侧名片已被删除。
        WorkflowRoleMissingError: 任一侧引用的 Agent 配置已不存在。
    """
    executor_card = _require_card(workflow.executor_assistant_id, "executor")
    verifier_card = _require_card(workflow.verifier_assistant_id, "verifier")
    executor = _resolve_side(executor_card, "executor")
    verifier = _resolve_side(verifier_card, "verifier")
    if executor["run_name"] == verifier["run_name"]:
        verifier["run_name"] = f"{verifier['run_name']}-{verifier['assistant_id']}"
    return {"executor": executor, "verifier": verifier}
