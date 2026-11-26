from __future__ import annotations

import json
import tempfile
import time

from pathlib import Path

import pytest

from tests.perf.page_load import measure_path, median, summarize

pytestmark = pytest.mark.perf

BUDGET_KEYS = {
    "lcp": "lcp_ms",
    "load": "load_ms",
    "transfer_kb": "transfer_kb",
    "requests": "requests",
}


def _write_report(target: Path, payload: dict) -> Path:
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    stamp = time.strftime("%H%M%S")
    candidates = (
        target,
        target.with_name(f"{target.stem}.{stamp}{target.suffix}"),
    )
    for candidate in candidates:
        try:
            candidate.write_text(text, encoding="utf-8")
            return candidate
        except PermissionError:
            continue
    fallback = Path(tempfile.gettempdir()) / f"{target.stem}.{stamp}{target.suffix}"
    fallback.write_text(text, encoding="utf-8")
    return fallback


def _round(value):
    return None if value is None else round(value, 1)


@pytest.mark.parametrize("path", ["/login", "/dashboard"])
def test_page_load_budget(path, perf_session, perf_report_dir):
    budgets = perf_session["budgets"]
    if path not in budgets:
        pytest.skip(f"profile {perf_session['profile']} 未登记 {path} 的预算")

    if perf_session.get("warmup"):
        measure_path(
            perf_session["browser"],
            perf_session["base_url"],
            path,
            perf_session["warmup"],
            perf_session["settle_ms"],
            perf_session["tokens"],
        )

    rows = measure_path(
        perf_session["browser"],
        perf_session["base_url"],
        path,
        perf_session["runs"],
        perf_session["settle_ms"],
        perf_session["tokens"],
    )
    summary = summarize(rows)
    budget = budgets[path]

    report = {
        "path": path,
        "profile": perf_session["profile"],
        "base_url": perf_session["base_url"],
        "runs": perf_session["runs"],
        "warmup": perf_session.get("warmup", 0),
        "settle_ms": perf_session["settle_ms"],
        "budget": budget,
        "summary": summary,
        "checks": {
            metric: {"actual": _round(median(rows, metric)), "budget": budget[key]}
            for metric, key in BUDGET_KEYS.items()
        },
        "rows": rows,
    }
    target = perf_report_dir / f"page-load-{path.strip('/') or 'root'}.json"
    target = _write_report(target, report)

    rendered = min(row.get("renderedChars") or 0 for row in rows)
    assert rendered > 0, (
        f"{path} 未渲染出内容（renderedChars=0）：前 3 条 page_errors={rows[0].get('page_errors')}；"
        "dev server 常见原因是 504 Outdated Optimize Dep，需清 frontend/node_modules/.vite 后重启"
    )

    failures: list[str] = []
    for metric, key in BUDGET_KEYS.items():
        actual = median(rows, metric)
        if actual is None:
            failures.append(f"{metric}: 未采集到样本")
            continue
        if actual > budget[key]:
            failures.append(f"{metric}: {actual:.0f} > 预算 {budget[key]}")

    assert not failures, (
        f"{path} 超出加载预算（profile={perf_session['profile']}, runs={perf_session['runs']}）："
        + "；".join(failures)
        + f"；明细见 {target}"
    )
