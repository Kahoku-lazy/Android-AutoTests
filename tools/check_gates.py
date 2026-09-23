"""本地质量门禁执行器。

检查项与 `.github/workflows/ci-phase1.yml` 一一对应：让本地（或任何没有 CI 的环境）
能跑完与 CI 同一批检查。命令、目录、分级均以 CI 原文为准。

用法:
    python run.py check          # 推荐入口
    python tools/check_gates.py  # 直接运行
    python tools/check_gates.py --only silent-except   # 只跑指定门禁（供 CI 调用）

退出码:
    0  全部阻塞项通过（告警项失败不影响退出码）
    1  存在阻塞项失败
"""

from __future__ import annotations

import argparse
import ast
import os
import re
import subprocess
import sys

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parent.parent
FRONTEND = ROOT / "frontend"
IS_WIN = sys.platform == "win32"

NPM = "npm.cmd" if IS_WIN else "npm"
NPX = "npx.cmd" if IS_WIN else "npx"

# CI 中 ruff 的作用域（既有拦截型步骤）
PY_SCOPES = ["apps/", "config/", "gateway/", "shared/", "models/"]
# 走查文件时跳过的目录：不改变判定口径，只是避免扫进依赖与缓存
SKIP_DIRS = {"node_modules", "__pycache__", ".venv", "venv", "dist", ".git", ".pytest_cache"}

TAIL_LINES = 20
INLINE_STYLE_LIMIT = 120


@dataclass(frozen=True)
class Gate:
    """一项检查。run() 返回 (是否通过, 输出行)。"""

    name: str
    desc: str
    blocking: bool
    run: Callable[[], "tuple[bool, list[str]]"]
    always_show: bool = False


# ── 执行器 ────────────────────────────────────────────────────


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
    if extra:
        env.update(extra)
    return env


def cmd_gate(
    name: str,
    desc: str,
    cmd: list[str],
    blocking: bool,
    cwd: Path = ROOT,
    env: dict[str, str] | None = None,
) -> Gate:
    """按外部命令判定：退出码 0 为通过。命令不存在按失败处理（不静默跳过）。"""

    def _run() -> tuple[bool, list[str]]:
        try:
            proc = subprocess.run(
                cmd,
                cwd=str(cwd),
                env=_env(env),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
        except FileNotFoundError:
            return False, [f"未找到命令：{cmd[0]}（环境缺失按失败处理，不跳过）"]
        lines = (proc.stdout + proc.stderr).strip().splitlines()
        return proc.returncode == 0, lines[-TAIL_LINES:]

    return Gate(name, desc, blocking, _run)


def _iter_files(roots: list[str], suffixes: set[str]):
    for root in roots:
        base = ROOT / root
        if not base.exists():
            continue
        for path in sorted(base.rglob("*")):
            if not path.is_file() or path.suffix not in suffixes:
                continue
            if SKIP_DIRS & set(path.parts):
                continue
            yield path


def grep_gate(
    name: str,
    desc: str,
    roots: list[str],
    suffixes: set[str],
    pattern: str,
    excludes: tuple[str, ...] = (),
    exclude_patterns: tuple[str, ...] = (),
    blocking: bool = True,
    always_show: bool = False,
) -> Gate:
    """按 CI 内联 grep -rnE 的口径走查：命中且不在排除清单中即为违规。

    excludes 为子串排除（对应 CI 的 `grep -v "xxx"`）；
    exclude_patterns 为行级正则排除（对应 CI 的 `grep -vE "xxx"`）。
    """

    rx = re.compile(pattern, re.ASCII)
    exclude_rx = [re.compile(p, re.ASCII) for p in exclude_patterns]

    def _run() -> tuple[bool, list[str]]:
        hits: list[str] = []
        for path in _iter_files(roots, suffixes):
            text = path.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if not rx.search(line):
                    continue
                if any(token in line for token in excludes):
                    continue
                if any(r.search(line) for r in exclude_rx):
                    continue
                hits.append(f"{path.relative_to(ROOT).as_posix()}:{lineno}:{line.strip()}")
        if always_show:
            # CI 中这类检查只提示、不置违规（如规则 3），故恒为通过
            return True, hits
        return not hits, hits

    return Gate(name, desc, blocking, _run, always_show)


# ── 静默吞异常（AST 检查，非 CI 内联项） ─────────────────────

LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}
# 供应商产物：与 ruff.toml 的 exclude 一致，改了会在下次 skill 更新时丢失
VENDORED = ("engines/ai/skills/skill-creator",)


def _has_log_call(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Attribute) and func.attr in LOG_METHODS:
                return True
    return False


def _handler_has_comment(lines: list[str], node: ast.ExceptHandler) -> bool:
    ends = [n.end_lineno for n in ast.walk(node) if getattr(n, "end_lineno", None)]
    start = node.lineno - 1
    end = max(ends) if ends else start + 1
    return any("#" in line for line in lines[start:end])


