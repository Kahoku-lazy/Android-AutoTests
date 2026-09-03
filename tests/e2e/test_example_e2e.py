"""黑盒·端到端测试示例 — 登录进入仪表盘。

演示 E2E 写法：data-testid 选择器 + 完整用户链路断言。
真实用例请按模块扩展。
"""

import pytest

from tests.e2e import selectors as S


@pytest.mark.e2e
@pytest.mark.auth
def test_login_and_enter_dashboard(page, e2e_services, admin_creds):
    frontend = e2e_services["frontend"]
    page.goto(f"{frontend}/login", wait_until="domcontentloaded")
    page.get_by_test_id(S.LOGIN_PAGE).wait_for(timeout=15000)
    page.get_by_test_id(S.LOGIN_USERNAME).locator("input").first.fill(admin_creds["username"])
    page.get_by_test_id(S.LOGIN_PASSWORD).locator("input").first.fill(admin_creds["password"])
    page.get_by_test_id(S.LOGIN_SUBMIT).click()
    page.wait_for_url("**/dashboard**", timeout=20000)
