from __future__ import annotations

import json
import logging

from datetime import datetime
from pathlib import Path

from engines.backend_bridge.eval import run_single
from engines.backend_bridge.reports import ASSISTANT_LOG_ROOT, REPORT_ROOT

log = logging.getLogger(__name__)

__all__ = ["CANDIDATE_LIMIT", "list_candidates", "list_scores", "run_scoring"]

CANDIDATE_LIMIT = 30
JUDGE_SOURCE = "assistant_eval_judge"
PROMPT_METRIC = "prompt_quality"
HANDOVER_METRIC = "handover_quality"
_ASSISTANT = "assistant"
_WORKFLOW = "workflow"
RESULTS_ROOT = REPORT_ROOT.parent / "eval_scores"


def _card(kind: str, target_id: str):
    from backend.apps.ai_assistant.models import AIAssistant, AISopWorkflow

    if kind == _WORKFLOW:
        return AISopWorkflow.objects.filter(pk=int(target_id)).first()
    return AIAssistant.objects.filter(assistant_id=target_id).first()


def _prompt_text(kind: str, target_id: str) -> str:
    from backend.apps.ai_assistant.models import AIAssistant, AIRole, AISopWorkflow

    if kind == _WORKFLOW:
        workflow = AISopWorkflow.objects.filter(pk=int(target_id)).first()
        if workflow is None:
            raise LookupError("工作流不存在")
        card = AIAssistant.objects.filter(assistant_id=workflow.executor_assistant_id).first()
    else:
        card = AIAssistant.objects.filter(assistant_id=target_id).first()
    if card is None:
        raise LookupError("助手不存在")
    role = AIRole.objects.filter(role_id=card.role_id).first()
    return str(getattr(role, "system_prompt", "") or "")


def _payload(kind: str, target_id: str) -> dict:
    from backend.apps.ai_assistant import api
    from backend.apps.ai_assistant.models import AIAssistant, AISopWorkflow

    if kind == _WORKFLOW:
        workflow = AISopWorkflow.objects.filter(pk=int(target_id)).first()
        if workflow is None:
            raise LookupError("工作流不存在")
        return api.workflow_eval_payload(workflow)
    card = AIAssistant.objects.filter(assistant_id=target_id).first()
    if card is None:
        raise LookupError("助手不存在")
    return api._release_payload_for_assistant(card)


def _assistant_runs(
    assistant_id: str, limit: int = CANDIDATE_LIMIT
) -> list[tuple[float, str, Path]]:
    root = ASSISTANT_LOG_ROOT / assistant_id
    if not root.is_dir():
        return []
    rows: list[tuple[float, str, Path]] = []
    for path in root.glob("*/*/*.aligned.json"):
        thread = path.parent.parent.name
        stamp = path.parent.name
        rows.append((path.stat().st_mtime, f"{_ASSISTANT}:{assistant_id}:{thread}:{stamp}", path))
    rows.sort(reverse=True)
    return rows[:limit]


def _workflow_runs(limit: int = CANDIDATE_LIMIT) -> list[tuple[float, str, Path]]:
    if not REPORT_ROOT.is_dir():
        return []
    rows: list[tuple[float, str, Path]] = []
    for path in REPORT_ROOT.glob("*/*.aligned.json"):
        rows.append((path.stat().st_mtime, f"task:{path.parent.name}:{path.name}", path))
    rows.sort(reverse=True)
    return rows[:limit]


def _runs(kind: str, target_id: str, limit: int = CANDIDATE_LIMIT) -> list[tuple[float, str, Path]]:
    return _workflow_runs(limit) if kind == _WORKFLOW else _assistant_runs(target_id, limit)


def _read_summary(path: Path) -> dict:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    if not isinstance(payload, dict):
        return {}
    summary = payload.get("summary") if isinstance(payload.get("summary"), dict) else {}
    inputs = payload.get("input") if isinstance(payload.get("input"), dict) else {}
    return {
        "task": str(inputs.get("user_message") or "")[:400],
        "handover": str(summary.get("final_text") or ""),
        "phase": str(summary.get("phase") or ""),
        "cost_s": summary.get("cost_s"),
    }


def list_candidates(kind: str, target_id: str = "", limit: int = CANDIDATE_LIMIT) -> list[dict]:
    items: list[dict] = []
    for moment, ref, path in _runs(kind, target_id, limit):
        info = _read_summary(path)
        items.append(
            {
                "source_ref": ref,
                "dir": path.parent.name,
                "file": path.name,
                "task": info.get("task", ""),
                "handover_chars": len(info.get("handover") or ""),
                "handover": (info.get("handover") or "")[:200],
                "phase": info.get("phase", ""),
                "cost_s": info.get("cost_s"),
                "modified_at": datetime.fromtimestamp(moment).isoformat(timespec="seconds"),
            }
        )
    return items


