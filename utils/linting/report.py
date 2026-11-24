"""
模块功能：➡️ 把检查结果渲染成人类可读文本或 JSON 🏁
Python 调试：➡️ python -m utils.linting.report 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无
🏁
"""

from __future__ import annotations

import json

from utils.linting.model import Report


def render_text(report: Report) -> str:
    """人类可读输出：逐条列链 / 逐条列违规，最后给汇总。"""
    lines = [f"linting：扫描 {report.files_scanned} 个文件，{len(report.contracts)} 条禁止合同"]

    for contract in report.contracts:
        for chain in contract.chains:
            lines.append(f"[FAIL] {contract.name}")
            for hop, file, line in chain:
                lines.append(f"        {hop} ({file}:{line})")
    for item in report.allow_violations:
        rule = "禁止依赖" if item.kind == "forbidden" else "未声明依赖"
        lines.append(
            f"[FAIL] {item.file}:{item.line} {rule} {item.imported}"
            f"（{item.usage_module} → {item.definition_module}）"
        )
    for module_path, declared in report.unused:
        lines.append(f"[UNUSED] {module_path} 声明了未使用的依赖 {declared}")
    for warning in report.warnings:
        lines.append(f"[WARN] {warning}")

    broken = [c for c in report.contracts if not c.kept]
    lines.append(
        f"{'通过' if report.ok else '未通过'}："
        f"{len(report.allow_violations)} 条允许清单违规，"
        f"{len(broken)}/{len(report.contracts)} 条合同被破，"
        f"{len(report.unused)} 条多余依赖"
    )
    return "\n".join(lines)


def render_json(report: Report) -> str:
    """给门禁 / CI 消费的 JSON。"""
    payload = {
        "ok": report.ok,
        "files_scanned": report.files_scanned,
        "allow_violations": [item.__dict__ for item in report.allow_violations],
        "contracts": [
            {
                "slug": contract.slug,
                "name": contract.name,
                "kept": contract.kept,
                "chains": [
                    [{"hop": hop, "file": file, "line": line} for hop, file, line in chain]
                    for chain in contract.chains
                ],
            }
            for contract in report.contracts
        ],
        "unused": [
            {"module": module_path, "dependency": dep} for module_path, dep in report.unused
        ],
        "warnings": report.warnings,
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)
