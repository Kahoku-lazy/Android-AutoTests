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

PY_SCOPES = [
    "backend/apps/",
    "backend/config/",
    "backend/gateway/",
    "backend/shared/",
    "backend/models/",
]
RUFF_SCOPES = [*PY_SCOPES, "tests/"]
SKIP_DIRS = {"node_modules", "__pycache__", ".venv", "venv", "dist", ".git", ".pytest_cache"}

TAIL_LINES = 20
INLINE_STYLE_LIMIT = 120


@dataclass(frozen=True)
class Gate:
    name: str
    desc: str
    blocking: bool
    run: Callable[[], "tuple[bool, list[str]]"]
    always_show: bool = False


def _env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    env.setdefault("DJANGO_SETTINGS_MODULE", "backend.config.settings")
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
            return True, hits
        return not hits, hits

    return Gate(name, desc, blocking, _run, always_show)


LOG_METHODS = {"debug", "info", "warning", "warn", "error", "exception", "critical", "log"}
VENDORED = ()


def _has_log_call(node: ast.AST) -> bool:
    for child in ast.walk(node):
        if isinstance(child, ast.Call):
            func = child.func
            if isinstance(func, ast.Attribute) and func.attr in LOG_METHODS:
                return True
    return False


def _handler_has_marker(lines: list[str], node: ast.ExceptHandler) -> bool:
    ends = [n.end_lineno for n in ast.walk(node) if getattr(n, "end_lineno", None)]
    start = node.lineno - 1
    end = max(ends) if ends else start + 1
    return any("silent-except" in line or "noqa" in line for line in lines[start:end])


def silent_except_gate() -> Gate:
    def _run() -> tuple[bool, list[str]]:
        findings: list[str] = []
        for path in _iter_files(["apps", "config", "gateway", "shared", "engines"], {".py"}):
            rel = path.relative_to(ROOT).as_posix()
            if rel.startswith(VENDORED):
                continue
            if "migrations" in path.parts:
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
                if _has_log_call(node) or _handler_has_marker(lines, node):
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


OPENAPI_BASELINE = ROOT / "openspec" / "openapi.yaml"
OPENAPI_GENERATED = ROOT / "temps" / "openapi.generated.yaml"
MODEL_KEY_ENV = {
    "DEEPSEEK_API_KEY": "local-collect-placeholder",
    "DASHSCOPE_API_KEY": "local-collect-placeholder",
    "OPENAI_API_KEY": "local-collect-placeholder",
}
OPENAPI_ENV = {
    "DJANGO_SECRET_KEY": "local-check-key-not-for-prod",
    **MODEL_KEY_ENV,
}


