"""全部调用方与后端路由表的一致性守护（前端 / 测试 / 接口用例）。

为什么要这个测试
----------------
后端自身的路由约定由 `test_api_path_convention.py` 守护，但那只能证明“路由表是对的”。
真正会断的是“调用方拼出来的路径在后端存不存在”。尾斜杠约定收紧时，
认证链路的前端与测试夹具各自漏改一处，而既有测试一个都没发现：

- `tests/api/case/*.yaml` 用的是带斜杠的路径 —— 只测后端；夹具（conftest）不在其覆盖内
- `test_api_path_convention.py` 只遍历 `get_resolver()` —— 也是后端侧
- `tests/e2e` 的登录用例需要凭据 + 运行中的前后端，默认 skip

扫描方式：按“调用形态”扫整份文件，而不是按行
--------------------------------------------
上一版守护逐行匹配“调用 + 字面量”，于是只要两者分处两行就整条漏掉。实测漏了
`tests/api/conftest.py` 的登录路径（正是它本该抓住的违规）与前端 `toolbox.ts` 的两处调用。
本模块把源文件整体读入后用支持跨行的正则匹配，行号由匹配起点反推，
并用 `test_multiline_call_sites_are_captured` 把这个能力钉住。

三个面都参与 resolve 断言
------------------------
前端 API 层、`tests/` 调用面与 `tests/api/case/*.yaml` 三个面**一并**纳入 resolve 断言。
原第四个面「端点资产目录」（`tools/seed_api_endpoints.py`）已随元素定位的 Web/API 两域
整体下线而退役（变更 remove-element-locator-web-api，规格 `api-endpoint-catalog` 已移除），
其扫描分支与规模下限同步删除 —— 面不存在就不留恒为 0 的空面。

规格：`openspec/specs/api-path-convention`。
"""

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

# 前端三种字面量写法的引号：双引号 / 单引号 / 反引号（模板字面量）
_QUOTES = "\"'`"

# 按“调用形态”匹配：动词 + （可选的 TS 泛型）+ 左括号 + 可选 f 前缀 + 第一个引号字面量。
# 不加 re.MULTILINE：让 \s* 能跳过换行，这正是上一版漏扫的修法。
_CALL_RX = re.compile(
    r"\.(?:get|post|put|patch|delete)\s*(?:<[^<>()]*>)?\s*\(\s*f?(["
    + _QUOTES
    + r"])((?:[^"
    + _QUOTES
    + r"])*)\1",
    re.S,
)

# 从字面量里取出 /api/ 开头的片段（Python 测试会写成 f"{base_url}/api/..."）
_API_IN_LITERAL_RX = re.compile(r"/api/[A-Za-z0-9_\-/{}.:]*")

# tests/api/case/*.yaml 的 path: 字段（单行标量，无跨行风险）
_YAML_PATH_RX = re.compile(r"^\s*(?:-\s*)?path:\s*[\"']?([^\"'\s]+)")

# 前端自身的路由，不是后端端点
NON_API_PREFIXES = ("/login", "/dashboard")

# 显式例外：三元组 (相对路径, 字面量, 理由)。
# 不用行号（会漂），不用整文件白名单（等于关掉该文件）。
EXCEPTIONS = (
    (
        "tests/graybox/unit/test_api_path_convention.py",
        "/api/auth/login",
        "该用例断言的就是“缺失尾斜杠返回 404”，必须是违规写法",
    ),
)

# 各面的规模下限（后方为实测值，下限取 ~95%）。
# 识别规则退化时计数骤降，测试随即失败，而不是给出虚假的“全部一致”。
MIN_PER_SURFACE = {
    "frontend": 83,  # 实测 88（变更 remove-element-locator-web-api：本变更自身贡献 111→102，元素定位 6 + workflow 2 + pageCatalog 1 = 9 个被扫到的调用点；其后**并发会话**继续改写 frontend/src，实测进一步降至 88，故按 apply 当下实测重登记。非扫描器退化）
    "tests": 32,  # 实测 34（本变更改写两个 element_locator 测试删去 2 个字面量调用点；其余下降来自并发会话对 tests/ 的改动）
    "yaml": 42,  # 实测 45
}

