"""注册流 E2E — TC-E2E-REG-001 ~ 003。"""

from __future__ import annotations

import time
import uuid

import allure
import pytest

from tests.auth.conftest import set_allure_metadata
from tests.e2e import selectors as S
from tests.e2e.helpers import click_by_testid, fill_by_testid


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_register_success(clean_page, frontend_url):
    """TC-E2E-REG-001: 注册新用户 → 自动进 dashboard。"""
    set_allure_metadata(
        feature="认证模块",
        story="注册E2E",
        title="TC-E2E-REG-001: 注册成功自动登录",
        description="填写合法注册表单 → 提交 → URL 进入 /dashboard",
        severity="blocker",
        tags=("auth", "e2e", "P0"),
    )
    page = clean_page
    username = f"E2E-{int(time.time())}-{uuid.uuid4().hex[:4]}"
    password = "E2ePass123"
    email = f"{username}@example.com"

    with allure.step("打开登录页并切换到注册"):
        page.goto(f"{frontend_url}/login", wait_until="domcontentloaded")
        page.get_by_test_id(S.LOGIN_TO_REGISTER).click()
        page.get_by_test_id(S.REGISTER_USERNAME).wait_for(timeout=5000)
    with allure.step(f"填写注册表单（用户名 {username}）"):
        fill_by_testid(page, S.REGISTER_USERNAME, username)
        fill_by_testid(page, S.REGISTER_EMAIL, email)
        fill_by_testid(page, S.REGISTER_PASSWORD, password)
        fill_by_testid(page, S.REGISTER_PASSWORD2, password)
    with allure.step("提交注册并等待进入仪表盘"):
        click_by_testid(page, S.REGISTER_SUBMIT)
        page.wait_for_url("**/dashboard**", timeout=20000)
    with allure.step("断言：侧边栏可见"):
        assert page.get_by_test_id(S.APP_SIDEBAR).is_visible()


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_toggle_login_register(clean_page, frontend_url):
    """TC-E2E-REG-002: 登录 ↔ 注册视图切换。"""
    set_allure_metadata(
        feature="认证模块",
        story="注册E2E",
        title="TC-E2E-REG-002: 登录注册视图切换",
        description="点「去注册」出现注册表单；点「去登录」回到登录表单",
        severity="normal",
        tags=("auth", "e2e", "P1"),
    )
    page = clean_page
    with allure.step("打开登录页，确认登录表单可见"):
        page.goto(f"{frontend_url}/login", wait_until="domcontentloaded")
        page.get_by_test_id(S.LOGIN_SUBMIT).wait_for(state="visible", timeout=10000)
    with allure.step("点击「去注册」，确认注册表单可见"):
        page.get_by_test_id(S.LOGIN_TO_REGISTER).click()
        page.get_by_test_id(S.REGISTER_SUBMIT).wait_for(state="visible", timeout=5000)
    with allure.step("点击「去登录」，确认回到登录表单"):
        page.get_by_test_id(S.REGISTER_TO_LOGIN).click()
        page.get_by_test_id(S.LOGIN_SUBMIT).wait_for(state="visible", timeout=5000)


@pytest.mark.e2e
@pytest.mark.ui
@pytest.mark.auth
def test_register_duplicate_username(clean_page, frontend_url, admin_creds):
    """TC-E2E-REG-003: 注册已存在用户名 → 错误遮罩。"""
    set_allure_metadata(
        feature="认证模块",
        story="注册E2E",
        title="TC-E2E-REG-003: 注册重复用户名失败",
        description="使用已存在的 admin 用户名注册 → 错误遮罩，仍停在注册页",
        severity="critical",
        tags=("auth", "e2e", "P1"),
    )
    page = clean_page
    with allure.step("打开登录页并切换到注册"):
        page.goto(f"{frontend_url}/login", wait_until="domcontentloaded")
        page.get_by_test_id(S.LOGIN_TO_REGISTER).click()
        page.get_by_test_id(S.REGISTER_USERNAME).wait_for(timeout=5000)
    with allure.step("填写与 admin 冲突的注册表单"):
        fill_by_testid(page, S.REGISTER_USERNAME, admin_creds["username"])
        fill_by_testid(page, S.REGISTER_EMAIL, "admin-dup@example.com")
        fill_by_testid(page, S.REGISTER_PASSWORD, "E2ePass123")
        fill_by_testid(page, S.REGISTER_PASSWORD2, "E2ePass123")
    with allure.step("提交注册"):
        click_by_testid(page, S.REGISTER_SUBMIT)
    with allure.step("断言：错误遮罩出现，未进入 dashboard"):
        page.get_by_test_id(S.LOGIN_ERROR_OVERLAY).wait_for(timeout=10000)
        msg = page.get_by_test_id(S.LOGIN_ERROR_MESSAGE).inner_text()
        assert msg
        assert "/dashboard" not in page.url
