from __future__ import annotations

import pathlib
import re

import pytest

from django.urls import Resolver404, resolve

pytestmark = pytest.mark.unit

NL = chr(10)
REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
FRONTEND_SRC = REPO_ROOT / "frontend" / "src"
TESTS_DIR = REPO_ROOT / "tests"
YAML_CASE_DIR = TESTS_DIR / "api" / "case"

API_BASE = "/api"

_QUOTES = "\"'`"

_CALL_RX = re.compile(
    r"\.(get|post|put|patch|delete)\s*(?:<[^<>()]*>)?\s*\(\s*f?(["
    + _QUOTES
    + r"])((?:[^"
    + _QUOTES
    + r"])*)\2",
    re.S,
)

_API_IN_LITERAL_RX = re.compile(r"/api/[A-Za-z0-9_\-/{}.:]*")

_YAML_PATH_RX = re.compile(r"^\s*(?:-\s*)?path:\s*[\"']?([^\"'\s]+)")

NON_API_PREFIXES = ("/login", "/dashboard")

EXCEPTIONS = (
    (
        "tests/arch/unit/test_api_path_convention.py",
        "/api/auth/login",
        "该用例断言的就是“缺失尾斜杠返回 404”，必须是违规写法",
    ),
)

MIN_PER_SURFACE = {
    "frontend": 42,
    "tests": 32,
    "yaml": 42,
}

AUTH_VIEW_BY_PATH = {
    "/api/auth/login/": "LoginView",
    "/api/auth/register/": "RegisterView",
    "/api/auth/refresh/": "RefreshView",
    "/api/auth/logout/": "LogoutView",
    "/api/auth/me/": "MeView",
}
AUTH_CALL_FILES = (
    "frontend/src/shared/api/auth.ts",
    "frontend/src/shared/api-client.ts",
    "tests/api/conftest.py",
)


class Caller:
    def __init__(
        self,
        surface: str,
        file: pathlib.Path,
        call_line: int,
        line: int,
        path: str,
        method: str | None = None,
    ) -> None:
        self.surface = surface
        self.file = file
        self.call_line = call_line
        self.line = line
        self.path = path
        self.method = method

    @property
    def rel(self) -> str:
        return self.file.relative_to(REPO_ROOT).as_posix()

    @property
    def multiline(self) -> bool:
        return self.call_line != self.line

    @property
    def full_path(self) -> str:
        path = self.path
        if not path.startswith(API_BASE + "/"):
            path = API_BASE + path
        path = re.sub(r"\$\{[^}]*\}", "1", path)
        return re.sub(r"\{[^}]*\}", "1", path)

    @property
    def where(self) -> str:
        return f"{self.rel}:{self.line}  {self.path}"


def _line_of(text: str, offset: int) -> int:
    return text[:offset].count(NL) + 1


def _scan_call_sites(surface: str, files) -> list[Caller]:
    found: list[Caller] = []
    for source in files:
        text = source.read_text(encoding="utf-8", errors="replace")
        for match in _CALL_RX.finditer(text):
            literal = match.group(3)
            if surface == "frontend":
                if not literal.startswith("/") or literal.startswith(NON_API_PREFIXES):
                    continue
                path = literal
            else:
                hit = _API_IN_LITERAL_RX.search(literal)
                if not hit:
                    continue
                path = hit.group(0)
            found.append(
                Caller(
                    surface=surface,
                    file=source,
                    call_line=_line_of(text, match.start()),
                    line=_line_of(text, match.start(3)),
                    path=path,
                    method=match.group(1),
                )
            )
    return found


def _scan_yaml_case_paths() -> list[Caller]:
    found: list[Caller] = []
    for source in sorted(YAML_CASE_DIR.glob("*.yaml")):
        for index, line in enumerate(source.read_text(encoding="utf-8").splitlines(), 1):
            match = _YAML_PATH_RX.match(line)
            if match and match.group(1).startswith("/"):
                found.append(Caller("yaml", source, index, index, match.group(1)))
    return found


def _collect_callers() -> list[Caller]:
    frontend = sorted(p for p in FRONTEND_SRC.rglob("*") if p.suffix in (".ts", ".vue"))
    tests = sorted(p for p in TESTS_DIR.rglob("*.py"))
    return (
        _scan_call_sites("frontend", frontend)
        + _scan_call_sites("tests", tests)
        + _scan_yaml_case_paths()
    )


CALLERS = _collect_callers()


def _is_excepted(caller: Caller) -> bool:
    for rel, literal, _reason in EXCEPTIONS:
        if caller.rel == rel and caller.path == literal:
            return True
    return False


