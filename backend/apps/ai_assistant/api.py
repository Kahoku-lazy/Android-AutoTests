from __future__ import annotations

from decimal import Decimal

from django.db import IntegrityError, transaction

from backend.apps.ai_assistant.models import (
    AIAssistant,
    AIAssistantThread,
    AIModelConfig,
    AIRole,
    AISopWorkflow,
    AssistantAuthorGrant,
    AssistantEvalCase,
    AssistantEvalCaseStep,
    AssistantEvalScore,
    AssistantEvalScoreItem,
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
    "score_eval_target",
    "list_eval_scores",
    "list_eval_candidates",
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
    "is_safe_report_id",
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
    if int(user_id) <= 0:
        raise ValueError("账号不存在")
    grant, _ = AssistantAuthorGrant.objects.get_or_create(user_id=int(user_id))
    return grant


def revoke_assistant_author(user_id: int) -> bool:
    deleted, _ = AssistantAuthorGrant.objects.filter(user_id=int(user_id)).delete()
    return deleted > 0


def has_assistant_author_grant(user_id: int) -> bool:
    return AssistantAuthorGrant.objects.filter(user_id=int(user_id)).exists()


def create_assistant(
    display_name: str, role_id: str, *, avatar: bytes | None = None, tools: list | None = None
):
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
    config = AIModelConfig.objects.create(**prepare_model_config(data))
    from django.contrib.auth import get_user_model

    for user_id in get_user_model().objects.filter(is_superuser=True).values_list("id", flat=True):
        ModelUseGrant.objects.get_or_create(user_id=int(user_id), model_config=config)
    return config


def grant_model_use(user_id: int, model_config_id: int) -> ModelUseGrant:
    config = get_model_config(model_config_id)
    grant, _ = ModelUseGrant.objects.get_or_create(user_id=int(user_id), model_config=config)
    return grant


def revoke_model_use(user_id: int, model_config_id: int) -> bool:
    deleted, _ = ModelUseGrant.objects.filter(
        user_id=int(user_id),
        model_config_id=int(model_config_id),
    ).delete()
    return deleted > 0


def can_select_model(user_id: int, model_config_id: int) -> bool:
    if not user_id:
        return False
    return ModelUseGrant.objects.filter(
        user_id=int(user_id),
        model_config_id=int(model_config_id),
    ).exists()


def list_selectable_model_configs(user_id: int):
    if not user_id:
        return AIModelConfig.objects.none()
    return list_model_configs("chat").filter(use_grants__user_id=int(user_id)).distinct()


def create_role(
    name: str, model_config_id: int, system_prompt: str = "", *, kinds: list[str] | None = None
):
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
    workflow.delete()


def list_sop_workflows() -> list[AISopWorkflow]:
    return list_workflows()


def get_sop_workflow(workflow_id: int) -> AISopWorkflow:
    return get_workflow(workflow_id)


def resolve_sop_workflow(workflow_id: int) -> dict:
    release = (
        AssistantRelease.objects.filter(target_kind="workflow", target_id=str(workflow_id))
        .order_by("-version")
        .first()
    )
    if release is None:
        return resolve_workflow(get_workflow(workflow_id))
    return _resolved_from_release(release)


def resolve_sop_release(workflow_id: int, version: int) -> dict:
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
    role = AIRole.objects.select_related("model_config").filter(role_id=card.role_id).first()
    config = role.model_config if role is not None else None
    return {
        "assistant_id": card.assistant_id,
        "run_name": card.display_name,
        "role_id": card.role_id,
        "system_prompt": role.system_prompt if role is not None else "",
        "tools": list(card.tools or []),
        "model_config_id": config.id if config is not None else None,
        "model_name": config.model_name if config is not None else "",
        "provider": config.provider if config is not None else "",
        "api_key_env": config.api_key_env if config is not None else "",
        "base_url": config.base_url if config is not None else "",
    }


def _next_release(kind: str, target_id: str, payload: dict) -> AssistantRelease:
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


def score_eval_target(
    kind: str, target_id: str, *, source_ref: str = "", created_by: str = ""
) -> dict:
    from backend.apps.ai_assistant.services.eval_scores import run_scoring

    if kind not in {"assistant", "workflow"} or not str(target_id).strip():
        raise ValueError("请选择助手或工作流")
    return run_scoring(kind, str(target_id), source_ref=source_ref, created_by=created_by)


def list_eval_scores(kind: str, target_id: str = "", limit: int = 20) -> list[dict]:
    from backend.apps.ai_assistant.services.eval_scores import list_scores

    if kind not in {"assistant", "workflow"}:
        raise ValueError("评测对象不正确")
    return list_scores(kind, str(target_id or ""), limit=limit)


def list_eval_candidates(kind: str, target_id: str = "") -> list[dict]:
    from backend.apps.ai_assistant.services.eval_scores import list_candidates

    if kind not in {"assistant", "workflow"}:
        raise ValueError("评测对象不正确")
    return list_candidates(kind, str(target_id or ""))


def create_eval_score(
    *,
    kind: str,
    target_id: str,
    prompt_fingerprint: str,
    source_ref: str,
    judge_model: str,
    created_by: str,
    items: list[dict],
    method_key: str = "",
    report_html: str = "",
    test_run_json: str = "",
) -> AssistantEvalScore:
    score = AssistantEvalScore.objects.create(
        target_kind=kind,
        target_id=target_id,
        prompt_fingerprint=prompt_fingerprint,
        source_ref=source_ref,
        judge_model=judge_model,
        method_key=method_key,
        report_html=report_html,
        test_run_json=test_run_json,
        created_by=created_by,
    )
    rows = [
        AssistantEvalScoreItem(
            run=score,
            metric_key=str(item["metric_key"]),
            score=Decimal(str(item["score"])),
            reason=str(item.get("reason") or ""),
            threshold=Decimal(str(item.get("threshold") or 0)),
        )
        for item in items
    ]
    if rows:
        AssistantEvalScoreItem.objects.bulk_create(rows)
    return score


def run_suite_eval(
    target_kind: str,
    target_id: str,
    *,
    case_ids: list[str],
    serial: str,
    owner_id: str = "",
    created_by: str = "",
) -> dict:
    from backend.apps.ai_assistant.services.eval_suite import run_suite

    return run_suite(
        target_kind,
        target_id,
        case_ids=case_ids,
        serial=serial,
        owner_id=owner_id,
        created_by=created_by,
    )


def list_eval_methods() -> list[dict]:
    from engines.backend_bridge.eval import list_methods

    return list_methods()


def list_eval_cases() -> list[dict]:
    rows = []
    for case in AssistantEvalCase.objects.prefetch_related("steps").all():
        rows.append(_eval_case_row(case))
    return rows


def _eval_case_row(case: AssistantEvalCase) -> dict:
    return {
        "id": case.pk,
        "title": case.title,
        "note": case.note,
        "enabled": case.enabled,
        "sort_order": case.sort_order,
        "steps": [
            {
                "id": step.pk,
                "sort_order": step.sort_order,
                "action": step.action,
                "assertion": step.assertion,
                "anchor": step.anchor or {},
            }
            for step in case.steps.all()
        ],
    }


def _replace_case_steps(case: AssistantEvalCase, steps: list[dict]) -> None:
    case.steps.all().delete()
    AssistantEvalCaseStep.objects.bulk_create(
        [
            AssistantEvalCaseStep(
                case=case,
                sort_order=index,
                action=str(item.get("action") or ""),
                assertion=str(item.get("assertion") or ""),
                anchor=item.get("anchor") or {},
            )
            for index, item in enumerate(steps, start=1)
        ]
    )


def create_eval_case(
    *, title: str, note: str = "", steps: list[dict] | None = None, created_by: str = ""
) -> dict:
    if not str(title).strip():
        raise ValueError("题目不能为空")
    case = AssistantEvalCase.objects.create(
        title=str(title).strip(), note=note, created_by=created_by
    )
    _replace_case_steps(case, steps or [])
    return _eval_case_row(case)


def update_eval_case(
    case_id: int,
    *,
    title: str = "",
    note: str | None = None,
    enabled: bool | None = None,
    steps: list[dict] | None = None,
) -> dict:
    case = AssistantEvalCase.objects.filter(pk=int(case_id)).first()
    if case is None:
        raise LookupError("评测题不存在")
    if title:
        case.title = str(title).strip()
    if note is not None:
        case.note = note
    if enabled is not None:
        case.enabled = bool(enabled)
    case.save()
    if steps is not None:
        _replace_case_steps(case, steps)
    return _eval_case_row(case)


def delete_eval_case(case_id: int) -> None:
    deleted, _ = AssistantEvalCase.objects.filter(pk=int(case_id)).delete()
    if not deleted:
        raise LookupError("评测题不存在")


def eval_report_file(run_id: int) -> str:
    run = AssistantEvalScore.objects.filter(pk=int(run_id)).first()
    if run is None or not run.report_html:
        raise LookupError("看板不存在")
    return run.report_html


def list_suite_scores(target_id: str = "", limit: int = 20) -> list[dict]:
    from backend.apps.ai_assistant.services.eval_suite import suite_detail

    queryset = AssistantEvalScore.objects.filter(target_kind="suite").order_by("-id")
    if target_id:
        queryset = queryset.filter(target_id=str(target_id))
    rows = []
    for run in queryset[:limit]:
        detail = suite_detail(run.pk)
        if detail is not None:
            rows.append(detail)
    return rows


def workflow_eval_payload(workflow: AISopWorkflow) -> dict:
    return {
        "orchestration": workflow.orchestration,
        "kind": workflow.kind,
        "executor_assistant_id": workflow.executor_assistant_id,
        "verifier_assistant_id": workflow.verifier_assistant_id,
    }


def publish_assistant(card: AIAssistant) -> AssistantRelease:
    if card.release_state == "published":
        raise ValueError("已经发布，请先改一版再发")
    release = _next_release(
        AssistantRelease.KIND_ASSISTANT, card.assistant_id, _release_payload_for_assistant(card)
    )
    card.release_state = "published"
    card.revision += 1
    card.save(update_fields=["release_state", "revision", "updated_at"])
    return release


def publish_workflow(workflow: AISopWorkflow) -> AssistantRelease:
    from backend.apps.ai_assistant.services.sop_workflows import (
        WorkflowBindingError,
        align_run_names,
    )

    if workflow.release_state == "published":
        raise ValueError("已经发布，请先改一版再发")
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
    align_run_names(payload["executor"], payload["verifier"])
    release = _next_release(AssistantRelease.KIND_WORKFLOW, str(workflow.id), payload)
    workflow.release_state = "published"
    workflow.revision += 1
    workflow.save(update_fields=["release_state", "revision", "updated_at"])
    return release


def create_thread(assistant_id: str):
    if not AIAssistant.objects.filter(assistant_id=assistant_id).exists():
        raise AIAssistant.DoesNotExist(assistant_id)
    return AIAssistantThread.objects.create(**new_thread_fields(assistant_id))