def openapi_schema_gate() -> Gate:
    def _run() -> tuple[bool, list[str]]:
        OPENAPI_GENERATED.parent.mkdir(parents=True, exist_ok=True)
        proc = subprocess.run(
            [
                sys.executable,
                "-m",
                "manage",
                "spectacular",
                "--file",
                str(OPENAPI_GENERATED),
                "--validate",
                "--fail-on-warn",
            ],
            cwd=str(ROOT),
            env=_env(OPENAPI_ENV),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        lines = (proc.stdout + proc.stderr).strip().splitlines()[-TAIL_LINES:]
        if proc.returncode != 0:
            return False, ["OpenAPI 生成或校验失败：", *lines]
        if not OPENAPI_BASELINE.exists():
            return False, [
                f"缺少契约基线 {OPENAPI_BASELINE.relative_to(ROOT)}",
                "首次生成：python -m manage spectacular --file openspec/openapi.yaml --validate --fail-on-warn",
            ]
        if _openapi_text(OPENAPI_GENERATED) != _openapi_text(OPENAPI_BASELINE):
            return False, [
                "OpenAPI 与基线不一致：接口改了但基线没更新",
                "更新基线：python -m manage spectacular --file openspec/openapi.yaml --validate --fail-on-warn",
                "（基线变更要随本次接口改动一起提交）",
            ]
        return True, ["OpenAPI 与基线一致"]

    return Gate("openapi-schema", "OpenAPI 契约（生成 + 校验 + 基线一致）", True, _run)


def _openapi_text(path: Path) -> str:
    return path.read_text(encoding="utf-8").replace("\r\n", "\n")


BUSINESS_ASSET_DIRS = (ROOT / "engines" / "agents" / "config" / "data" / "app_info",)
FORBIDDEN_ASSET_PATHS = (
    "engines/agents/config/data/app_info/govee_home.md",
    "engines/ae_harness/workflow/sop/steps/govee_widget.yaml",
)
RESTRICTED_VENDOR_TOKENS = ("govee",)


def business_asset_gate() -> Gate:
    def run() -> "tuple[bool, list[str]]":
        lines: list[str] = []
        for rel in FORBIDDEN_ASSET_PATHS:
            if (ROOT / rel).exists():
                lines.append(f"{rel}：已禁用资产路径重新出现")
        for directory in BUSINESS_ASSET_DIRS:
            if not directory.is_dir():
                continue
            for path in sorted(directory.rglob("*")):
                if not path.is_file():
                    continue
                try:
                    rel = path.relative_to(ROOT).as_posix()
                except ValueError:
                    rel = path.as_posix()
                body = path.read_text(encoding="utf-8", errors="ignore").lower()
                for token in RESTRICTED_VENDOR_TOKENS:
                    if token in rel.lower() or token in body:
                        lines.append(f"{rel}：命中受限厂商标识")
                        break
        return (not lines, lines)

    return Gate(
        "business-asset",
        "业务资产（受管目录禁厂商标识 / 禁用路径不复活）",
        blocking=True,
        run=run,
    )


AGENT_CONSTRUCTOR_FILE = "engines/ae_harness/agents/creator.py"


def single_agent_constructor_gate() -> Gate:
    def _run() -> tuple[bool, list[str]]:
        hits: list[str] = []
        for path in _iter_files(["engines"], {".py"}):
            rel = path.relative_to(ROOT).as_posix()
            text = path.read_text(encoding="utf-8", errors="replace")
            try:
                tree = ast.parse(text)
            except SyntaxError as exc:
                hits.append(f"{rel}: 解析失败 {exc}")
                continue
            for node in ast.walk(tree):
                if not isinstance(node, ast.Call):
                    continue
                func = node.func
                if not isinstance(func, ast.Name) or func.id != "Agent":
                    continue
                if rel == AGENT_CONSTRUCTOR_FILE:
                    continue
                hits.append(f"{rel}:{node.lineno}: 直接构造 Agent，必须改走 create_agent")
        return not hits, hits

    return Gate(
        "single-agent-constructor",
        "Agent 只在 creator.py 构造（其余位置走 create_agent）",
        blocking=True,
        run=_run,
    )


RETIRE_PHASE = {
    "reverse_dependency": True,
    "knowledge_assistant": True,
    "agents_package": True,
}

_BASE_PKG_AGENT_IMPORT = re.compile(
    r"^\s*(?:from|import)\s+engines\.(?:agents|backend_bridge|ae_harness)\b"
)
_ENGINES_AGENTS_IMPORT = re.compile(r"^\s*(?:from|import)\s+engines\.agents\b")

KNOWLEDGE_ASSISTANT_PATHS = (
    "backend/apps/knowledge_assistant",
    "frontend/src/modules/knowledge-assistant",
)


def _import_hits(root: str, pattern: re.Pattern[str]) -> "list[str]":
    hits: list[str] = []
    for path in _iter_files([root], {".py"}):
        rel = path.relative_to(ROOT).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        for lineno, line in enumerate(text.splitlines(), start=1):
            if pattern.match(line):
                hits.append(f"{rel}:{lineno}: {line.strip()}")
    return hits


def engines_agents_retirement_gate() -> Gate:
    def run() -> "tuple[bool, list[str]]":
        lines: list[str] = []
        if RETIRE_PHASE["reverse_dependency"]:
            for root in ("engines/device", "engines/vision", "engines/uart_log"):
                lines.extend(_import_hits(root, _BASE_PKG_AGENT_IMPORT))
        if RETIRE_PHASE["knowledge_assistant"]:
            for rel in KNOWLEDGE_ASSISTANT_PATHS:
                if (ROOT / rel).exists():
                    lines.append(f"{rel}：该产品面已下线，目录不得存在")
        if RETIRE_PHASE["agents_package"]:
            if (ROOT / "engines" / "agents").exists():
                lines.append("engines/agents：包已退役，目录不得存在")
            for root in ("engines", "backend", "tests", "utils"):
                lines.extend(_import_hits(root, _ENGINES_AGENTS_IMPORT))
        return (not lines, lines)

    return Gate(
        "engines-agents-retirement",
        "Agent 退役（底座不反向依赖 / 下线面无残留 / 旧包不复活）",
        blocking=True,
        run=run,
    )


def build_gates() -> list[Gate]:
    py = sys.executable
    return [
        cmd_gate(
            "django-check",
            "Django 系统检查",
            [py, "-m", "manage", "check"],
            blocking=True,
            env={"DJANGO_SECRET_KEY": "local-check-key-not-for-prod"},
        ),
        cmd_gate(
            "ruff-format",
            "Python 格式（ruff format，平台+tests）",
            [py, "-m", "ruff", "format", "--check", *RUFF_SCOPES],
            blocking=True,
        ),
        cmd_gate(
            "ruff-lint",
            "Python lint（ruff check，平台+tests）",
            [py, "-m", "ruff", "check", *RUFF_SCOPES],
            blocking=True,
        ),
        cmd_gate(
            "makemigrations-check",
            "迁移与模型一致（makemigrations --check）",
            [py, "-m", "manage", "makemigrations", "--check", "--dry-run"],
            blocking=True,
            env={"DJANGO_SECRET_KEY": "local-check-key-not-for-prod"},
        ),
        cmd_gate(
            "pytest-collect",
            "Python 测试收集（pytest --collect-only）",
            [py, "-m", "pytest", "-c", "tests/pytest.ini", "--collect-only", "-q"],
            blocking=True,
            env={
                "DJANGO_SECRET_KEY": "local-check-key-not-for-prod",
                **MODEL_KEY_ENV,
            },
        ),
        openapi_schema_gate(),
        cmd_gate(
            "openapi-coverage",
            "OpenAPI 覆盖（业务路径必须全部已文档化）",
            [py, "-m", "utils.check_openapi_coverage"],
            blocking=True,
            env=OPENAPI_ENV,
        ),
        cmd_gate("vitest", "前端单元测试（P0/P1）", [NPM, "test"], blocking=True, cwd=FRONTEND),
        cmd_gate("vite-build", "前端构建", [NPX, "vite", "build"], blocking=True, cwd=FRONTEND),
        cmd_gate(
            "bundle-budget",
            "前端体积预算（入口 JS/CSS、最大 chunk、JS 总量 gzip）",
            [py, "utils/check_bundle_budget.py"],
            blocking=True,
        ),
        cmd_gate(
            "prettier",
            "前端格式（prettier，vue/js/css）",
            [NPX, "prettier", "--check", "src/**/*.{vue,js,css}"],
            blocking=True,
            cwd=FRONTEND,
        ),
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
            "dashed-whitelist",
            "前端线型（虚线白名单）",
            [NPM, "run", "lint:lines"],
            blocking=True,
            cwd=FRONTEND,
        ),
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
        cmd_gate(
            "style-gates",
            "前端样式（字号 / 令牌 / 阴影 / 圆角 / 动效）",
            [NPM, "run", "lint:styles"],
            blocking=True,
            cwd=FRONTEND,
        ),
        grep_gate(
            "cred-password",
            "硬编码密码",
            [*PY_SCOPES, "engines"],
            {".py"},
            r"password\s*=\s*'[^']+'",
            excludes=(r"password\s*=\s*''", "PASSWORD"),
        ),
        grep_gate(
            "cred-apikey",
            "明文 API Key",
            [*PY_SCOPES[:-1], "engines"],
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
            [*PY_SCOPES[:-1], "engines"],
            {".py"},
            r"(secret_key|SECRET_KEY|private_key)\s*=\s*'[^']+'",
            excludes=("os.environ", "getenv"),
        ),
        grep_gate(
            "cred-frontend",
            "前端硬编码凭据",
            ["frontend/src"],
            {".js", ".vue", ".ts"},
            r"(api_key|password|token|secret)\s*[=:]\s*['\"]\w{8,}",
            excludes=("node_modules", ".test."),
            exclude_patterns=(r"[:.\-](api_key|password|token|secret)\s*[=:]",),
        ),
        cmd_gate(
            "boundary",
            "模块边界检查（防火墙 #1/#2，import 方向见 linting）",
            [py, "-m", "utils.gen_arch_stats", "--check-boundaries"],
            blocking=True,
            env={"DJANGO_SECRET_KEY": "local-check-key-not-for-prod"},
        ),
        cmd_gate(
            "linting",
            "模块依赖（.linting：19 个模块的允许清单 + 16 条禁止合同）",
            [py, "-m", "utils.linting"],
            blocking=True,
        ),
        cmd_gate(
            "vue-file-size",
            "Vue 文件体积（<500 行）",
            [py, "-m", "utils.gen_arch_stats", "--check-frontend"],
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
        silent_except_gate(),
        business_asset_gate(),
        engines_agents_retirement_gate(),
        single_agent_constructor_gate(),
        cmd_gate(
            "engines-agents-style",
            "engines 风格（tool 命名 / 禁 django·apps import；见 engines-code-style.md）",
            [py, "-m", "scripts.check_engines_agents_style"],
            blocking=False,
            cwd=ROOT / ".agents" / "skills" / "engines-agents-style-check",
        ),
    ]


def main() -> int:
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
    return 1 if any(gate.blocking and not ok for gate, ok, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main())