def silent_except_gate() -> Gate:
    """禁止「捕获后什么都不做」：处理器体只有 pass/continue/break，且无 raise、无日志、无注释。

    明确选择忽略的情形以注释表达（见 AGENTS.md：错误不应默默忽略，除非明确地选择忽略）。
    """

    def _run() -> tuple[bool, list[str]]:
        findings: list[str] = []
        for path in _iter_files(["apps", "config", "gateway", "shared", "engines"], {".py"}):
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith(VENDORED):
                continue
            if "migrations" in path.parts:
                # 历史迁移不可改（与 ruff.toml 的 exclude 一致）
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            lines = text.splitlines()
            try:
                tree = ast.parse(text)
            except SyntaxError as exc:
                findings.append(f"{rel}: 解析失败 {exc}")
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.ExceptHandler):
                    continue
                if not all(isinstance(s, (ast.Pass, ast.Continue, ast.Break)) for s in node.body):
                    continue
                if any(isinstance(n, ast.Raise) for n in ast.walk(node)):
                    continue
                if _has_log_call(node) or _handler_has_comment(lines, node):
                    continue
                findings.append(f"{rel}:{node.lineno}: {lines[node.lineno - 1].strip()}")
        return not findings, findings

    return Gate(
        "silent-except",
        "静默吞异常（捕获后什么都不做且无注释说明）",
        blocking=True,
        run=_run,
    )


def inline_style_gate() -> Gate:
    """CI 内联 Python 的等价实现：单文件 <style> 块超过阈值即提示（CI 中不拦截）。"""

    def _run() -> tuple[bool, list[str]]:
        issues: list[str] = []
        for path in _iter_files(["frontend/src/modules"], {".vue"}):
            content = path.read_text(encoding="utf-8", errors="replace")
            match = re.search(r"<style[^>]*>", content)
            if not match:
                continue
            start = content[: match.start()].count("\n")
            end = content[match.end() :].find("</style>")
            if end < 0:
                continue
            style_end = start + content[match.end() : match.end() + end].count("\n") + 1
            size = style_end - start
            if size > INLINE_STYLE_LIMIT:
                rel = path.relative_to(ROOT).as_posix()
                issues.append(f"{rel}: {size}行内联样式 (建议外置)")
        return True, issues

    return Gate(
        "inline-style",
        f"内联样式体积（>{INLINE_STYLE_LIMIT} 行，CI 中仅提示）",
        False,
        _run,
        always_show=True,
    )


# ── 检查清单（对应 CI 的 6 个 job） ───────────────────────────


def build_gates() -> list[Gate]:
    py = sys.executable
    return [
        # Job 1 backend-check
        cmd_gate(
            "django-check",
            "Django 系统检查",
            [py, "manage.py", "check"],
            blocking=True,
            env={"DJANGO_SECRET_KEY": "local-check-key-not-for-prod"},
        ),
        cmd_gate(
            "ruff-format",
            "Python 格式（ruff format，平台范围）",
            [py, "-m", "ruff", "format", "--check", *PY_SCOPES],
            blocking=True,
        ),
        cmd_gate(
            "ruff-lint",
            "Python lint（ruff check，平台范围）",
            [py, "-m", "ruff", "check", *PY_SCOPES],
            blocking=True,
        ),
        # Job 2 frontend-check
        cmd_gate("vitest", "前端单元测试（P0/P1）", [NPM, "test"], blocking=True, cwd=FRONTEND),
        cmd_gate("vite-build", "前端构建", [NPX, "vite", "build"], blocking=True, cwd=FRONTEND),
        cmd_gate(
            "prettier",
            "前端格式（prettier，vue/js/css）",
            [NPX, "prettier", "--check", "src/**/*.{vue,js,css}"],
            blocking=True,
            cwd=FRONTEND,
        ),
        # Job 6 static-checks（原告警项，2026-09-23 起转为拦截）
        cmd_gate(
            "ruff-engines-format",
            "Python 格式（engines/）",
            [py, "-m", "ruff", "format", "--check", "engines/"],
            blocking=True,
        ),
        cmd_gate(
            "ruff-engines-lint",
            "Python lint（engines/）",
            [py, "-m", "ruff", "check", "engines/"],
            blocking=True,
        ),
        cmd_gate("eslint", "前端代码检查（eslint）", [NPM, "run", "lint"], True, FRONTEND),
        cmd_gate(
            "vue-tsc",
            "前端类型检查（vue-tsc）",
            [NPM, "run", "typecheck"],
            blocking=True,
            cwd=FRONTEND,
        ),
        cmd_gate(
            "prettier-ts",
            "前端格式（prettier，.ts）",
            [NPX, "prettier", "--check", "src/**/*.ts"],
            blocking=True,
            cwd=FRONTEND,
        ),
        # Job 3 security-scan（规则 3 在 CI 中仅提示，不置违规）
        grep_gate(
            "cred-password",
            "硬编码密码",
            PY_SCOPES,
            {".py"},
            r"password\s*=\s*'[^']+'",
            excludes=(r"password\s*=\s*''", "PASSWORD"),
        ),
        grep_gate(
            "cred-apikey",
            "明文 API Key",
            PY_SCOPES[:-1],
            {".py"},
            r"(api_key|apikey|API_KEY)\s*=\s*'sk-[A-Za-z0-9]+'",
        ),
        grep_gate(
            "cred-default-pwd",
            "常见默认密码（CI 中仅提示）",
            PY_SCOPES[:-1],
            {".py"},
            r"'admin123'|'autotests2026'|'password'\s*[:=]",
            excludes=("PASSWORD", "test", "__pycache__"),
            blocking=False,
            always_show=True,
        ),
        grep_gate(
            "cred-secret",
            "硬编码 Token/Secret",
            PY_SCOPES[:-1],
            {".py"},
            r"(secret_key|SECRET_KEY|private_key)\s*=\s*'[^']+'",
            excludes=("os.environ", "getenv"),
        ),
        grep_gate(
            "cred-frontend",
            "前端硬编码凭据",
            ["frontend/src"],
            {".js", ".vue"},
            r"(api_key|password|token|secret)\s*[=:]\s*['\"]\w{8,}",
            excludes=("node_modules", ".test."),
            # 排除 Vue 属性绑定（v-model:password / :token）与属性访问、连字符命名前缀，
            # 与 CI security-scan 规则 5 的 `grep -vE` 保持同一口径
            exclude_patterns=(r"[:.\-](api_key|password|token|secret)\s*[=:]",),
        ),
        # Job 4 boundary-check
        cmd_gate(
            "boundary",
            "模块边界检查（防火墙 #1/#2）",
            [py, "tools/gen_arch_stats.py", "--check-boundaries"],
            blocking=True,
            env={"DJANGO_SECRET_KEY": "local-check-key-not-for-prod"},
        ),
        # Job 5 frontend-quality
        cmd_gate(
            "vue-file-size",
            "Vue 文件体积（<500 行）",
            [py, "tools/gen_arch_stats.py", "--check-frontend"],
            blocking=True,
        ),
        grep_gate(
            "mock-data",
            "前端硬编码假数据",
            ["frontend/src/modules"],
            {".vue"},
            r"ref\(\s*\[\s*\{[^}]*id:",
        ),
        inline_style_gate(),
        # 本次新增（不在 CI 内联项中）
        silent_except_gate(),
    ]


