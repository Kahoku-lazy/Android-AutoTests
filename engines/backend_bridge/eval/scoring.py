from __future__ import annotations

import json

from pathlib import Path
from typing import Any

from engines.eval import (
    CASE_SUITE,
    HANDOVER_QUALITY,
    PROMPT_QUALITY,
    EvalCase,
    build_judge,
    run_evaluation,
)

__all__ = ["run_single", "run_suite"]

EVIDENCE_LIMIT = 1500


def _judge_of(judge: dict) -> Any:
    return build_judge(
        provider=str(judge.get("provider") or ""),
        api_key_env=str(judge.get("api_key_env") or ""),
        model_name=str(judge.get("model_name") or ""),
        base_url=str(judge.get("base_url") or ""),
    )


def _cases_of(
    specs: list[dict], runner: Any, *, serial: str, report_root: Path | None
) -> list[dict]:
    rows: list[dict] = []
    for item in specs:
        outcome = runner(item, serial=serial, report_root=report_root)
        rows.append(outcome)
    return rows


def run_single(
    *,
    judge: dict,
    prompt_subject: str,
    prompt_body: str,
    results_dir: Path,
    handover_subject: str = "",
    handover_body: str = "",
) -> dict:
    watcher = _judge_of(judge)
    prompt = run_evaluation(
        [EvalCase(label=prompt_subject, input_text=prompt_subject, actual_output=prompt_body)],
        method_key=PROMPT_QUALITY,
        judge=watcher,
        results_dir=results_dir,
        results_subfolder="prompt",
    )
    handover = None
    if handover_body.strip():
        handover = run_evaluation(
            [
                EvalCase(
                    label=handover_subject or prompt_subject,
                    input_text=handover_subject or prompt_subject,
                    actual_output=handover_body,
                )
            ],
            method_key=HANDOVER_QUALITY,
            judge=watcher,
            results_dir=results_dir,
            results_subfolder="handover",
        )
    scores = [{**row, "metric_key": PROMPT_QUALITY} for row in prompt.scores]
    if handover is not None:
        scores.extend({**row, "metric_key": HANDOVER_QUALITY} for row in handover.scores)
    primary = handover or prompt
    return {
        "scores": scores,
        "dashboard_html": primary.dashboard_html,
        "test_run_json": primary.test_run_json,
        "prompt_dashboard_html": prompt.dashboard_html,
        "handover_dashboard_html": handover.dashboard_html if handover else "",
        "judge_model": str(judge.get("model_name") or ""),
        "judge_usage": prompt.judge_usage + (handover.judge_usage if handover else []),
    }


def _case_text(case: dict, result: dict) -> str:
    steps = result.get("steps") or []
    lines = [f"题目：{case.get('title', '')}"]
    for step in steps:
        mark = "通过" if step.get("passed") else "未通过"
        lines.append(f"- 第 {step.get('index')} 步 {step.get('subject', '')}：{mark}")
        message = str(step.get("message") or "").strip()
        if message and not step.get("passed"):
            lines.append(f"  说明：{message[:400]}")
    handover = str(result.get("handover") or "").strip()
    if handover:
        lines.append(f"交接文本：{handover[:EVIDENCE_LIMIT]}")
    return "\n".join(lines)


def run_suite(
    *,
    judge: dict,
    cases: list[dict],
    runner: Any,
    serial: str,
    results_dir: Path,
    report_root: Path | None = None,
    method_key: str = CASE_SUITE,
) -> dict:
    executed: list[dict] = []
    for case in cases:
        executed.append(
            {"case": case, "result": runner(case, serial=serial, report_root=report_root)}
        )
    payload = [
        EvalCase(
            label=str(item["case"].get("case_id") or item["case"].get("title") or ""),
            input_text=f"题目：{item['case'].get('title', '')}\n断言：{item['case'].get('assertions', '')}",
            actual_output=_case_text(item["case"], item["result"]),
        )
        for item in executed
    ]
    watcher = _judge_of(judge)
    outcome = run_evaluation(
        payload,
        method_key=method_key,
        judge=watcher,
        results_dir=results_dir,
        results_subfolder="suite",
    )
    scored = {row["label"]: row for row in outcome.scores}
    rows: list[dict] = []
    for item in executed:
        key = str(item["case"].get("case_id") or item["case"].get("title") or "")
        grade = scored.get(key, {})
        result = item["result"]
        rows.append(
            {
                "case_id": item["case"].get("case_id", ""),
                "case_title": item["case"].get("title", ""),
                "steps_total": int(result.get("steps_total") or 0),
                "steps_passed": int(result.get("steps_passed") or 0),
                "attempts": int(result.get("attempts") or 0),
                "cost_s": float(result.get("cost_s") or 0),
                "score": float(grade.get("score") or 0),
                "reason": str(grade.get("reason") or ""),
                "failed_steps": result.get("failed_steps") or [],
                "source_ref": str(result.get("report_path") or ""),
            }
        )
    return {
        "method_key": method_key,
        "judge_model": str(judge.get("model_name") or ""),
        "scores": outcome.scores,
        "cases": rows,
        "dashboard_html": outcome.dashboard_html,
        "test_run_json": outcome.test_run_json,
        "judge_usage": outcome.judge_usage,
    }


def read_handover(report_path: str) -> str:
    if not report_path:
        return ""
    path = Path(report_path)
    aligned = path.with_name(path.name.replace(".html", ".aligned.json"))
    if not aligned.is_file():
        return ""
    try:
        document = json.loads(aligned.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return ""
    return str((document.get("summary") or {}).get("final_text") or "")
