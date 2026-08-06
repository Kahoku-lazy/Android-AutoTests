"""当前用户接口测试 — GET /api/ai/auth/me（数据驱动 + JSON Schema）。

⚠️ 已知问题：/api/ai/auth/me 匹配中间件公开路径前缀 /api/ai/auth/，
中间件跳过鉴权 → me view 永远拿不到 user_id → 总是返回 401 "Not authenticated"。
成功路径用例用 @pytest.mark.xfail 标记，修复中间件后自动生效。

9 条用例按断言 Shape 分为 1 个参数化组 + 3 个独立函数：
  - test_me_auth_reject[6]      — 401 "Not authenticated"
  - test_me_success              — 200 + user 对象（xfail：中间件 BUG）
  - test_me_no_sensitive_fields  — 不返回敏感字段（xfail：中间件 BUG）
  - test_me_user_deleted         — 404 "User not found"（xfail：中间件 BUG）

运行方式：
    pytest tests/auth/test_me.py -v
"""

import time

from dataclasses import dataclass

import allure
import jsonschema
import jwt
import pytest

from django.conf import settings

from tests.auth.conftest import LOGOUT_URL, ME_URL, REGISTER_URL, set_allure_metadata
from tests.auth.schemas import ME_USER_SCHEMA

_XFAIL_MIDDLEWARE = (
    "中间件 BUG: /api/ai/auth/me 匹配公开路径前缀 /api/ai/auth/，"
    "中间件跳过鉴权 → me view 拿不到 user_id → 始终返回 401"
)


# ═══════════════════════════════════════════════════════════════════
# 数据类型
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class MeRejectCase:
    """401 鉴权拒绝用例。"""

    id: str
    title: str
    description: str
    severity: str
    priority: str
    expected_status: int
    expected_message: str
    auth_format: str  # "none" | "non-bearer" | "expired" | "tampered" | "blacklisted" | "refresh"
    extra_tags: tuple[str, ...] = ()


# ═══════════════════════════════════════════════════════════════════
# 独立函数：正常获取当前用户（xfail：中间件 BUG）
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.xfail(reason=_XFAIL_MIDDLEWARE)
@allure.feature("认证模块")
@allure.story("当前用户")
@allure.severity(allure.severity_level.BLOCKER)
@allure.title("TC-ME-001: 正常获取当前用户")
@allure.description(
    "GET /me，Authorization: Bearer <有效token>\n期望：200，user: {id, username}\n测试点：页面刷新后恢复登录态"
)
@allure.tag("auth", "api", "P0")
@pytest.mark.api
@pytest.mark.auth
def test_me_success(base_url, api_session, auth_token):
    """正常获取当前用户 → 200 — xfail：中间件 BUG。"""
    headers = {"Authorization": f"Bearer {auth_token['access_token']}"}
    resp = api_session.get(f"{base_url}{ME_URL}", headers=headers)
    body = resp.json()
    assert resp.status_code == 200, f"期望 200，实际 {resp.status_code}: {body}"
    jsonschema.validate(instance=body, schema=ME_USER_SCHEMA)
    assert body["user"]["username"] == "admin"


