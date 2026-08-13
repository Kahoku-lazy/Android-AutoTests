"""多账号 E2E — TC-E2E-SW-001 ~ 005。"""

from __future__ import annotations

import allure
import pytest

from tests.auth.conftest import set_allure_metadata
from tests.e2e import selectors as S
from tests.e2e.helpers import (
    add_second_account_via_ui,
    fetch_me_username,
    login_as,
    logout_via_ui,
    read_active_account,
    read_auth_pool,
    seed_empty_token_pool,
)


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_add_account_entry(clean_page, frontend_url, admin_creds):
    """TC-E2E-SW-001: 登录后点「添加账号」→ /login?add=1 + LoginCard。"""
    set_allure_metadata(
        feature="认证模块",
        story="多账号E2E",
        title="TC-E2E-SW-001: 侧边栏添加账号入口",
        description="打开账号菜单 → 添加账号 → URL 含 add=1，出现登录表单",
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
    with allure.step("打开账号菜单并点击「添加账号」"):
        page.get_by_test_id(S.SIDEBAR_ACCOUNT_MENU).click()
        page.get_by_test_id(S.SIDEBAR_ADD_ACCOUNT).click()
    with allure.step("断言：URL 含 add=1 且登录表单可见"):
        page.wait_for_url("**/login?add=1", timeout=10000)
        assert "add=1" in page.url
        assert page.get_by_test_id(S.LOGIN_SUBMIT).is_visible()


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_login_second_account(clean_page, frontend_url, admin_creds, second_user):
    """TC-E2E-SW-002: 在 ?add 页登录第二账号 → 池中 2 个 key。"""
    set_allure_metadata(
        feature="认证模块",
        story="多账号E2E",
        title="TC-E2E-SW-002: 添加第二账号入库",
        description="admin 登录后添加账号 → 登录 second_user → auth_accounts 含 2 个账号",
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
    add_second_account_via_ui(page, frontend_url, second_user["username"], second_user["password"])
    with allure.step("断言：账号池含两个账号，active 为第二账号"):
        pool = read_auth_pool(page)
        assert admin_creds["username"] in pool
        assert second_user["username"] in pool
        assert len(pool) >= 2
        assert read_active_account(page) == second_user["username"]


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_switch_account_in_sidebar(clean_page, frontend_url, admin_creds, second_user):
    """TC-E2E-SW-003: 侧边栏切换回原账号。"""
    set_allure_metadata(
        feature="认证模块",
        story="多账号E2E",
        title="TC-E2E-SW-003: 侧边栏切换账号",
        description="池内两账号时，菜单切换回 admin → active 变化且页面可用",
        severity="normal",
        tags=("auth", "e2e", "P1"),
    )
    page = clean_page
    login_as(
        page,
        admin_creds["username"],
        admin_creds["password"],
        frontend_url=frontend_url,
    )
    add_second_account_via_ui(page, frontend_url, second_user["username"], second_user["password"])
    with allure.step(f"在账号菜单中切换回「{admin_creds['username']}」"):
        page.get_by_test_id(S.SIDEBAR_ACCOUNT_MENU).click()
        page.get_by_test_id(f"sidebar-account-{admin_creds['username']}").click()
        page.wait_for_load_state("domcontentloaded")
        page.get_by_test_id(S.APP_SIDEBAR).wait_for(timeout=15000)
    with allure.step("断言：active 为 admin 且侧边栏可用"):
        assert read_active_account(page) == admin_creds["username"]
        assert "/dashboard" in page.url or page.get_by_test_id(S.APP_SIDEBAR).is_visible()
    with allure.step("断言：用当前 token 调 /me 返回 admin"):
        me_name = fetch_me_username(page)
        assert me_name == admin_creds["username"], f"/me 返回用户不符: {me_name}"


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_logout_keeps_remaining_account(clean_page, frontend_url, admin_creds, second_user):
    """TC-E2E-SW-004: 多账号时退出当前 → 仍留站内切到剩余账号。"""
    set_allure_metadata(
        feature="认证模块",
        story="多账号E2E",
        title="TC-E2E-SW-004: 多账号登出留人",
        description="池内两账号，退出当前（second）→ 不回登录页，active 切到 admin",
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
    add_second_account_via_ui(page, frontend_url, second_user["username"], second_user["password"])
    assert read_active_account(page) == second_user["username"]

    logout_via_ui(page)
    with allure.step("断言：未回登录页，侧边栏仍在，active 为剩余账号"):
        page.get_by_test_id(S.APP_SIDEBAR).wait_for(timeout=15000)
        assert "/login" not in page.url
        pool = read_auth_pool(page)
        assert second_user["username"] not in pool
        assert admin_creds["username"] in pool
        assert read_active_account(page) == admin_creds["username"]


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_account_switch_prompt(clean_page, frontend_url, admin_creds):
    """TC-E2E-SW-005: 有账号无有效 token 时出现 switchPrompt。"""
    set_allure_metadata(
        feature="认证模块",
        story="多账号E2E",
        title="TC-E2E-SW-005: AccountSwitchPrompt 可达",
        description="账号池有用户但 token 为空 → /login 显示 switchPrompt；点切换进 dashboard",
        severity="normal",
        tags=("auth", "e2e", "P1"),
    )
    page = clean_page
    with allure.step("构造「池内有账号、token 为空」状态并打开 /login"):
        seed_empty_token_pool(page, admin_creds["username"])
        page.goto(f"{frontend_url}/login", wait_until="domcontentloaded")
    with allure.step("断言：出现账号切换提示"):
        page.get_by_test_id(S.ACCOUNT_SWITCH_PROMPT).wait_for(timeout=10000)
        assert page.get_by_test_id(S.SWITCH_TO_EXISTING).is_visible()
    with allure.step("点击「添加新账号」，进入登录表单"):
        page.get_by_test_id(S.ADD_NEW_ACCOUNT).locator("button").first.click()
        page.get_by_test_id(S.LOGIN_SUBMIT).wait_for(state="visible", timeout=10000)
    with allure.step("断言：URL 含 add=1 且登录表单可见"):
        assert "add=1" in page.url
        assert page.get_by_test_id(S.LOGIN_SUBMIT).is_visible()
