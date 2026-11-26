from __future__ import annotations

import logging

from datetime import datetime
from decimal import Decimal
from pathlib import Path

log = logging.getLogger(__name__)

__all__ = ["list_cases", "run_suite", "suite_detail"]

SUITE_KIND = "suite"


def list_cases() -> list[dict]:
    from backend.apps.ai_assistant.models import AssistantEvalCase

    rows = []
    for case in AssistantEvalCase.objects.filter(enabled=True).prefetch_related("steps"):
        rows.append(_case_payload(case))
    return rows


def _case_payload(case) -> dict:
    steps = [
        {
            "action": step.action,
            "assertion": step.assertion,
            "anchor": step.anchor or {},
        }
        for step in case.steps.all()
    ]
    return {
        "case_id": str(case.pk),
        "title": case.title,
        "assertions": "；".join(step["assertion"] for step in steps if step["assertion"]),
        "step_count": len(steps),
        "steps": steps,
    }


def _bindings(target_kind: str, target_id: str):
    from backend.apps.ai_assistant import api
    from backend.apps.ai_assistant.models import AIAssistant, AISopWorkflow
    from engines.backend_bridge.workflow.bound_roles import RoleBinding

    if target_kind == "workflow":
        workflow = AISopWorkflow.objects.filter(pk=int(target_id)).first()
        if workflow is None:
            raise LookupError("工作流不存在")
        resolved = api.resolve_sop_workflow(workflow.id)

        def _pick(side: dict) -> RoleBinding:
            return RoleBinding(
                run_name=side["run_name"],
                system_prompt=side["system_prompt"],
                provider=side["provider"],
                api_key_env=side["api_key_env"],
                model_name=side["model_name"],
                base_url=side.get("base_url") or "",
                tools=tuple(side.get("tools") or []),
            )

        return _pick(resolved["executor"]), _pick(resolved["verifier"])
    card = AIAssistant.objects.filter(assistant_id=target_id).first()
    if card is None:
        raise LookupError("助手不存在")
    payload = api._release_payload_for_assistant(card)
    binding = RoleBinding(
        run_name=str(card.display_name or card.assistant_id),
        system_prompt=str(payload.get("system_prompt") or ""),
        provider=str(payload.get("provider") or ""),
        api_key_env=str(payload.get("api_key_env") or ""),
        model_name=str(payload.get("model_name") or ""),
        tools=tuple(card.tools or []),
    )
    verifier_card = _verifier_card(card)
    if verifier_card is None:
        return binding, binding
    verifier_payload = api._release_payload_for_assistant(verifier_card)
    verifier = RoleBinding(
        run_name=str(verifier_card.display_name or verifier_card.assistant_id),
        system_prompt=str(verifier_payload.get("system_prompt") or ""),
        provider=str(verifier_payload.get("provider") or ""),
        api_key_env=str(verifier_payload.get("api_key_env") or ""),
        model_name=str(verifier_payload.get("model_name") or ""),
        tools=tuple(verifier_card.tools or []),
    )
    return binding, verifier


def _verifier_card(card):
    from backend.apps.ai_assistant.models import AIAssistant, AIRoleKind

    role_ids = list(
        AIRoleKind.objects.filter(kind=AIRoleKind.KIND_VERIFIER).values_list("role_id", flat=True)
    )
    if not role_ids:
        return None
    rows = (
        AIAssistant.objects.filter(role_id__in=role_ids)
        .exclude(assistant_id=card.assistant_id)
        .order_by("-release_state", "id")
    )
    return rows.first()