def _handover_of(kind: str, target_id: str, source_ref: str) -> tuple[str, str]:
    for _, ref, path in _runs(kind, target_id, CANDIDATE_LIMIT):
        if ref != source_ref:
            continue
        info = _read_summary(path)
        handover = str(info.get("handover") or "").strip()
        if not handover:
            raise LookupError(f"这条运行没有交接文本：{source_ref}")
        return str(info.get("task") or ""), handover
    raise LookupError(f"运行产物不存在或已清理：{source_ref}")


def judge_binding(model_config_id: int | None) -> dict:
    from backend.apps.ai_assistant.models import AIModelConfig

    if model_config_id:
        config = AIModelConfig.objects.filter(pk=int(model_config_id)).first()
    else:
        config = AIModelConfig.objects.filter(api_key_env="DEEPSEEK_API_KEY").first()
    if config is None:
        raise ValueError("没有可用的裁判模型配置")
    return {
        "model_config_id": config.pk,
        "provider": config.provider,
        "api_key_env": config.api_key_env,
        "model_name": config.model_name,
        "base_url": config.base_url or "",
    }


def _bill(usages: list[dict], run_id: int) -> None:
    from backend.apps.usage_ledger.api import record_usage

    for index, item in enumerate(usages, start=1):
        try:
            record_usage(
                event_id=f"{JUDGE_SOURCE}:{run_id}:{index}",
                provider=str(item.get("provider") or "deepseek"),
                model=str(item.get("model") or ""),
                occurred_at=datetime.now(),
                input_tokens=int(item.get("input_tokens") or 0),
                output_tokens=int(item.get("output_tokens") or 0),
                category="LLM",
                source=JUDGE_SOURCE,
                execution_id=str(run_id),
            )
        except Exception:
            log.exception("eval judge usage write failed run=%s index=%s", run_id, index)


def run_scoring(
    kind: str,
    target_id: str,
    *,
    source_ref: str = "",
    created_by: str = "",
    model_config_id: int | None = None,
) -> dict:
    from backend.apps.ai_assistant import api

    prompt = _prompt_text(kind, target_id)
    if not prompt.strip():
        raise ValueError("这个目标的系统提示词是空的，无法评分")
    ref = source_ref or (_runs(kind, target_id, 1)[0][1] if _runs(kind, target_id, 1) else "")
    judge = judge_binding(model_config_id)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    results_dir = RESULTS_ROOT / f"{kind}_{target_id}_{stamp}"
    handover_error = ""
    handover_subject = ""
    handover_body = ""
    if ref:
        try:
            handover_subject, handover_body = _handover_of(kind, target_id, ref)
        except LookupError as exc:
            handover_error = str(exc)
    else:
        handover_error = "没有可用的运行产物"
    outcome = run_single(
        judge=judge,
        prompt_subject=f"{kind}:{target_id}",
        prompt_body=prompt,
        handover_subject=handover_subject,
        handover_body=handover_body,
        results_dir=results_dir,
    )
    items = [
        {
            "metric_key": str(row.get("metric_key") or PROMPT_METRIC),
            "score": round(float(row["score"]), 3),
            "reason": str(row.get("reason") or "")[:4000],
            "threshold": 0.5,
        }
        for row in outcome["scores"]
    ]
    score = api.create_eval_score(
        kind=kind,
        target_id=str(target_id),
        prompt_fingerprint=api._fingerprint(_payload(kind, target_id)),
        source_ref=ref,
        judge_model=outcome["judge_model"],
        created_by=str(created_by or ""),
        items=items,
        method_key=PROMPT_METRIC,
        report_html=outcome.get("dashboard_html", ""),
        test_run_json=outcome.get("test_run_json", ""),
    )
    _bill(outcome.get("judge_usage") or [], score.pk)
    detail = _detail(score)
    if handover_error:
        detail["missing"] = [{"metric_key": HANDOVER_METRIC, "reason": handover_error}]
    return detail


def _detail(run) -> dict:
    return {
        "id": run.pk,
        "target_kind": run.target_kind,
        "target_id": run.target_id,
        "prompt_fingerprint": run.prompt_fingerprint,
        "source_ref": run.source_ref,
        "judge_model": run.judge_model,
        "method_key": run.method_key,
        "report_html": run.report_html,
        "created_at": run.created_at.isoformat(timespec="seconds"),
        "items": [
            {
                "metric_key": item.metric_key,
                "score": float(item.score),
                "threshold": float(item.threshold),
                "reason": item.reason,
            }
            for item in run.items.all()
        ],
    }


def list_scores(kind: str, target_id: str, limit: int = 20) -> list[dict]:
    from backend.apps.ai_assistant.models import AssistantEvalScore

    queryset = AssistantEvalScore.objects.prefetch_related("items").filter(target_kind=kind)
    if target_id:
        queryset = queryset.filter(target_id=str(target_id))
    return [_detail(run) for run in queryset.order_by("-id")[:limit]]
