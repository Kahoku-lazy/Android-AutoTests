"""本地质量门禁执行器。

检查项与 `.github/workflows/ci-phase1.yml` 一一对应：让本地（或任何没有 CI 的环境）
能跑完与 CI 同一批检查。命令、目录、分级均以 CI 原文为准。

用法:
    python run.py check          # 推荐入口
    python tools/check_gates.py  # 直接运行

退出码:
    0  全部阻塞项通过（告警项失败不影响退出码）
    1  存在阻塞项失败
"""

from __future__ import annotations

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
    blocking: bool = True,
    always_show: bool = False,
) -> Gate:
    """按 CI 内联 grep -rnE 的口径走查：命中且不在排除清单中即为违规。"""

    rx = re.compile(pattern, re.ASCII)

    def _run() -> tuple[bool, list[str]]:
        hits: list[str] = []
        for path in _iter_files(roots, suffixes):
            text = path.read_text(encoding="utf-8", errors="replace")
            for lineno, line in enumerate(text.splitlines(), start=1):
                if not rx.search(line):
                    continue
                if any(token in line for token in excludes):
                    continue
                hits.append(f"{path.relative_to(ROOT).as_posix()}:{lineno}:{line.strip()}")
        if always_show:
            # CI 中这类检查只提示、不置违规（如规则 3），故恒为通过
            return True, hits
        return not hits, hits

    return Gate(name, desc, blocking, _run, always_show)


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
        # Job 6 advisory-checks（本次接入 CI 的告警项）
        cmd_gate(
            "ruff-engines-format",
            "Python 格式（engines/，仅告警）",
            [py, "-m", "ruff", "format", "--check", "engines/"],
            blocking=False,
        ),
        cmd_gate(
            "ruff-engines-lint",
            "Python lint（engines/，仅告警）",
            [py, "-m", "ruff", "check", "engines/"],
            blocking=False,
        ),
        cmd_gate("eslint", "前端代码检查（eslint，仅告警）", [NPM, "run", "lint"], False, FRONTEND),
        cmd_gate(
            "vue-tsc",
            "前端类型检查（vue-tsc，仅告警）",
            [NPM, "run", "typecheck"],
            blocking=False,
            cwd=FRONTEND,
        ),
        cmd_gate(
            "prettier-ts",
            "前端格式（prettier，.ts，仅告警）",
            [NPX, "prettier", "--check", "src/**/*.ts"],
            blocking=False,
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
    ]


# ── 主流程 ────────────────────────────────────────────────────


def main() -> int:
    # Windows 控制台默认 GBK，而被检查工具会输出非 GBK 字符（如 vitest 的 ❯）→ 统一切到 UTF-8
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")

    gates = build_gates()
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