def run_suite(
    target_kind: str,
    target_id: str,
    *,
    case_ids: list[str],
    serial: str,
    owner_id: str = "",
    created_by: str = "",
    model_config_id: int | None = None,
) -> dict:
    from backend.apps.ai_assistant import api
    from backend.apps.ai_assistant.models import AssistantEvalCase, AssistantEvalCaseResult
    from backend.apps.ai_assistant.services.eval_scores import (
        RESULTS_ROOT,
        _bill,
        _payload,
        judge_binding,
    )
    from engines.backend_bridge.device_guard import require_online
    from engines.backend_bridge.eval import run_case
    from engines.backend_bridge.eval import run_suite as score_suite

    clean = require_online(serial)
    picked = [str(item) for item in case_ids if str(item)]
    if not picked:
        raise ValueError("请选择至少一条真题")
    cards = {
        str(case.pk): case
        for case in AssistantEvalCase.objects.filter(pk__in=picked).prefetch_related("steps")
    }
    missing = [item for item in picked if item not in cards]
    if missing:
        raise LookupError(f"评测题不存在：{', '.join(missing)}")
    executor_binding, verifier_binding = _bindings(target_kind, target_id)
    judge = judge_binding(model_config_id)

    def _runner(case: dict, *, serial: str, report_root: Path | None) -> dict:
        return run_case(
            case,
            serial=serial,
            executor=executor_binding,
            verifier=verifier_binding,
            report_root=report_root,
        )

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    outcome = score_suite(
        judge=judge,
        cases=[_case_payload(cards[item]) for item in picked],
        runner=_runner,
        serial=clean,
        results_dir=RESULTS_ROOT / f"suite_{target_kind}_{target_id}_{stamp}",
    )
    rows = outcome["cases"]
    total_steps = sum(row["steps_total"] for row in rows)
    passed_steps = sum(row["steps_passed"] for row in rows)
    scored = [row["score"] for row in rows]
    pass_rate = round(passed_steps / total_steps, 3) if total_steps else 0.0
    score_avg = round(sum(scored) / len(scored), 3) if scored else 0.0
    run = api.create_eval_score(
        kind=SUITE_KIND,
        target_id=f"{target_kind}:{target_id}",
        prompt_fingerprint=api._fingerprint(_payload(target_kind, target_id)),
        source_ref=f"cases:{','.join(picked)}",
        judge_model=outcome["judge_model"],
        created_by=str(created_by or ""),
        method_key=outcome["method_key"],
        report_html=outcome["dashboard_html"],
        test_run_json=outcome["test_run_json"],
        items=[
            {
                "metric_key": "suite_pass_rate",
                "score": pass_rate,
                "reason": f"{passed_steps}/{total_steps} 步达成，共 {len(rows)} 条真题",
                "threshold": 0.5,
            },
            {
                "metric_key": "suite_score_avg",
                "score": score_avg,
                "reason": f"{len(scored)} 条真题均分",
                "threshold": 0.5,
            },
        ],
    )
    AssistantEvalCaseResult.objects.bulk_create(
        [
            AssistantEvalCaseResult(
                run=run,
                case_id=row["case_id"],
                case_title=row["case_title"],
                steps_total=row["steps_total"],
                steps_passed=row["steps_passed"],
                attempts=row["attempts"],
                cost_s=Decimal(str(row["cost_s"])),
                score=Decimal(str(row["score"])),
                reason=row["reason"],
                failed_steps=row["failed_steps"],
                source_ref=row["source_ref"],
            )
            for row in rows
        ]
    )
    _bill(outcome.get("judge_usage") or [], run.pk)
    return {
        "id": run.pk,
        "target": f"{target_kind}:{target_id}",
        "serial": clean,
        "pass_rate": pass_rate,
        "score_avg": score_avg,
        "report_html": outcome["dashboard_html"],
        "cases": rows,
    }


def suite_detail(run_id: int) -> dict | None:
    from backend.apps.ai_assistant.models import AssistantEvalScore

    run = AssistantEvalScore.objects.filter(pk=run_id, target_kind=SUITE_KIND).first()
    if run is None:
        return None
    return {
        "id": run.pk,
        "target_id": run.target_id,
        "created_at": run.created_at.isoformat(timespec="seconds"),
        "judge_model": run.judge_model,
        "method_key": run.method_key,
        "report_html": run.report_html,
        "items": [
            {"metric_key": item.metric_key, "score": float(item.score), "reason": item.reason}
            for item in run.items.all()
        ],
        "cases": [
            {
                "case_id": row.case_id,
                "case_title": row.case_title,
                "steps_total": row.steps_total,
                "steps_passed": row.steps_passed,
                "attempts": row.attempts,
                "cost_s": float(row.cost_s),
                "score": None if row.score is None else float(row.score),
                "reason": row.reason,
                "failed_steps": row.failed_steps,
                "source_ref": row.source_ref,
            }
            for row in run.cases.all()
        ],
    }
