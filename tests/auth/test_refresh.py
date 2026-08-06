"""刷新 Token 接口测试 — POST /api/ai/auth/refresh（数据驱动 + JSON Schema）。

10 条用例按断言 Shape 分为 1 个参数化组 + 4 个独立函数：
  - test_refresh_reject[5]       — 401 + status=False
  - test_refresh_success          — 200 + 新 access_token
  - test_refresh_replaces_token   — 刷新后旧 access_token 对 /me 的效力
  - test_refresh_expired          — 过期 refresh_token → 401
  - test_refresh_invalid_json     — 非 JSON 请求体
  - test_refresh_post_logout      — 登出后 refresh_token 被拒

运行方式：
    pytest tests/auth/test_refresh.py -v
"""

import time

from dataclasses import dataclass

import allure
import jsonschema
import jwt
import pytest

from django.conf import settings

from tests.auth.conftest import REFRESH_URL, set_allure_metadata
from tests.auth.schemas import ERROR_RESPONSE_SCHEMA, REFRESH_SUCCESS_SCHEMA

# ═══════════════════════════════════════════════════════════════════
# 数据类型
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class RefreshRejectCase:
    """401 拒绝用例 — 无效的 refresh_token。"""

    id: str
    title: str
    description: str
    severity: str
    priority: str
    payload: dict
    expected_message: str | None = None  # 有值则精确匹配
    extra_tags: tuple[str, ...] = ()


# ═══════════════════════════════════════════════════════════════════
# Group 1: 401 — 无效/缺失/篡改的 refresh_token（5 条）
# ═══════════════════════════════════════════════════════════════════

REFRESH_REJECT_CASES: list[RefreshRejectCase] = [
    RefreshRejectCase(
        id="TC-REF-003",
        title="refresh_token 为空",
        description='请求体：{"refresh_token":""}\n期望：401，message 含错误描述\n测试点：data.get("refresh_token","") → ""',
        severity="critical",
        priority="P0",
        payload={"refresh_token": ""},
    ),
    RefreshRejectCase(
        id="TC-REF-004",
        title="缺少 refresh_token 字段",
        description="请求体：{}\n期望：401，message 含错误描述\n测试点：空 token 触发 verify_token 异常",
        severity="critical",
        priority="P0",
        payload={},
    ),
    RefreshRejectCase(
        id="TC-REF-005",
        title="refresh_token 为随机字符串",
        description='请求体：{"refresh_token":"random_string"}\n期望：401，message 含 JWT 解析错误\n测试点：非 JWT 格式',
        severity="normal",
        priority="P1",
        payload={"refresh_token": "random_string"},
    ),
    RefreshRejectCase(
        id="TC-REF-007",
        title="使用 access_token 代替 refresh_token",
        description='请求体：{"refresh_token":"<有效access_token>"}\n期望：401，message="Invalid token type: expected refresh"\n测试点：payload.get("type") != "refresh"',
        severity="critical",
        priority="P0",
        payload=None,  # 运行时注入 auth_token.access_token
        expected_message="Invalid token type: expected refresh",
    ),
    RefreshRejectCase(
        id="TC-REF-008",
        title="使用被篡改的 refresh_token",
        description="请求体：refresh_token 最后一位翻转\n期望：401，签名验证失败\n测试点：JWT 签名验证",
        severity="normal",
        priority="P1",
        extra_tags=("security",),
        payload=None,  # 运行时注入篡改后的 refresh_token
    ),
]


def _resolve_refresh_payload(case: RefreshRejectCase, auth_token: dict) -> dict:
    """将运行时 token 注入到 payload 中。"""
    if case.id == "TC-REF-007":
        return {"refresh_token": auth_token["access_token"]}
    if case.id == "TC-REF-008":
        tampered = auth_token["refresh_token"][:-1] + (
            "0" if auth_token["refresh_token"][-1] != "0" else "1"
        )
        return {"refresh_token": tampered}
    return case.payload


@pytest.mark.parametrize("case", REFRESH_REJECT_CASES, ids=lambda c: c.id)
@pytest.mark.api
@pytest.mark.auth
def test_refresh_reject(base_url, api_session, auth_token, case):
    """参数化：refresh_token 被拒绝（5 条）。"""
    tags = ("auth", "api", case.priority) + case.extra_tags
    set_allure_metadata(
        feature="认证模块",
        story="刷新 Token",
        title=f"{case.id}: {case.title}",
        description=case.description,
        severity=case.severity,
        tags=tags,
    )
    payload = _resolve_refresh_payload(case, auth_token)
    resp = api_session.post(f"{base_url}{REFRESH_URL}", json=payload)
    body = resp.json()
    jsonschema.validate(instance=body, schema=ERROR_RESPONSE_SCHEMA)
    assert resp.status_code == 401, f"期望 401，实际 {resp.status_code}: {body}"
    if case.expected_message:
        assert body["message"] == case.expected_message


# ═══════════════════════════════════════════════════════════════════
# 独立函数：成功 / token 替换 / 过期 / 非法 JSON / 登出后
# ═══════════════════════════════════════════════════════════════════