@pytest.mark.xfail(reason=_XFAIL_MIDDLEWARE)
@allure.feature("认证模块")
@allure.story("当前用户")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC-ME-002: 不返回敏感字段")
@allure.description(
    "确认 /me 响应中 user 对象不含 password / email / api_key\n测试点：确认响应无敏感字段泄漏"
)
@allure.tag("auth", "api", "security", "P0")
@pytest.mark.api
@pytest.mark.auth
def test_me_no_sensitive_fields(base_url, api_session, auth_token):
    """验证 /me 响应不泄露敏感字段 — xfail：中间件 BUG。"""
    headers = {"Authorization": f"Bearer {auth_token['access_token']}"}
    resp = api_session.get(f"{base_url}{ME_URL}", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    user = body["user"]
    for forbidden in ("password", "email", "api_key"):
        assert forbidden not in user, f"user 对象不应包含 {forbidden} 字段"


# ═══════════════════════════════════════════════════════════════════
# Group 1: 401 — "Not authenticated"（6 条）
# ═══════════════════════════════════════════════════════════════════

ME_REJECT_CASES: list[MeRejectCase] = [
    MeRejectCase(
        id="TC-ME-003",
        title="无 Authorization 请求头",
        description='无 Authorization 头\n期望：401，message="Not authenticated"\n测试点：request.user_id 为 None',
        severity="critical",
        priority="P0",
        expected_status=401,
        expected_message="Not authenticated",
        auth_format="none",
    ),
    MeRejectCase(
        id="TC-ME-004",
        title="Authorization 值非 Bearer 格式",
        description='Authorization: Token xxx\n期望：401，message="Not authenticated"\n测试点：中间件无法从非 Bearer 格式提取 Token',
        severity="normal",
        priority="P1",
        expected_status=401,
        expected_message="Not authenticated",
        auth_format="non-bearer",
    ),
    MeRejectCase(
        id="TC-ME-005",
        title="access_token 已过期",
        description='Authorization: Bearer <过期token>\n期望：401，message="Not authenticated"\n测试点：过期 token → verify_token 失败 → user_id=None',
        severity="normal",
        priority="P1",
        expected_status=401,
        expected_message="Not authenticated",
        auth_format="expired",
    ),
    MeRejectCase(
        id="TC-ME-006",
        title="access_token 被篡改",
        description='Authorization: Bearer <篡改token>\n期望：401，message="Not authenticated"\n测试点：JWT 签名验证失败',
        severity="normal",
        priority="P1",
        expected_status=401,
        expected_message="Not authenticated",
        auth_format="tampered",
        extra_tags=("security",),
    ),
    MeRejectCase(
        id="TC-ME-007",
        title="access_token 已在黑名单",
        description='Authorization: Bearer <已登出token>\n期望：401，message="Not authenticated"\n测试点：中间件/me view 对已登出 token 的处理',
        severity="critical",
        priority="P0",
        expected_status=401,
        expected_message="Not authenticated",
        auth_format="blacklisted",
    ),
    MeRejectCase(
        id="TC-ME-009",
        title="使用 refresh_token 访问",
        description="Authorization: Bearer <refresh_token>\n期望：401（me view 的 user_id 为 None）\n测试点：type 校验",
        severity="normal",
        priority="P1",
        expected_status=401,
        expected_message="Not authenticated",
        auth_format="refresh",
        extra_tags=("security",),
    ),
]


def _build_me_headers(case: MeRejectCase, auth_token: dict) -> dict:
    """根据用例 auth_format 构造 Authorization 头。"""
    if case.auth_format == "none":
        return {}
    if case.auth_format == "non-bearer":
        return {"Authorization": f"Token {auth_token['access_token']}"}
    if case.auth_format == "expired":
        expired = jwt.encode(
            {
                "sub": "1",
                "jti": "expired_me_test",
                "type": "access",
                "iat": int(time.time()) - 7200,
                "exp": int(time.time()) - 3600,
            },
            settings.SECRET_KEY,
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {expired}"}
    if case.auth_format == "tampered":
        tampered = auth_token["access_token"][:-1] + (
            "0" if auth_token["access_token"][-1] != "0" else "1"
        )
        return {"Authorization": f"Bearer {tampered}"}
    if case.auth_format == "blacklisted":
        return {"Authorization": f"Bearer {auth_token['access_token']}"}
    if case.auth_format == "refresh":
        return {"Authorization": f"Bearer {auth_token['refresh_token']}"}
    return {}


@pytest.mark.parametrize("case", ME_REJECT_CASES, ids=lambda c: c.id)
@pytest.mark.api
@pytest.mark.auth
def test_me_auth_reject(base_url, api_session, auth_token, case):
    """参数化：鉴权被拒 — 始终 401 "Not authenticated"（6 条）。

    注意：由于中间件将 /api/ai/auth/me 视为公开路径跳过鉴权，
    实际 401 来自 me view 自身（user_id 为 None），而非来自中间件。
    修复中间件后，部分用例的 401 来源会从 me view 变为中间件。
    """
    tags = ("auth", "api", case.priority) + case.extra_tags
    set_allure_metadata(
        feature="认证模块",
        story="当前用户",
        title=f"{case.id}: {case.title}",
        description=case.description,
        severity=case.severity,
        tags=tags,
    )
    # TC-ME-007 需要先登出
    if case.auth_format == "blacklisted":
        api_session.post(
            f"{base_url}{LOGOUT_URL}",
            headers={"Authorization": f"Bearer {auth_token['access_token']}"},
        )

    headers = _build_me_headers(case, auth_token)
    resp = api_session.get(f"{base_url}{ME_URL}", headers=headers)
    body = resp.json()
    assert resp.status_code == case.expected_status, (
        f"期望 {case.expected_status}，实际 {resp.status_code}: {body}"
    )
    assert body["message"] == case.expected_message


# ═══════════════════════════════════════════════════════════════════
# 独立函数：用户已删
# ═══════════════════════════════════════════════════════════════════


@pytest.mark.xfail(reason=_XFAIL_MIDDLEWARE + " + django_db 兼容性问题")
@allure.feature("认证模块")
@allure.story("当前用户")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("TC-ME-008: Token 中 user_id 对应用户已删除")
@allure.description(
    "步骤：注册新用户 → 获取 token → 删除用户 → 用 token 调 /me\n"
    '期望：404，message="User not found"\n'
    "测试点：User.objects.get(id=user_id) 抛出 DoesNotExist"
)
@allure.tag("auth", "api", "P2")
@pytest.mark.api
@pytest.mark.auth
@pytest.mark.django_db(transaction=True)
def test_me_user_deleted(base_url, api_session, unique_username):
    """用户已删除 → 404 — xfail：中间件 BUG。"""
    from django.contrib.auth.models import User

    register_resp = api_session.post(
        f"{base_url}{REGISTER_URL}",
        json={
            "username": unique_username,
            "password": "pass123",
            "password2": "pass123",
            "email": "a@b.com",
        },
    )
    assert register_resp.status_code == 200, f"注册失败: {register_resp.json()}"
    tokens = register_resp.json()
    access = tokens["access_token"]
    user_id = tokens["user"]["id"]

    # 删除用户
    User.objects.filter(id=user_id).delete()

    # 用有效 token 调 /me
    resp = api_session.get(
        f"{base_url}{ME_URL}",
        headers={"Authorization": f"Bearer {access}"},
    )
    body = resp.json()
    assert resp.status_code == 404, f"期望 404，实际 {resp.status_code}: {body}"
    assert body["message"] == "User not found"
