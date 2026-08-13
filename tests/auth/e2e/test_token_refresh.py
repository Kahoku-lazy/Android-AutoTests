"""Token 刷新 E2E — TC-E2E-TOKEN-001 ~ 002。"""

from __future__ import annotations

import allure
import pytest

from tests.auth.conftest import set_allure_metadata
from tests.e2e import selectors as S
from tests.e2e.helpers import corrupt_access_token, login_as, read_auth_pool


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_access_token_auto_refresh(clean_page, frontend_url, admin_creds):
    """TC-E2E-TOKEN-001: access 无效时自动 refresh，业务页仍可用。"""
    set_allure_metadata(
        feature="认证模块",
        story="Token刷新E2E",
        title="TC-E2E-TOKEN-001: access 过期自动刷新",
        description="登录后伪造无效 access_token → 刷新仪表盘触发 API → refresh 成功且页面仍可用",
        severity="blocker",
        tags=("auth", "e2e", "P0"),
    )
    page = clean_page
    login_as(
        page,
        admin_creds["username"],
        admin_creds["password"],
        frontend_url=frontend_url,
    )
    with allure.step("记录伪造前的 access_token"):
        pool_before = read_auth_pool(page)
        old_access = pool_before[admin_creds["username"]]["access_token"]
        assert old_access
        assert pool_before[admin_creds["username"]].get("refresh_token")

    corrupt_access_token(page, bogus="expired.access.token")

    with allure.step("刷新 /dashboard 触发带鉴权的业务请求"):
        page.goto(f"{frontend_url}/dashboard", wait_until="networkidle")
        page.get_by_test_id(S.APP_SIDEBAR).wait_for(timeout=15000)

    with allure.step("断言：仍在仪表盘，伪造 token 已被 refresh 替换"):
        assert "/dashboard" in page.url
        assert "/login" not in page.url
        pool_after = read_auth_pool(page)
        new_access = pool_after[admin_creds["username"]]["access_token"]
        assert new_access
        assert new_access != "expired.access.token"


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_refresh_failure_kicks_to_login(clean_page, frontend_url, admin_creds):
    """TC-E2E-TOKEN-002: refresh 也失败时踢回登录页。"""
    set_allure_metadata(
        feature="认证模块",
        story="Token刷新E2E",
        title="TC-E2E-TOKEN-002: refresh 失败踢回登录",
        description="access 与 refresh 均无效 → 业务请求 401 后清空账号并跳转 /login",
        severity="critical",
        tags=("auth", "e2e", "P0"),
    )
    page = clean_page
    login_as(
        page,
        admin_creds["username"],
        admin_creds["password"],
        frontend_url=frontend_url,
    )

    with allure.step("同时破坏 access_token 与 refresh_token"):
        page.evaluate(
            """([poolKey, activeKey]) => {
                const pool = JSON.parse(localStorage.getItem(poolKey) || '{}');
                const active = sessionStorage.getItem(activeKey) || Object.keys(pool)[0] || '';
                if (active && pool[active]) {
                    pool[active].access_token = 'bad.access';
                    pool[active].refresh_token = 'bad.refresh';
                    localStorage.setItem(poolKey, JSON.stringify(pool));
                }
            }""",
            [S.POOL_KEY, S.ACTIVE_KEY],
        )

    with allure.step("访问仪表盘触发鉴权失败链路"):
        page.goto(f"{frontend_url}/dashboard", wait_until="domcontentloaded")
        try:
            page.wait_for_url("**/login**", timeout=15000)
        except Exception:
            page.reload(wait_until="networkidle")
            page.wait_for_url("**/login**", timeout=15000)

    with allure.step("断言：被踢回 /login，当前账号已从池中移除"):
        assert "/login" in page.url
        pool = read_auth_pool(page)
        assert admin_creds["username"] not in pool
