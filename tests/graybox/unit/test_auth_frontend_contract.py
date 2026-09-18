"""前端认证契约与后端事实的对拍：响应字段、公开端点清单。

为什么需要它
--------------
1. 前端用 TypeScript DTO 复述后端的响应形状。一旦声明了后端不返回的字段，
   消费者会在运行时拿到 `undefined` 而不会有任何报错。
   实例：原本 `AuthTokenData.user?: { id, username, email? }` 把 login（无 email）与
   register（有 email）的差异掩盖掉了，而该字段在前端无任何读取点。
2. 全局 401 拦截器需要知道哪些端点是公开的 —— 公开端点的 401 是“凭证错误”，
   不是“令牌过期”。该清单与网关的公开路径清单必须一致，否则两边各自漂移。

边界（见 tests/AGENTS.md §契约对拍测试）：只读源码、只做一致性断言、零外部依赖。
已知边界：双端点共用的 DTO 只断言**顶层**字段；嵌套形状的差异靠“不声明该字段”消除，
不在本模块机械覆盖。当前前端无嵌套声明，因此该局限不影响现状。
规格：`openspec/specs/auth-response-shape` 与 `openspec/specs/auth-session`。
"""

from __future__ import annotations

import ast
import pathlib
import re

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
AUTH_TYPES = REPO_ROOT / "frontend/src/shared/types/auth.ts"
AUTH_API = REPO_ROOT / "frontend/src/shared/api/auth.ts"
INTERCEPTORS = REPO_ROOT / "frontend/src/shared/api-auth-interceptors.ts"
BACKEND_VIEWS = REPO_ROOT / "apps/accounts/views.py"
BACKEND_JWT = REPO_ROOT / "shared/auth/jwt_auth.py"

# 错误响应的唯一 key；除它之外的 Response 就是成功响应
ERROR_KEY_SET = {"detail"}


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _interface_fields(path: pathlib.Path, name: str) -> set[str]:
    """读出某个 interface 声明的顶层字段名。"""
    fields: set[str] = set()
    inside = False
    for line in _read(path).splitlines():
        if not inside:
            if re.match(r"\s*(?:export\s+)?interface\s+" + name + r"\s*\{", line):
                inside = True
            continue
        if re.match(r"^\}", line):
            break
        match = re.match(r"\s*(\w+)(\?)?\s*:", line)
        if match:
            fields.add(match.group(1))
    return fields


def _call_name(node: ast.AST) -> str:
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Name):
        return node.id
    return ""


def _token_pair_keys() -> set[str]:
    """后端 create_token_pair() 返回的 key 集合。"""
    tree = ast.parse(_read(BACKEND_JWT))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "create_token_pair":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Dict):
                    return {k.value for k in sub.value.keys if isinstance(k, ast.Constant)}
    return set()


def _response_key_sets(class_name: str, method: str) -> list[set[str]]:
    """某视图方法里每个 Response({...}) 的顶层 key集合；★★tokens 展开为 create_token_pair 的 key。"""
    tokens = _token_pair_keys()
    out: list[set[str]] = []
    tree = ast.parse(_read(BACKEND_VIEWS))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.ClassDef) and node.name == class_name):
            continue
        for sub in node.body:
            if not (isinstance(sub, ast.FunctionDef) and sub.name == method):
                continue
            for call in ast.walk(sub):
                if not (
                    isinstance(call, ast.Call)
                    and _call_name(call.func) == "Response"
                    and call.args
                    and isinstance(call.args[0], ast.Dict)
                ):
                    continue
                keys: set[str] = set()
                for index, key in enumerate(call.args[0].keys):
                    if key is None:
                        keys |= tokens  # **tokens
                    elif isinstance(key, ast.Constant):
                        keys.add(str(key.value))
                out.append(keys)
    return out


def _success_keys(class_name: str, method: str) -> set[str]:
    """成功响应的 key 集合（排除 {detail} 形式的错误响应）。"""
    for keys in _response_key_sets(class_name, method):
        if keys != ERROR_KEY_SET:
            return keys
    return set()


