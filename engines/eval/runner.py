from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from .methods import METHODS, build_metric

__all__ = ["EvalCase", "EvalOutcome", "run_evaluation"]


@dataclass(frozen=True)
class EvalCase:
    label: str
    input_text: str
    actual_output: str


@dataclass
class EvalOutcome:
    scores: list[dict] = field(default_factory=list)
    dashboard_html: str = ""
    test_run_json: str = ""
    judge_usage: list[dict] = field(default_factory=list)


def _metric_name(item: Any) -> str:
    return str(getattr(item, "name", "") or "")


def _dashboard_files(folder: Path) -> tuple[str, str]:
    html_files = sorted(folder.glob("*.html"), key=lambda path: path.stat().st_mtime)
    json_files = sorted(folder.glob("test_run_*.json"), key=lambda path: path.stat().st_mtime)
    return (
        html_files[-1].as_posix() if html_files else "",
        json_files[-1].as_posix() if json_files else "",
    )


def run_evaluation(
    cases: list[EvalCase],
    *,
    method_key: str,
    judge: Any,
    results_dir: Path,
    threshold: float = 0.5,
    results_subfolder: str = "",
) -> EvalOutcome:
    from deepeval import evaluate
    from deepeval.evaluate import AsyncConfig, DisplayConfig
    from deepeval.test_case import LLMTestCase

    if not cases:
        raise ValueError("没有可评测的样本")
    if method_key not in METHODS:
        raise ValueError(f"未知评测方法：{method_key}")
    folder = results_dir / results_subfolder if results_subfolder else results_dir
    folder.mkdir(parents=True, exist_ok=True)
    test_cases = [
        LLMTestCase(input=item.input_text, actual_output=item.actual_output) for item in cases
    ]
    metric = build_metric(method_key, judge, threshold=threshold)
    result = evaluate(
        test_cases=test_cases,
        metrics=[metric],
        async_config=AsyncConfig(run_async=False),
        display_config=DisplayConfig(
            print_results=True,
            show_indicator=False,
            results_folder=folder.as_posix(),
            file_type="html",
            file_output_dir=folder.as_posix(),
            inspect_after_run=False,
        ),
    )
    rows: list[dict] = []
    for index, test_result in enumerate(getattr(result, "test_results", []) or []):
        label = cases[index].label if index < len(cases) else str(index)
        datas = getattr(test_result, "metrics_data", None) or []
        if not datas:
            rows.append({"label": label, "score": 0.0, "reason": "", "success": False})
            continue
        data = datas[0]
        rows.append(
            {
                "label": label,
                "metric": _metric_name(data),
                "score": float(getattr(data, "score", 0) or 0),
                "reason": str(getattr(data, "reason", "") or ""),
                "success": bool(getattr(data, "success", False)),
            }
        )
    html_path, json_path = _dashboard_files(folder)
    return EvalOutcome(
        scores=rows,
        dashboard_html=html_path,
        test_run_json=json_path,
        judge_usage=_judge_usage(judge, metric),
    )


def _judge_usage(judge: Any, metric: Any) -> list[dict]:
    model_name = ""
    getter = getattr(judge, "get_model_name", None)
    if callable(getter):
        model_name = str(getter() or "")
    return [
        {
            "model": model_name,
            "input_tokens": int(getattr(metric, "input_tokens", 0) or 0),
            "output_tokens": int(getattr(metric, "output_tokens", 0) or 0),
        }
    ]