# 认证链路：本守护最初要解决的问题，单独钉住
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
    """一个 HTTP 调用点上的路径字面量。"""

    def __init__(
        self,
        surface: str,
        file: pathlib.Path,
        call_line: int,
        line: int,
        path: str,
    ) -> None:
        self.surface = surface
        self.file = file
        self.call_line = call_line
        self.line = line
        self.path = path

    @property
    def rel(self) -> str:
        return self.file.relative_to(REPO_ROOT).as_posix()

    @property
    def multiline(self) -> bool:
        """调用与字面量是否分处两行 —— 上一版守护正是在这里漏扫。"""
        return self.call_line != self.line

    @property
    def full_path(self) -> str:
        """拼上 baseURL 后的后端路径；动态段换为占位值以便 resolve。

        下位置选 `1`：本仓只用了 `int` 与 `str` 两种转换器，两者都能匹配 "1"。
        """
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
    """扫描一组文件里的 HTTP 调用点。"""
    found: list[Caller] = []
    for source in files:
        text = source.read_text(encoding="utf-8", errors="replace")
        for match in _CALL_RX.finditer(text):
            literal = match.group(2)
            if surface == "frontend":
                # 前端的调用写相对 baseURL 的路径（如 "/auth/login/"），
                # 但 /login、/dashboard 是前端自身路由，不是端点。
                if not literal.startswith("/") or literal.startswith(NON_API_PREFIXES):
                    continue
                path = literal
            else:
                # 测试侧一律带 /api/ 写全路径（或在 f-string 里）。
                # 不能把 "/admin/login/" 这类非 API 路径当成接口。
                hit = _API_IN_LITERAL_RX.search(literal)
                if not hit:
                    continue
                path = hit.group(0)
            found.append(
                Caller(
                    surface=surface,
                    file=source,
                    call_line=_line_of(text, match.start()),
                    line=_line_of(text, match.start(2)),
                    path=path,
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
# 三个面全部参与 resolve 断言


def _is_excepted(caller: Caller) -> bool:
    for rel, literal, _reason in EXCEPTIONS:
        if caller.rel == rel and caller.path == literal:
            return True
    return False


def test_scanner_finds_the_expected_volume():
    """每个面都必须真的扫到东西，否则后面的断言会空跑通过。"""
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
    """跨行书写的调用必须被扫到 —— 上一版守护正是在这里漏了。"""
    multiline = [c for c in CALLERS if c.multiline]
    assert multiline, "一条跨行调用都没扫到，说明扫描器退化成了按行匹配"
    assert any(c.rel == "tests/api/conftest.py" for c in multiline), (
        "tests/api/conftest.py 的跨行调用未被扫到："
        + NL
        + NL.join(f"  - {c.rel}:{c.line}" for c in multiline)
    )
    assert any(c.rel.endswith("api/toolbox.ts") for c in multiline), (
        "前端跨行调用未被扫到（toolbox.ts）"
    )


def test_exception_list_entries_are_real():
    """例外必须指向真实存在的字面量，否则清单会腐化成永久免责。"""
    stale = []
    for rel, literal, reason in EXCEPTIONS:
        if not reason.strip():
            stale.append(f"{rel} 的例外缺理由：{literal}")
        if not any(c.rel == rel and c.path == literal for c in CALLERS):
            stale.append(f"{rel} 中已找不到该字面量：{literal}")
    assert stale == [], "例外清单失效：" + NL + NL.join(f"  - {s}" for s in stale)


def test_auth_chain_is_covered_by_the_scan():
    """本守护起因于认证链路，必须确认那些调用真的被扫到了。"""
    covered = {c.rel for c in CALLERS if c.rel in AUTH_CALL_FILES}
    assert covered == set(AUTH_CALL_FILES), (
        "认证链路有文件没被扫到："
        + NL
        + NL.join(f"  - {p}" for p in sorted(set(AUTH_CALL_FILES) - covered))
    )


def test_every_caller_path_ends_with_slash():
    """全部三个面的 /api/ 路径都必须带尾斜杠（例外清单除外）。"""
    bad = [c.where for c in CALLERS if not c.path.endswith("/") and not _is_excepted(c)]
    assert bad == [], (
        "以下调用方缺尾斜杠（约定见 openspec/specs/api-path-convention）："
        + NL
        + NL.join(f"  - {item}" for item in bad)
    )


def test_every_caller_path_resolves_to_a_view():
    """**三个面**的每条路径都必须在后端路由表里命中。"""
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


def test_auth_chain_resolves_to_expected_views():
    """认证链路五个端点必须命中五个认证视图。"""
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
