"""登录流 E2E — TC-E2E-LOGIN-001 ~ 008。"""

from __future__ import annotations

import allure
import pytest

from tests.auth.conftest import set_allure_metadata
from tests.e2e import selectors as S
from tests.e2e.helpers import (
    clear_auth_tokens_only,
    click_by_testid,
    fill_by_testid,
    login_as,
    logout_via_ui,
    read_saved_username,
    set_remember_me,
)


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_login_success(clean_page, frontend_url, admin_creds):
    """TC-E2E-LOGIN-001: 正确账号密码登录 → dashboard + 侧边栏。"""
    set_allure_metadata(
        feature="认证模块",
        story="登录E2E",
        title="TC-E2E-LOGIN-001: 正确账号密码登录",
        description="填写 admin 凭据 → 提交 → URL 进入 /dashboard，侧边栏可见",
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
    with allure.step("断言：URL 含 /dashboard 且侧边栏可见"):
        assert "/dashboard" in page.url
        assert page.get_by_test_id(S.APP_SIDEBAR).is_visible()


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_login_wrong_password(clean_page, frontend_url, admin_creds):
    """TC-E2E-LOGIN-002: 密码错误 → 错误遮罩，仍停在 /login。"""
    set_allure_metadata(
        feature="认证模块",
        story="登录E2E",
        title="TC-E2E-LOGIN-002: 密码错误显示遮罩",
        description="错误密码提交 → 遮罩文案含「用户名或密码错误」，URL 仍为 /login",
        severity="critical",
        tags=("auth", "e2e", "P0"),
    )
    page = clean_page
    with allure.step("打开登录页"):
        page.goto(f"{frontend_url}/login", wait_until="domcontentloaded")
    with allure.step("填写正确用户名 + 错误密码"):
        fill_by_testid(page, S.LOGIN_USERNAME, admin_creds["username"])
        fill_by_testid(page, S.LOGIN_PASSWORD, "wrong-password-xxx")
    with allure.step("点击登录"):
        click_by_testid(page, S.LOGIN_SUBMIT)
    with allure.step("断言：错误遮罩出现且文案正确，仍在登录页"):
        page.get_by_test_id(S.LOGIN_ERROR_OVERLAY).wait_for(timeout=10000)
        msg = page.get_by_test_id(S.LOGIN_ERROR_MESSAGE).inner_text()
        assert "用户名或密码错误" in msg
        assert "/login" in page.url


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_remember_username(clean_page, frontend_url, admin_creds):
    """TC-E2E-LOGIN-003: 记住账号 → 清 token 再开登录页 → 用户名预填。"""
    set_allure_metadata(
        feature="认证模块",
        story="登录E2E",
        title="TC-E2E-LOGIN-003: 记住账号刷新预填",
        description="勾选记住账号登录 → 仅清 token → 再打开 /login → 用户名预填",
        severity="normal",
        tags=("auth", "e2e", "P1"),
    )
    page = clean_page
    login_as(
        page,
        admin_creds["username"],
        admin_creds["password"],
        frontend_url=frontend_url,
        remember=True,
    )
    with allure.step("仅清除 token，保留 saved_username"):
        clear_auth_tokens_only(page, frontend_url=frontend_url)
    with allure.step("再次打开登录页"):
        page.goto(f"{frontend_url}/login", wait_until="domcontentloaded")
        page.get_by_test_id(S.LOGIN_PAGE).wait_for(timeout=10000)
    with allure.step("断言：用户名输入框预填为 admin"):
        value = page.get_by_test_id(S.LOGIN_USERNAME).locator("input").input_value()
        assert value == admin_creds["username"]


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_guard_redirects_unauthenticated(clean_page, frontend_url):
    """TC-E2E-LOGIN-004: 未登录访问 /dashboard → 踢回 /login。"""
    set_allure_metadata(
        feature="认证模块",
        story="登录E2E",
        title="TC-E2E-LOGIN-004: 未登录访问受保护路由",
        description="无 token 访问 /dashboard → 路由守卫踢回 /login",
        severity="critical",
        tags=("auth", "e2e", "P0"),
    )
    page = clean_page
    with allure.step("未登录状态下访问 /dashboard"):
        page.goto(f"{frontend_url}/dashboard", wait_until="domcontentloaded")
    with allure.step("断言：被踢回 /login"):
        page.wait_for_url("**/login**", timeout=10000)
        assert "/login" in page.url


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_logged_in_visits_login_redirects(clean_page, frontend_url, admin_creds):
    """TC-E2E-LOGIN-005: 已登录再访问 /login（无 ?add）→ /dashboard。"""
    set_allure_metadata(
        feature="认证模块",
        story="登录E2E",
        title="TC-E2E-LOGIN-005: 已登录访问登录页重定向",
        description="有 token 访问 /login（无 add）→ 重定向 /dashboard",
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
    with allure.step("已登录状态下访问 /login（无 add 参数）"):
        page.goto(f"{frontend_url}/login", wait_until="domcontentloaded")
    with allure.step("断言：重定向到 /dashboard"):
        page.wait_for_url("**/dashboard**", timeout=10000)
        assert "/dashboard" in page.url


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_logout_then_guard(clean_page, frontend_url, admin_creds):
    """TC-E2E-LOGIN-006: 登录 → 登出 → 再访受保护页仍被踢。"""
    set_allure_metadata(
        feature="认证模块",
        story="登录E2E",
        title="TC-E2E-LOGIN-006: 登出后再访问受保护路由",
        description="UI 退出 → /login；再访问 /dashboard → 仍踢回登录",
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
    logout_via_ui(page)
    with allure.step("断言：退出后回到 /login"):
        page.wait_for_url("**/login**", timeout=15000)
        assert "/login" in page.url
    with allure.step("再次访问 /dashboard"):
        page.goto(f"{frontend_url}/dashboard", wait_until="domcontentloaded")
    with allure.step("断言：仍被踢回 /login"):
        page.wait_for_url("**/login**", timeout=10000)
        assert "/login" in page.url


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_uncheck_remember_clears_saved(clean_page, frontend_url, admin_creds):
    """TC-E2E-LOGIN-007: 取消记住账号后，下次不再预填。"""
    set_allure_metadata(
        feature="认证模块",
        story="登录E2E",
        title="TC-E2E-LOGIN-007: 取消记住账号清除预填",
        description="先记住账号登录 → 再以取消记住方式登录 → 清 token 后用户名不再预填",
        severity="normal",
        tags=("auth", "e2e", "P1"),
    )
    page = clean_page
    login_as(
        page,
        admin_creds["username"],
        admin_creds["password"],
        frontend_url=frontend_url,
        remember=True,
    )
    logout_via_ui(page)
    page.wait_for_url("**/login**", timeout=15000)

    with allure.step("再次登录并关闭「记住账号」"):
        fill_by_testid(page, S.LOGIN_USERNAME, admin_creds["username"])
        fill_by_testid(page, S.LOGIN_PASSWORD, admin_creds["password"])
        set_remember_me(page, False)
        click_by_testid(page, S.LOGIN_SUBMIT)
        page.wait_for_url("**/dashboard**", timeout=20000)

    with allure.step("仅清 token 后重开登录页"):
        clear_auth_tokens_only(page, frontend_url=frontend_url)
        page.goto(f"{frontend_url}/login", wait_until="domcontentloaded")
        page.get_by_test_id(S.LOGIN_PAGE).wait_for(timeout=10000)

    with allure.step("断言：saved_username 已清除且输入框为空"):
        assert read_saved_username(page) == ""
        value = page.get_by_test_id(S.LOGIN_USERNAME).locator("input").input_value()
        assert value == ""


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_login_network_error_overlay(clean_page, frontend_url, admin_creds):
    """TC-E2E-LOGIN-008: 登录接口不可达 → 错误遮罩。"""
    set_allure_metadata(
        feature="认证模块",
        story="登录E2E",
        title="TC-E2E-LOGIN-008: 网络/后端不可用错误遮罩",
        description="拦截登录 API 请求失败 → 出现错误遮罩，仍停在 /login",
        severity="critical",
        tags=("auth", "e2e", "P0"),
    )
    page = clean_page

    def abort_login(route):
        route.abort("failed")

    with allure.step("拦截 POST /api/auth/login 使其失败"):
        page.route("**/api/auth/login", abort_login)

    with allure.step("打开登录页并提交合法凭据"):
        page.goto(f"{frontend_url}/login", wait_until="domcontentloaded")
        fill_by_testid(page, S.LOGIN_USERNAME, admin_creds["username"])
        fill_by_testid(page, S.LOGIN_PASSWORD, admin_creds["password"])
        click_by_testid(page, S.LOGIN_SUBMIT)

    with allure.step("断言：错误遮罩出现且仍在登录页"):
        page.get_by_test_id(S.LOGIN_ERROR_OVERLAY).wait_for(timeout=10000)
        msg = page.get_by_test_id(S.LOGIN_ERROR_MESSAGE).inner_text()
        assert msg  # 网络失败走 fallback，不暴露技术栈细节即可
        assert "/login" in page.url

    page.unroute("**/api/auth/login")