def _me_user_keys() -> set[str]:
    """MeView 成功响应里嵌套 user 对象的 key。"""
    tree = ast.parse(_read(BACKEND_VIEWS))
    for node in ast.walk(tree):
        if not (isinstance(node, ast.ClassDef) and node.name == "MeView"):
            continue
        for sub in node.body:
            if not (isinstance(sub, ast.FunctionDef) and sub.name == "get"):
                continue
            for call in ast.walk(sub):
                if not (
                    isinstance(call, ast.Call)
                    and _call_name(call.func) == "Response"
                    and call.args
                    and isinstance(call.args[0], ast.Dict)
                ):
                    continue
                for key, value in zip(call.args[0].keys, call.args[0].values):
                    if (
                        isinstance(key, ast.Constant)
                        and key.value == "user"
                        and isinstance(value, ast.Dict)
                    ):
                        return {k.value for k in value.keys if isinstance(k, ast.Constant)}
    return set()


def _interceptor_public_paths() -> set[str]:
    """前端拦截器声明的公开端点（相对 baseURL）。"""
    text = _read(INTERCEPTORS)
    match = re.search(r"PUBLIC_AUTH_PATHS\s*=\s*\[([^\]]*)\]", text)
    return set(re.findall(r"'([^']+)'", match.group(1))) if match else set()


def _gateway_public_auth_paths() -> set[str]:
    """网关 PUBLIC_PREFIXES 中 /api/auth/ 的那一部分（去掉 /api 前缀以便对拍）。"""
    from gateway.middleware import PUBLIC_PREFIXES

    return {p[len("/api") :] for p in PUBLIC_PREFIXES if p.startswith("/api/auth/")}


LOGIN_KEYS = _success_keys("LoginView", "post")
REGISTER_KEYS = _success_keys("RegisterView", "post")
REFRESH_KEYS = _success_keys("RefreshView", "post")


def test_extraction_finds_the_expected_sides():
    """两边都必须真的读到东西，否则子集断言会因为空集合而空跑通过。"""
    actual = {
        "登录响应 key": LOGIN_KEYS,
        "注册响应 key": REGISTER_KEYS,
        "刷新响应 key": REFRESH_KEYS,
        "me 的 user key": _me_user_keys(),
        "前端 AuthTokenData": _interface_fields(AUTH_TYPES, "AuthTokenData"),
        "前端 AuthRefreshData": _interface_fields(AUTH_TYPES, "AuthRefreshData"),
        "前端 MeUser": _interface_fields(AUTH_API, "MeUser"),
        "拦截器公开端点": _interceptor_public_paths(),
        "网关公开端点": _gateway_public_auth_paths(),
    }
    empty = [label for label, value in actual.items() if not value]
    assert empty == [], "以下侧提取为空，提取规则可能失效：" + "、".join(empty)


def test_token_dto_fields_are_returned_by_both_endpoints():
    """`AuthTokenData` 被 login 与 register 共用：它声明的每个字段都必须被两者返回。"""
    declared = _interface_fields(AUTH_TYPES, "AuthTokenData")
    both = LOGIN_KEYS & REGISTER_KEYS
    extra = sorted(declared - both)
    assert extra == [], (
        "`AuthTokenData` 声明了两个端点都不返回的字段："
        + "、".join(extra)
        + "（login="
        + ",".join(sorted(LOGIN_KEYS))
        + " / register="
        + ",".join(sorted(REGISTER_KEYS))
        + "）"
    )


def test_refresh_dto_fields_are_returned_by_refresh():
    """`AuthRefreshData` 声明的字段必须都在 refresh 响应里。"""
    declared = _interface_fields(AUTH_TYPES, "AuthRefreshData")
    extra = sorted(declared - REFRESH_KEYS)
    assert extra == [], (
        "`AuthRefreshData` 声明了 refresh 响应不返回的字段："
        + "、".join(extra)
        + "（响应="
        + ",".join(sorted(REFRESH_KEYS))
        + "）"
    )


def test_me_dto_fields_match_me_response_user():
    """`MeUser` 与 `/api/auth/me/` 响应中 user 对象的 key 必须完全一致。"""
    declared = _interface_fields(AUTH_API, "MeUser")
    actual = _me_user_keys()
    assert declared == actual, (
        "`MeUser` 与 me 响应不一致：仅前端 "
        + str(sorted(declared - actual))
        + "，仅后端 "
        + str(sorted(actual - declared))
    )


def test_interceptor_public_paths_match_gateway():
    """拦截器的公开端点清单必须与网关的 /api/auth/* 部分逐项相等。"""
    frontend = _interceptor_public_paths()
    backend = _gateway_public_auth_paths()
    assert frontend == backend, (
        "前端与网关的公开认证端点清单不一致：仅前端 "
        + str(sorted(frontend - backend))
        + "，仅网关 "
        + str(sorted(backend - frontend))
    )
