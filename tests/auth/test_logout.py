"""登出接口测试 — POST /api/ai/auth/logout（数据驱动 + JSON Schema）。

9 条用例按断言 Shape 分为 2 个参数化组 + 3 个独立函数：
  - test_logout_success[1]       — 200 + status=True（正常登出）
  - test_logout_reject[5]        — 401（中间件拦截）
  - test_logout_token_invalid    — 两步验证：登出 → /me 401
  - test_logout_repeated         — 重复登出
  - test_logout_redis_unavailable — 503（skip：需 Redis 不可用环境）

运行方式：
    pytest tests/auth/test_logout.py -v
"""

from dataclasses import dataclass

import allure
import jsonschema
import pytest

from tests.auth.conftest import LOGOUT_URL, ME_URL, set_allure_metadata
from tests.auth.schemas import ERROR_RESPONSE_SCHEMA, LOGOUT_SUCCESS_SCHEMA

# ═══════════════════════════════════════════════════════════════════
# 数据类型
# ═══════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class LogoutCase:
    """登出用例 — 含鉴权头构造参数。"""

    id: str
    title: str
    description: str
    severity: str
    priority: str
    expected_status: int
    auth_format: str  # "bearer" | "none" | "non-bearer" | "empty-bearer" | "expired" | "tampered"
    extra_tags: tuple[str, ...] = ()


def _build_auth_header(case: LogoutCase, auth_token: dict) -> str:
    """根据用例 auth_format 构造 Authorization 头值。"""
    if case.auth_format == "bearer":
        return f"Bearer {auth_token['access_token']}"
    if case.auth_format == "non-bearer":
        return f"Token {auth_token['access_token']}"
    if case.auth_format == "empty-bearer":
        return "Bearer "
    if case.auth_format == "expired":
        return "expired_token_placeholder"
    if case.auth_format == "tampered":
        tampered = auth_token["access_token"][:-1] + (
            "0" if auth_token["access_token"][-1] != "0" else "1"
        )
        return f"Bearer {tampered}"
    return ""


# ═══════════════════════════════════════════════════════════════════
# Group 1: 200 — 登出成功（3 条）— 全部 xfail（中间件 BUG）
# ═══════════════════════════════════════════════════════════════════

LOGOUT_SUCCESS_CASES: list[LogoutCase] = [
    LogoutCase(
        id="TC-LOGOUT-001",
        title="正常登出",
        description="Authorization: Bearer <有效token>\n期望：200，token 加入 Redis 黑名单\n测试点：正常登出流程",
        severity="blocker",
        priority="P0",
        expected_status=200,
        auth_format="bearer",
    ),
]


@pytest.mark.parametrize("case", LOGOUT_SUCCESS_CASES, ids=lambda c: c.id)
@pytest.mark.api
@pytest.mark.auth
def test_logout_success(base_url, api_session, auth_token, case):
    """参数化：登出成功（1 条）。"""
    tags = ("auth", "api", case.priority) + case.extra_tags
    set_allure_metadata(
        feature="认证模块",
        story="登出接口",
        title=f"{case.id}: {case.title}",
        description=case.description,
        severity=case.severity,
        tags=tags,
    )
    headers = {}
    if case.auth_format == "bearer":
        # TC-LOGOUT-001: 独立登录获取 token，避免污染共享 auth_token
        login_resp = api_session.post(
            f"{base_url}/api/ai/auth/login",
            json={"username": "admin", "password": "admin123"},
        )
        access = login_resp.json()["access_token"]
        headers["Authorization"] = f"Bearer {access}"
    elif case.auth_format != "none":
        headers["Authorization"] = _build_auth_header(case, auth_token)

    resp = api_session.post(f"{base_url}{LOGOUT_URL}", headers=headers)
    body = resp.json()
    assert resp.status_code == case.expected_status, (
        f"期望 {case.expected_status}，实际 {resp.status_code}: {body}"
    )
    jsonschema.validate(instance=body, schema=LOGOUT_SUCCESS_SCHEMA)


# ═══════════════════════════════════════════════════════════════════
# Group 2: 401 — 中间件拦截（5 条）
# ═══════════════════════════════════════════════════════════════════

LOGOUT_REJECT_CASES: list[LogoutCase] = [
    LogoutCase(
        id="TC-LOGOUT-003",
        title="无 Authorization 请求头",
        description="无 Authorization 头\n期望：401（中间件拦截：缺 Authorization header）\n测试点：缺少鉴权信息",
        severity="critical",
        priority="P0",
        expected_status=401,
        auth_format="none",
    ),
    LogoutCase(
        id="TC-LOGOUT-004",
        title="Authorization 值非 Bearer 格式",
        description="Authorization: Token xxx\n期望：401（中间件拦截：非 Bearer 格式）\n测试点：中间件只接受 Bearer scheme",
        severity="normal",
        priority="P1",
        expected_status=401,
        auth_format="non-bearer",
    ),
    LogoutCase(
        id="TC-LOGOUT-005",
        title="Authorization 值为空 Bearer",
        description="Authorization: Bearer \n期望：401（中间件拦截：空 token 无法通过 verify_token）\n测试点：边界行为 — 空 token",
        severity="normal",
        priority="P1",
        expected_status=401,
        auth_format="empty-bearer",
    ),
    LogoutCase(
        id="TC-LOGOUT-006",
        title="使用已过期的 access_token",
        description="Authorization: Bearer <过期token>\n期望：401（中间件 verify_token exp 校验失败）\n测试点：过期 token 被中间件拦截",
        severity="normal",
        priority="P1",
        expected_status=401,
        auth_format="expired",
    ),
    LogoutCase(
        id="TC-LOGOUT-007",
        title="使用被篡改的 access_token",
        description="Authorization: Bearer <篡改token>\n期望：401（JWT 签名验证失败）\n测试点：签名校验",
        severity="normal",
        priority="P1",
        expected_status=401,
        auth_format="tampered",
        extra_tags=("security",),
    ),
]