@allure.feature("认证模块")
@allure.story("刷新 Token")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("TC-REF-001: 正常刷新")
@allure.description("使用有效 refresh_token\n期望：200，返回新 access_token\n测试点：正常刷新流程")
@allure.tag("auth", "api", "P0")
@pytest.mark.api
@pytest.mark.auth
def test_refresh_success(base_url, api_session, auth_token):
    """正常刷新 → 200 + 新 access_token。"""
    resp = api_session.post(
        f"{base_url}{REFRESH_URL}",
        json={"refresh_token": auth_token["refresh_token"]},
    )
    body = resp.json()
    assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {body}"
    jsonschema.validate(instance=body, schema=REFRESH_SUCCESS_SCHEMA)
    assert body["access_token"] != auth_token["access_token"], "新 access_token 应与旧 token 不同"


@pytest.mark.xfail(
    reason="中间件 BUG: /api/ai/auth/me 匹配公开路径前缀 /api/ai/auth/，"
    "中间件跳过鉴权 → me view 永远拿不到 user_id → 返回 401。"
    "修复 middleware 后再运行此用例。"
)
@allure.feature("认证模块")
@allure.story("刷新 Token")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC-REF-002: 刷新后原 access_token 对 /me 的效力")
@allure.description(
    "先刷新获取新 access_token → 用新旧 token 分别请求 /me\n"
    "期望：新 token 200（当前因中间件 BUG 返回 401）\n"
    "测试点：刷新不影响旧 access_token 有效期（当前设计）"
)
@allure.tag("auth", "api", "P1")
@pytest.mark.api
@pytest.mark.auth
def test_refresh_replaces_token(base_url, api_session, auth_token):
    """刷新后新旧 token 对 /me 的效力 — 受中间件 BUG 影响 xfail。"""
    old_access = auth_token["access_token"]

    resp = api_session.post(
        f"{base_url}{REFRESH_URL}",
        json={"refresh_token": auth_token["refresh_token"]},
    )
    body = resp.json()
    assert resp.status_code == 200, f"刷新失败: {body}"
    new_access = body["access_token"]
    assert new_access != old_access

    me_old = api_session.get(
        f"{base_url}/api/ai/auth/me",
        headers={"Authorization": f"Bearer {old_access}"},
    )
    me_new = api_session.get(
        f"{base_url}/api/ai/auth/me",
        headers={"Authorization": f"Bearer {new_access}"},
    )
    assert me_new.status_code == 200, f"新 token 调 /me 失败: {me_new.json()}"
    assert me_old.status_code == 200, f"旧 token 调 /me 失败: {me_old.json()}"


@allure.feature("认证模块")
@allure.story("刷新 Token")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("TC-REF-006: refresh_token 已过期")
@allure.description("使用已过期的 refresh_token\n期望：401\n测试点：JWT exp 校验")
@allure.tag("auth", "api", "P1")
@pytest.mark.api
@pytest.mark.auth
def test_refresh_expired(base_url, api_session):
    """过期 refresh_token → 401。"""
    expired = jwt.encode(
        {
            "sub": "1",
            "jti": "expired_test",
            "type": "refresh",
            "iat": int(time.time()) - 7200,
            "exp": int(time.time()) - 3600,
        },
        settings.SECRET_KEY,
        algorithm="HS256",
    )
    resp = api_session.post(f"{base_url}{REFRESH_URL}", json={"refresh_token": expired})
    body = resp.json()
    assert resp.status_code == 401, f"期望 401，实际 {resp.status_code}: {body}"
    assert body["status"] is False


@allure.feature("认证模块")
@allure.story("刷新 Token")
@allure.severity(allure.severity_level.MINOR)
@allure.title("TC-REF-009: JSON 格式非法")
@allure.description(
    '请求体：纯文本 "not a json"\n'
    "期望：500（此接口无 try/except JSONDecodeError）\n"
    "测试点：验证已知缺陷 — 非法 JSON 未被优雅处理，会导致 500 而非 400"
)
@allure.tag("auth", "api", "security", "P2")
@pytest.mark.api
@pytest.mark.auth
def test_refresh_invalid_json(base_url, api_session):
    """非 JSON 请求体 — 已知缺陷：无 try/except JSONDecodeError，会 500。"""
    resp = api_session.post(f"{base_url}{REFRESH_URL}", data="not a json")
    # 此接口未捕获 JSONDecodeError，预期返回 500
    assert resp.status_code in (400, 500), (
        f"期望 400 或 500，实际 {resp.status_code}: {resp.text[:200]}"
    )


@pytest.mark.xfail(
    reason="中间件 BUG: /api/ai/auth/logout 匹配公开路径前缀 /api/ai/auth/，"
    "中间件跳过鉴权 → require_auth 拿不到 user_id → 总是返回 401。"
    "修复 middleware 后再运行此用例。"
)
@allure.feature("认证模块")
@allure.story("刷新 Token")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC-REF-010: 使用登出后的 refresh_token")
@allure.description("先登出，再用同 refresh_token 调 refresh\n期望：401\n测试点：黑名单拦截")
@allure.tag("auth", "api", "security", "P0")
@pytest.mark.api
@pytest.mark.auth
def test_refresh_post_logout(base_url, api_session, auth_token):
    """登出后 refresh_token 应被拒绝 — 受中间件 BUG 影响 xfail。"""
    logout_resp = api_session.post(
        f"{base_url}/api/ai/auth/logout",
        headers={"Authorization": f"Bearer {auth_token['access_token']}"},
    )
    assert logout_resp.status_code == 200, f"登出失败: {logout_resp.json()}"

    resp = api_session.post(
        f"{base_url}{REFRESH_URL}",
        json={"refresh_token": auth_token["refresh_token"]},
    )
    body = resp.json()
    assert resp.status_code == 401, f"期望 401，实际 {resp.status_code}: {body}"
    assert body["status"] is False