def test_scanner_finds_the_expected_volume():
    actual = {}
    for caller in CALLERS:
        actual[caller.surface] = actual.get(caller.surface, 0) + 1
    shortfalls = [
        f"{surface}: 扫到 {actual.get(surface, 0)} 条，低于登记下限 {minimum}"
        for surface, minimum in MIN_PER_SURFACE.items()
        if actual.get(surface, 0) < minimum
    ]
    assert shortfalls == [], (
        "扫描量不足，请检查 _CALL_RX / _YAML_PATH_RX 与面清单，"
        "而不是直接调低下限：" + NL + NL.join(f"  - {item}" for item in shortfalls)
    )


def test_multiline_call_sites_are_captured():
    multiline = [c for c in CALLERS if c.multiline]
    assert multiline, "一条跨行调用都没扫到，说明扫描器退化成了按行匹配"
    assert any(c.rel == "tests/api/conftest.py" for c in multiline), (
        "tests/api/conftest.py 的跨行调用未被扫到："
        + NL
        + NL.join(f"  - {c.rel}:{c.line}" for c in multiline)
    )
    assert any(c.rel.endswith("task-list/api/tasks.ts") for c in multiline), (
        "前端跨行调用未被扫到（task-list/api/tasks.ts）"
    )


def test_exception_list_entries_are_real():
    stale = []
    for rel, literal, reason in EXCEPTIONS:
        if not reason.strip():
            stale.append(f"{rel} 的例外缺理由：{literal}")
        if not any(c.rel == rel and c.path == literal for c in CALLERS):
            stale.append(f"{rel} 中已找不到该字面量：{literal}")
    assert stale == [], "例外清单失效：" + NL + NL.join(f"  - {s}" for s in stale)


def test_auth_chain_is_covered_by_the_scan():
    covered = {c.rel for c in CALLERS if c.rel in AUTH_CALL_FILES}
    assert covered == set(AUTH_CALL_FILES), (
        "认证链路有文件没被扫到："
        + NL
        + NL.join(f"  - {p}" for p in sorted(set(AUTH_CALL_FILES) - covered))
    )


def test_every_caller_path_ends_with_slash():
    bad = [c.where for c in CALLERS if not c.path.endswith("/") and not _is_excepted(c)]
    assert bad == [], (
        "以下调用方缺尾斜杠（约定见 openspec/specs/api-path-convention）："
        + NL
        + NL.join(f"  - {item}" for item in bad)
    )


def test_every_caller_path_resolves_to_a_view():
    failures = []
    for caller in CALLERS:
        if _is_excepted(caller):
            continue
        try:
            resolve(caller.full_path)
        except Resolver404:
            failures.append(f"{caller.where}  →  resolve({caller.full_path!r}) 无匹配路由")
    assert failures == [], (
        "以下调用在后端不存在对应路由：" + NL + NL.join(f"  - {item}" for item in failures)
    )


def test_scanner_records_http_methods():
    by_method = {}
    for caller in CALLERS:
        if caller.method:
            by_method[caller.method] = by_method.get(caller.method, 0) + 1
    missing = [verb for verb in ("get", "post", "patch") if not by_method.get(verb)]
    assert missing == [], (
        "以下动词一个调用点都没扫到，说明 _CALL_RX 的动词捕获组退化了：" + ", ".join(missing)
    )


def test_every_caller_method_is_accepted_by_the_matched_view():
    failures = []
    for caller in CALLERS:
        if caller.method is None or _is_excepted(caller):
            continue
        try:
            match = resolve(caller.full_path)
        except Resolver404:
            continue
        actions = getattr(match.func, "actions", None)
        if not actions:
            continue
        if caller.method not in actions:
            failures.append(
                f"{caller.where}  {caller.method.upper()} → {match.func.cls.__name__} "
                f"仅接受 {sorted(actions)}"
            )
    assert failures == [], (
        "以下调用的方法不会被命中的视图受理（最终表现为 405）："
        + NL
        + NL.join(f"  - {item}" for item in failures)
    )


def test_auth_chain_resolves_to_expected_views():
    mismatches = []
    for path, view_name in AUTH_VIEW_BY_PATH.items():
        try:
            actual = resolve(path).func.view_class.__name__
        except (Resolver404, AttributeError) as exc:
            mismatches.append(f"{path}  →  {type(exc).__name__}")
            continue
        if actual != view_name:
            mismatches.append(f"{path}  →  {actual}（期望 {view_name}）")
    assert mismatches == [], (
        "认证链路路径与视图对不上：" + NL + NL.join(f"  - {item}" for item in mismatches)
    )
