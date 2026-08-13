"""跨 Tab 账号池 E2E — TC-E2E-TAB-001 ~ 002。"""

from __future__ import annotations

import allure
import pytest

from tests.auth.conftest import set_allure_metadata
from tests.e2e import selectors as S
from tests.e2e.helpers import (
    add_second_account_via_ui,
    login_as,
    logout_via_ui,
    read_auth_pool,
)


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_cross_tab_pool_shared(clean_page, frontend_url, admin_creds, context):
    """TC-E2E-TAB-001: 同 context 第二 page 共享 localStorage 账号池。"""
    set_allure_metadata(
        feature="认证模块",
        story="跨TabE2E",
        title="TC-E2E-TAB-001: 跨 Tab 账号池同步",
        description="Tab A 登录后，同 context 的 Tab B 读到同一 auth_accounts",
        severity="normal",
        tags=("auth", "e2e", "P1"),
    )
    page_a = clean_page
    login_as(
        page_a,
        admin_creds["username"],
        admin_creds["password"],
        frontend_url=frontend_url,
    )
    with allure.step("读取 Tab A 的账号池"):
        pool_a = read_auth_pool(page_a)
        assert admin_creds["username"] in pool_a

    with allure.step("同 context 打开 Tab B 访问 /dashboard"):
        page_b = context.new_page()
        page_b.goto(f"{frontend_url}/dashboard", wait_until="domcontentloaded")
    with allure.step("断言：Tab B 账号池与 Tab A 一致"):
        pool_b = read_auth_pool(page_b)
        assert pool_b == pool_a
        assert page_b.get_by_test_id(S.APP_SIDEBAR).is_visible() or "/login" in page_b.url
    page_b.close()


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_cross_tab_logout_clears_pool(clean_page, frontend_url, admin_creds, context):
    """TC-E2E-TAB-002: Tab A 登出后 Tab B 读到空池（storage 共享 + 可观测）。"""
    set_allure_metadata(
        feature="认证模块",
        story="跨TabE2E",
        title="TC-E2E-TAB-002: 跨 Tab 登出后池清空",
        description="Tab A/B 均登录态 → Tab A 退出唯一账号 → Tab B 的 auth_accounts 为空",
        severity="normal",
        tags=("auth", "e2e", "P1"),
    )
    page_a = clean_page
    login_as(
        page_a,
        admin_creds["username"],
        admin_creds["password"],
        frontend_url=frontend_url,
    )
    with allure.step("打开 Tab B 并确认已登录"):
        page_b = context.new_page()
        page_b.goto(f"{frontend_url}/dashboard", wait_until="domcontentloaded")
        page_b.get_by_test_id(S.APP_SIDEBAR).wait_for(timeout=15000)
        assert admin_creds["username"] in read_auth_pool(page_b)

    with allure.step("在 Tab A 退出登录"):
        page_a.bring_to_front()
        logout_via_ui(page_a)
        page_a.wait_for_url("**/login**", timeout=15000)

    with allure.step("断言：Tab B 的账号池已空"):
        page_b.bring_to_front()
        # 同 context 共享 localStorage；读池即可验证跨页一致性
        pool_b = read_auth_pool(page_b)
        assert pool_b == {} or admin_creds["username"] not in pool_b
    page_b.close()


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_cross_tab_add_account_visible_in_pool(
    clean_page, frontend_url, admin_creds, second_user, context
):
    """TC-E2E-TAB-003: Tab A 添加第二账号后，Tab B 池内可见两账号。"""
    set_allure_metadata(
        feature="认证模块",
        story="跨TabE2E",
        title="TC-E2E-TAB-003: 跨 Tab 加号后池同步",
        description="Tab A 添加第二账号 → Tab B 读取 auth_accounts 含两个 key",
        severity="normal",
        tags=("auth", "e2e", "P1"),
    )
    page_a = clean_page
    login_as(
        page_a,
        admin_creds["username"],
        admin_creds["password"],
        frontend_url=frontend_url,
    )
    with allure.step("打开 Tab B"):
        page_b = context.new_page()
        page_b.goto(f"{frontend_url}/dashboard", wait_until="domcontentloaded")
        page_b.get_by_test_id(S.APP_SIDEBAR).wait_for(timeout=15000)

    with allure.step("Tab A 添加第二账号"):
        page_a.bring_to_front()
        add_second_account_via_ui(
            page_a, frontend_url, second_user["username"], second_user["password"]
        )
        assert len(read_auth_pool(page_a)) >= 2

    with allure.step("断言：Tab B 池中也有两个账号"):
        page_b.bring_to_front()
        pool_b = read_auth_pool(page_b)
        assert admin_creds["username"] in pool_b
        assert second_user["username"] in pool_b
    page_b.close()
