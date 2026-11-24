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
BACKEND_VIEWS = REPO_ROOT / "backend/apps/accounts/views.py"
BACKEND_JWT = REPO_ROOT / "backend/shared/auth/jwt_auth.py"

ERROR_KEY_SET = {"detail"}


def _read(path: pathlib.Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _interface_fields(path: pathlib.Path, name: str) -> set[str]:
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
    tree = ast.parse(_read(BACKEND_JWT))
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "create_token_pair":
            for sub in ast.walk(node):
                if isinstance(sub, ast.Return) and isinstance(sub.value, ast.Dict):
                    return {k.value for k in sub.value.keys if isinstance(k, ast.Constant)}
    return set()


def _response_key_sets(class_name: str, method: str) -> list[set[str]]:
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
                        keys |= tokens
                    elif isinstance(key, ast.Constant):
                        keys.add(str(key.value))
                out.append(keys)
    return out


def _success_keys(class_name: str, method: str) -> set[str]:
    for keys in _response_key_sets(class_name, method):
        if keys != ERROR_KEY_SET:
            return keys
    return set()


def _me_user_keys() -> set[str]:
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
    text = _read(INTERCEPTORS)
    match = re.search(r"PUBLIC_AUTH_PATHS\s*=\s*\[([^\]]*)\]", text)
    return set(re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))) if match else set()


def _gateway_public_auth_paths() -> set[str]:
    from backend.gateway.middleware import PUBLIC_PREFIXES

    return {p[len("/api") :] for p in PUBLIC_PREFIXES if p.startswith("/api/auth/")}


LOGIN_KEYS = _success_keys("LoginView", "post")
REGISTER_KEYS = _success_keys("RegisterView", "post")
REFRESH_KEYS = _success_keys("RefreshView", "post")


def test_extraction_finds_the_expected_sides():
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
    declared = _interface_fields(AUTH_API, "MeUser")
    actual = _me_user_keys()
    assert declared == actual, (
        "`MeUser` 与 me 响应不一致：仅前端 "
        + str(sorted(declared - actual))
        + "，仅后端 "
        + str(sorted(actual - declared))
    )


def test_interceptor_public_paths_match_gateway():
    frontend = _interceptor_public_paths()
    backend = _gateway_public_auth_paths()
    assert frontend == backend, (
        "前端与网关的公开认证端点清单不一致：仅前端 "
        + str(sorted(frontend - backend))
        + "，仅网关 "
        + str(sorted(backend - frontend))
    )