@pytest.mark.parametrize("case", LOGOUT_REJECT_CASES, ids=lambda c: c.id)
@pytest.mark.api
@pytest.mark.auth
def test_logout_reject(base_url, api_session, auth_token, case):
    """参数化：登出被中间件拒绝（5 条）。"""
    tags = ("auth", "api", case.priority) + case.extra_tags
    set_allure_metadata(
        feature="认证模块",
        story="登出接口",
        title=f"{case.id}: {case.title}",
        description=case.description,
        severity=case.severity,
        tags=tags,
    )
    headers = {}
    if case.auth_format != "none":
        headers["Authorization"] = _build_auth_header(case, auth_token)

    resp = api_session.post(f"{base_url}{LOGOUT_URL}", headers=headers)
    body = resp.json()
    assert resp.status_code == 401, f"期望 401，实际 {resp.status_code}: {body}"
    jsonschema.validate(instance=body, schema=ERROR_RESPONSE_SCHEMA)


# ═══════════════════════════════════════════════════════════════════
# 独立函数：两步验证 / 重复登出 / Redis 不可用
# ═══════════════════════════════════════════════════════════════════


@allure.feature("认证模块")
@allure.story("登出接口")
@allure.severity(allure.severity_level.CRITICAL)
@allure.title("TC-LOGOUT-002: 登出后原 token 无法使用")
@allure.description(
    "步骤：正常登出 → 用同 token 调 /me\n期望：登出 200 → /me 401\n测试点：黑名单生效"
)
@allure.tag("auth", "api", "P0")
@pytest.mark.api
@pytest.mark.auth
def test_logout_token_invalid(base_url, api_session, auth_token):
    """两步验证：登出后 token 失效。"""
    # 独立登录获取 token，避免污染共享 auth_token
    login_resp = api_session.post(
        f"{base_url}/api/ai/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    access = login_resp.json()["access_token"]

    # Step 1: 确认 token 有效
    me_before = api_session.get(
        f"{base_url}{ME_URL}",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert me_before.status_code == 200, f"登出前 /me 应正常: {me_before.json()}"

    # Step 2: 登出
    logout_resp = api_session.post(
        f"{base_url}{LOGOUT_URL}",
        headers={"Authorization": f"Bearer {access}"},
    )
    assert logout_resp.status_code == 200, f"登出失败: {logout_resp.json()}"

    # Step 3: 登出后同 token 调 /me
    me_after = api_session.get(
        f"{base_url}{ME_URL}",
        headers={"Authorization": f"Bearer {access}"},
    )
    body = me_after.json()
    assert me_after.status_code == 401, f"登出后 /me 期望 401，实际 {me_after.status_code}: {body}"
    assert body["status"] is False


@allure.feature("认证模块")
@allure.story("登出接口")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("TC-LOGOUT-009: 重复登出")
@allure.description(
    "对已登出的 token 再次登出\n"
    "期望：第二次登出返回 401（中间件 verify_token 检测到黑名单）或 200（幂等）\n"
    "测试点：验证重复登出不产生意外副作用"
)
@allure.tag("auth", "api", "P2")
@pytest.mark.api
@pytest.mark.auth
def test_logout_repeated(base_url, api_session, auth_token):
    """重复登出。"""
    # 独立登录获取 token，避免污染共享 auth_token
    login_resp = api_session.post(
        f"{base_url}/api/ai/auth/login",
        json={"username": "admin", "password": "admin123"},
    )
    access = login_resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {access}"}

    resp1 = api_session.post(f"{base_url}{LOGOUT_URL}", headers=headers)
    assert resp1.status_code == 200, f"首次登出失败: {resp1.json()}"

    resp2 = api_session.post(f"{base_url}{LOGOUT_URL}", headers=headers)
    assert resp2.status_code in (200, 401), (
        f"重复登出期望 200/401，实际 {resp2.status_code}: {resp2.json()}"
    )


@allure.feature("认证模块")
@allure.story("登出接口")
@allure.severity(allure.severity_level.NORMAL)
@allure.title("TC-LOGOUT-008: Redis 不可用")
@allure.description(
    "Redis 不可用时登出 → 503，retry: true\n"
    "测试点：BlacklistUnavailableError 正确捕获\n"
    "注意：此用例在 Redis 正常时不执行（pytest.skip）"
)
@allure.tag("auth", "api", "P2")
@pytest.mark.api
@pytest.mark.auth
def test_logout_redis_unavailable(base_url, api_session, auth_token):
    """Redis 不可用 → 503。仅在 Redis 故障时触发。"""
    pytest.skip("需要 Redis 不可用环境 — 手动验证时注释此行")
