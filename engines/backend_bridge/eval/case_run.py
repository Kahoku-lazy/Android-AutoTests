from __future__ import annotations

import asyncio
import tempfile

from pathlib import Path
from typing import Any

from engines.ae_harness.workflow.sop import load_spec
from engines.backend_bridge.workflow.bound_sop import run_bound_sop

from .scoring import read_handover

__all__ = ["compile_case_yaml", "run_case"]


def compile_case_yaml(case: dict) -> str:
    steps = []
    for index, step in enumerate(case.get("steps") or [], start=1):
        action = " ".join(str(step.get("action", "") or "").split())
        description = (
            f"用例：{case.get('title', '')}\n"
            f"动作：{step.get('action', '')}\n断言：{step.get('assertion', '')}"
        )
        anchor = step.get("anchor") or {}
        if isinstance(anchor, dict) and anchor:
            description += (
                f"\n页面锚点：页面={anchor.get('page', '')}；"
                f"入口={anchor.get('entry', '')}；目标={anchor.get('target', '')}"
            )
        steps.append(
            {
                "subject": action or f"第 {index} 步",
                "description": description,
                "max_attempts": 3,
            }
        )
    if not steps:
        raise ValueError(f"评测题没有可执行步骤：{case.get('title', '')}")
    import yaml

    return yaml.safe_dump(
        {
            "name": str(case.get("case_id") or case.get("title") or "case"),
            "description": "由评测题库编译",
            "steps": steps,
        },
        allow_unicode=True,
        sort_keys=False,
    )


def run_case(
    case: dict,
    *,
    serial: str,
    executor: Any,
    verifier: Any,
    report_root: Path | None = None,
) -> dict:
    text = compile_case_yaml(case)
    handle = tempfile.NamedTemporaryFile(suffix=".yaml", delete=False, mode="w", encoding="utf-8")
    handle.write(text)
    handle.close()
    path = Path(handle.name)
    try:
        spec = load_spec(path)
    finally:
        path.unlink(missing_ok=True)
    outcome = asyncio.run(
        run_bound_sop(spec, executor, verifier, serial=serial, task_id=0, report_root=report_root)
    )
    report_path = outcome.report_path.as_posix() if outcome.report_path else ""
    steps = [
        {
            "index": index,
            "subject": item.subject,
            "passed": bool(item.passed),
            "attempts": int(item.attempts or 0),
            "message": item.message,
        }
        for index, item in enumerate(outcome.steps, start=1)
    ]
    return {
        "steps": steps,
        "steps_total": len(steps),
        "steps_passed": sum(1 for item in steps if item["passed"]),
        "attempts": sum(item["attempts"] for item in steps),
        "cost_s": float(outcome.cost_s or 0),
        "failed_steps": [
            {"subject": item["subject"], "message": item["message"][:400]}
            for item in steps
            if not item["passed"]
        ],
        "handover": read_handover(report_path),
        "report_path": report_path,
        "tokens": dict(outcome.tokens or {}),
    }
