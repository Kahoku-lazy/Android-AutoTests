"""前端 E2E 浏览器操作 helper（可被各模块 import）。"""

from __future__ import annotations

import json
import os

import allure

from tests.e2e import selectors as S

FRONTEND_URL = os.environ.get("TEST_FRONTEND_URL", "http://localhost:5173")


def clear_auth(page, *, keep_saved_username: bool = False, frontend_url: str | None = None) -> None:
    """清除账号池与 active；默认同时清掉记住的用户名。"""
    base = (frontend_url or FRONTEND_URL).rstrip("/")
    with allure.step("清除浏览器认证状态" + ("（保留记住账号）" if keep_saved_username else "")):
        page.goto(f"{base}/login", wait_until="domcontentloaded")
        page.evaluate(
            """([poolKey, activeKey, savedKey, keepSaved]) => {
                localStorage.removeItem(poolKey);
                localStorage.removeItem('access_token');
                localStorage.removeItem('refresh_token');
                localStorage.removeItem('username');
                sessionStorage.removeItem(activeKey);
                if (!keepSaved) localStorage.removeItem(savedKey);
            }""",
            [S.POOL_KEY, S.ACTIVE_KEY, S.SAVED_USERNAME_KEY, keep_saved_username],
        )


def clear_auth_tokens_only(page, *, frontend_url: str | None = None) -> None:
    """只清 token 池，保留 saved_username。"""
    clear_auth(page, keep_saved_username=True, frontend_url=frontend_url)


def fill_by_testid(page, test_id: str, value: str) -> None:
    """testid 挂在包裹层上，填内部 native input。"""
    page.get_by_test_id(test_id).locator("input").first.fill(value)


def click_by_testid(page, test_id: str) -> None:
    """点击包裹层内的 button，若无则点包裹层本身。"""
    root = page.get_by_test_id(test_id)
    btn = root.locator("button")
    if btn.count() > 0:
        btn.first.click()
    else:
        root.click()


def set_remember_me(page, enabled: bool) -> None:
    """设置「记住账号」开关到目标状态。"""
    switch = page.get_by_test_id(S.LOGIN_REMEMBER).locator(".el-switch").first
    cls = switch.get_attribute("class") or ""
    is_on = "is-checked" in cls
    if enabled != is_on:
        switch.click()


def login_as(
    page,
    username: str = "admin",
    password: str = "admin123",
    *,
    frontend_url: str | None = None,
    remember: bool = False,
) -> None:
    """打开登录页 → 填写 → 提交 → 等待进入 dashboard。"""
    base = (frontend_url or FRONTEND_URL).rstrip("/")
    with allure.step(f"登录账号「{username}」" + ("（勾选记住账号）" if remember else "")):
        with allure.step("打开登录页 /login"):
            page.goto(f"{base}/login", wait_until="domcontentloaded")
            page.get_by_test_id(S.LOGIN_PAGE).wait_for(timeout=15000)
        with allure.step("填写用户名"):
            fill_by_testid(page, S.LOGIN_USERNAME, username)
        with allure.step("填写密码"):
            fill_by_testid(page, S.LOGIN_PASSWORD, password)
        if remember:
            with allure.step("勾选「记住账号」"):
                set_remember_me(page, True)
        with allure.step("点击登录并等待进入 /dashboard"):
            click_by_testid(page, S.LOGIN_SUBMIT)
            page.wait_for_url("**/dashboard**", timeout=20000)


def logout_via_ui(page) -> None:
    with allure.step("点击侧边栏「退出」"):
        click_by_testid(page, S.SIDEBAR_LOGOUT)


def read_auth_pool(page) -> dict:
    raw = page.evaluate(f"() => localStorage.getItem('{S.POOL_KEY}') || '{{}}'")
    return json.loads(raw)


def read_active_account(page) -> str:
    return page.evaluate(f"() => sessionStorage.getItem('{S.ACTIVE_KEY}') || ''")


def read_saved_username(page) -> str:
    return page.evaluate(f"() => localStorage.getItem('{S.SAVED_USERNAME_KEY}') || ''")


def corrupt_access_token(page, bogus: str = "expired.access.token") -> str:
    """把当前 active 账号的 access_token 改成无效值，保留 refresh_token。返回改前 token。"""
    with allure.step("伪造过期/无效的 access_token（保留 refresh）"):
        before = page.evaluate(
            """([poolKey, activeKey, bogus]) => {
                const pool = JSON.parse(localStorage.getItem(poolKey) || '{}');
                const active = sessionStorage.getItem(activeKey) || Object.keys(pool)[0] || '';
                const old = pool[active]?.access_token || '';
                if (active && pool[active]) {
                    pool[active].access_token = bogus;
                    localStorage.setItem(poolKey, JSON.stringify(pool));
                }
                return old;
            }""",
            [S.POOL_KEY, S.ACTIVE_KEY, bogus],
        )
        return before or ""


def seed_empty_token_pool(page, username: str) -> None:
    """写入「有账号、无有效 token」的池，用于触发 switchPrompt。"""
    with allure.step(f"写入账号池「{username}」且 access/refresh 为空（触发 switchPrompt）"):
        page.evaluate(
            """([poolKey, activeKey, username]) => {
                const pool = { [username]: { access_token: '', refresh_token: '' } };
                localStorage.setItem(poolKey, JSON.stringify(pool));
                sessionStorage.setItem(activeKey, username);
            }""",
            [S.POOL_KEY, S.ACTIVE_KEY, username],
        )


def add_second_account_via_ui(page, frontend_url: str, username: str, password: str) -> None:
    """侧边栏添加账号并登录第二用户。"""
    with allure.step(f"通过侧边栏添加并登录第二账号「{username}」"):
        with allure.step("打开账号菜单 → 添加账号"):
            page.get_by_test_id(S.SIDEBAR_ACCOUNT_MENU).click()
            page.get_by_test_id(S.SIDEBAR_ADD_ACCOUNT).click()
            page.wait_for_url("**/login**", timeout=10000)
        with allure.step("填写第二账号凭据并提交"):
            fill_by_testid(page, S.LOGIN_USERNAME, username)
            fill_by_testid(page, S.LOGIN_PASSWORD, password)
            click_by_testid(page, S.LOGIN_SUBMIT)
            page.wait_for_url("**/dashboard**", timeout=20000)


def fetch_me_username(page) -> str:
    """用当前 active access_token 调 /api/auth/me，返回 username。"""
    return page.evaluate(
        """([poolKey, activeKey]) => {
            const pool = JSON.parse(localStorage.getItem(poolKey) || '{}');
            const active = sessionStorage.getItem(activeKey) || Object.keys(pool)[0] || '';
            const token = pool[active]?.access_token || '';
            return fetch('/api/auth/me', {
                headers: { Authorization: 'Bearer ' + token }
            }).then(r => r.json()).then(body => {
                if (body && body.status && body.data?.user) return body.data.user.username || '';
                return body?.username || JSON.stringify(body);
            });
        }""",
        [S.POOL_KEY, S.ACTIVE_KEY],
    )
