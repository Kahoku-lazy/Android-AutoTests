from __future__ import annotations

from backend.apps.ai_assistant.models import AIAssistant, AIRole, AISopWorkflow

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

ALLOWED_PAIRS = {
    (ORCHESTRATION_SOP, KIND_UI),
    (ORCHESTRATION_GOAL, KIND_CASE),
    (ORCHESTRATION_TEAM, KIND_REQUIREMENT),
}


class WorkflowNameError(Exception):
    pass


class WorkflowAssistantMissingError(Exception):
    def __init__(self, side: str):
        self.side = side
        super().__init__(f"{side}名片不存在")


class WorkflowPairError(Exception):
    pass


class WorkflowBindingError(Exception):
    pass


class WorkflowRoleMissingError(Exception):
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
    clean = (name or "").strip()
    if not clean:
        raise WorkflowNameError("名称不能为空")
    return clean


def _require_card(assistant_id: str, side: str) -> AIAssistant:
    card = AIAssistant.objects.filter(assistant_id=assistant_id).first()
    if card is None:
        raise WorkflowAssistantMissingError(_side_label(side))
    return card


def _pair(orchestration: str, kind: str) -> tuple[str, str]:
    pair = ((orchestration or "").strip(), (kind or "").strip())
    if pair not in ALLOWED_PAIRS:
        raise WorkflowPairError("该编排与种类不能组合")
    return pair


def _members(raw: list[dict] | None, leader_id: str) -> list[dict]:
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
    return list(AISopWorkflow.objects.order_by("id"))


def get_workflow(workflow_id: int) -> AISopWorkflow:
    return AISopWorkflow.objects.get(pk=workflow_id)


def align_run_names(executor: dict, verifier: dict) -> None:
    name = executor.get("run_name") or ""
    if not name or name != (verifier.get("run_name") or ""):
        return
    verifier["run_name"] = f"{name}-{verifier.get('assistant_id') or ''}"


def _resolve_side(card: AIAssistant, side: str) -> dict:
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
    align_run_names(executor, verifier)
    return {"executor": executor, "verifier": verifier}
