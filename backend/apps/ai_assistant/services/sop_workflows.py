"""
模块功能：➡️ 工作流：登记编排、种类与名片引用，运行时现读名片 🏁
Python 调试：➡️ python -m backend.apps.ai_assistant.services.sop_workflows 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 ai_assistant 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from __future__ import annotations

from backend.apps.ai_assistant.models import AIAssistant, AIRole, AISopWorkflow

# 工作流表允许写入的列。解析出的提示词与工具不得写回。
WORKFLOW_FIELDS = (
    "name",
    "orchestration",
    "kind",
    "executor_assistant_id",
    "verifier_assistant_id",
    "leader_assistant_id",
    "members",
    "created_at",
    "updated_at",
)

ORCHESTRATION_SOP = "sop"
ORCHESTRATION_GOAL = "goal"
ORCHESTRATION_TEAM = "team"
KIND_UI = "ui_automation"
KIND_CASE = "case_authoring"
KIND_REQUIREMENT = "requirement_breakdown"

# 编排与种类只能成对出现。交叉组合在创建和编辑时拒绝。
ALLOWED_PAIRS = {
    (ORCHESTRATION_SOP, KIND_UI),
    (ORCHESTRATION_GOAL, KIND_CASE),
    (ORCHESTRATION_TEAM, KIND_REQUIREMENT),
}


class WorkflowNameError(Exception):
    """名称为空。"""


class WorkflowAssistantMissingError(Exception):
    """某一侧的名片不存在。"""

    def __init__(self, side: str):
        self.side = side
        super().__init__(f"{side}名片不存在")


class WorkflowPairError(Exception):
    """编排与种类不是允许的一对。"""


class WorkflowBindingError(Exception):
    """Team 绑定缺成员、重名或说明为空。"""


class WorkflowRoleMissingError(Exception):
    """名片仍在，但其引用的 Agent 配置已不存在。"""

    def __init__(self, side: str):
        self.side = side
        super().__init__(f"{side}引用的 Agent 配置不存在")


def _side_label(side: str) -> str:
    labels = {
        "executor": "执行助手",
        "verifier": "验收助手",
        "leader": "队长",
    }
    if side.startswith("member:"):
        return f"成员 {side.split(':', 1)[1]}"
    return labels.get(side, side)


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


def _pair(orchestration: str, kind: str) -> tuple[str, str]:
    """确认编排与种类是允许的一对。"""
    pair = ((orchestration or "").strip(), (kind or "").strip())
    if pair not in ALLOWED_PAIRS:
        raise WorkflowPairError("该编排与种类不能组合")
    return pair


def _members(raw: list[dict] | None, leader_id: str) -> list[dict]:
    """校验 Team 成员：至少两名、说明非空、编号不重复且不与队长相同。"""
    rows = list(raw or [])
    if len(rows) < 2:
        raise WorkflowBindingError("团队至少需要两名成员")
    seen: set[str] = set()
    cleaned: list[dict] = []
    for index, item in enumerate(rows, start=1):
        assistant_id = str((item or {}).get("assistant_id") or "").strip()
        description = str((item or {}).get("description") or "").strip()
        if not description:
            raise WorkflowBindingError(f"成员 {index} 缺少说明")
        card = _require_card(assistant_id, f"member:{index}")
        if card.assistant_id == leader_id or card.assistant_id in seen:
            raise WorkflowBindingError("成员不能重复，也不能与队长相同")
        seen.add(card.assistant_id)
        cleaned.append({"assistant_id": card.assistant_id, "description": description})
    return cleaned


def prepare_workflow(
    name: str,
    orchestration: str = ORCHESTRATION_SOP,
    kind: str = KIND_UI,
    executor_assistant_id: str = "",
    verifier_assistant_id: str = "",
    leader_assistant_id: str = "",
    members: list[dict] | None = None,
) -> dict:
    """校验名称、组合与绑定，返回待写入的字段。不写库。

    Args:
        name: 工作流名称。
        orchestration: sop、goal 或 team。
        kind: 与编排成对的种类。
        executor_assistant_id: SOP 与 Goal 的执行名片。
        verifier_assistant_id: SOP 与 Goal 的验收名片。
        leader_assistant_id: Team 的队长名片。
        members: Team 成员，每项含 assistant_id 与 description。

    Returns:
        只含名称、组合与名片引用的字段字典。

    Raises:
        WorkflowNameError: 名称为空。
        WorkflowPairError: 编排与种类不能组合。
        WorkflowAssistantMissingError: 绑定名片不存在。
        WorkflowBindingError: Team 成员不合法。
    """
    pair = _pair(orchestration, kind)
    fields = {
        "name": _require_name(name),
        "orchestration": pair[0],
        "kind": pair[1],
        "executor_assistant_id": "",
        "verifier_assistant_id": "",
        "leader_assistant_id": "",
        "members": [],
    }
    if pair[0] == ORCHESTRATION_TEAM:
        leader = _require_card(leader_assistant_id, "leader")
        fields["leader_assistant_id"] = leader.assistant_id
        fields["members"] = _members(members, leader.assistant_id)
        return fields
    fields["executor_assistant_id"] = _require_card(executor_assistant_id, "executor").assistant_id
    fields["verifier_assistant_id"] = _require_card(verifier_assistant_id, "verifier").assistant_id
    return fields


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
    if workflow.orchestration == ORCHESTRATION_TEAM:
        leader = _resolve_side(_require_card(workflow.leader_assistant_id, "leader"), "leader")
        member_rows = []
        for index, item in enumerate(workflow.members or [], start=1):
            card = _require_card(str(item.get("assistant_id") or ""), f"member:{index}")
            side = _resolve_side(card, f"member:{index}")
            side["description"] = str(item.get("description") or "")
            member_rows.append(side)
        return {"leader": leader, "members": member_rows}
    executor_card = _require_card(workflow.executor_assistant_id, "executor")
    verifier_card = _require_card(workflow.verifier_assistant_id, "verifier")
    executor = _resolve_side(executor_card, "executor")
    verifier = _resolve_side(verifier_card, "verifier")
    if executor["run_name"] == verifier["run_name"]:
        verifier["run_name"] = f"{verifier['run_name']}-{verifier['assistant_id']}"
    return {"executor": executor, "verifier": verifier}