# ── 主流程 ────────────────────────────────────────────────────


def main() -> int:
    # Windows 控制台默认 GBK，而被检查工具会输出非 GBK 字符（如 vitest 的 ❯）→ 统一切到 UTF-8
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    parser = argparse.ArgumentParser(description="本地质量门禁执行器")
    parser.add_argument("--only", default="", help="只运行指定门禁，逗号分隔（供 CI 单独调用某项）")
    args = parser.parse_args()

    gates = build_gates()
    if args.only:
        wanted = {name.strip() for name in args.only.split(",") if name.strip()}
        known = {gate.name for gate in gates}
        unknown = wanted - known
        if unknown:
            print(f"未知门禁：{', '.join(sorted(unknown))}")
            print(f"可用门禁：{', '.join(sorted(known))}")
            return 2
        gates = [gate for gate in gates if gate.name in wanted]

    results: list[tuple[Gate, bool, list[str]]] = []
    for gate in gates:
        ok, lines = gate.run()
        results.append((gate, ok, lines))

    print("=" * 62)
    print("  本地质量门禁")
    print("=" * 62)
    for gate, ok, lines in results:
        if lines and (not ok or gate.always_show):
            print(f"\n── {gate.desc} ──")
            for line in lines:
                print(f"   {line}")

    print("\n" + "=" * 62)
    blocking_failed = 0
    advisory_failed = 0
    for gate, ok, _ in results:
        mark = "PASS" if ok else ("FAIL" if gate.blocking else "WARN")
        if not ok:
            if gate.blocking:
                blocking_failed += 1
            else:
                advisory_failed += 1
        print(f"  {mark}  {gate.name:<22} {gate.desc}")

    passed_blocking = sum(1 for g, ok, _ in results if g.blocking and ok)
    passed_advisory = sum(1 for g, ok, _ in results if not g.blocking and ok)
    total_blocking = sum(1 for g, _, _ in results if g.blocking)
    total_advisory = len(results) - total_blocking

    print("=" * 62)
    print(f"  阻塞项 {passed_blocking}/{total_blocking} 通过，{blocking_failed} 失败")
    print(
        f"  告警项 {passed_advisory}/{total_advisory} 通过，{advisory_failed} 未通过（不影响退出码）"
    )
    print("=" * 62)
    return exit_code(results)


def exit_code(results: "list[tuple[Gate, bool, list[str]]]") -> int:
    """退出码只由阻塞项决定：有阻塞项失败返回 1，否则返回 0。"""
    return 1 if any(gate.blocking and not ok for gate, ok, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main())
