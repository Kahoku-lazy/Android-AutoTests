"""
Real browser end-to-end smoke test for Web executor.

This is the ONE test that proves the Web automation module actually works.
All 228 mock tests pass → meaningless if this one fails.
"""
import pytest
import asyncio


@pytest.mark.slow
@pytest.mark.e2e
class TestWebExecutorRealBrowser:
    """End-to-end: start Playwright → navigate → interact → verify."""

    @pytest.mark.asyncio
    async def test_login_page_loads(self):
        """Can Playwright start and open the login page?"""
        from apps.test_runner.executors.web.adapter import WebAdapter, _pw_run

        adapter = WebAdapter()
        try:
            await adapter._ensure_browser()
            await adapter._navigate("http://localhost:5173/login")

            content = await _pw_run(adapter._page.content)
            assert len(content) > 100, "Page should have meaningful content"
        finally:
            await adapter.close()

    @pytest.mark.asyncio
    async def test_login_form_submit(self):
        """Fill login form → click submit → verify navigation."""
        from apps.test_runner.executors.web.adapter import WebAdapter, _pw_run

        adapter = WebAdapter()
        try:
            await adapter._ensure_browser()
            await adapter._navigate("http://localhost:5173/login")
            await adapter._fill('input[placeholder="账号"]', "admin")
            await adapter._fill('.login-form input[type="password"]', "admin123")
            await adapter._click(".login-form .el-button--primary")
            await asyncio.sleep(2)

            url = await _pw_run(lambda: adapter._page.url)
            # After login, should not be on the login page anymore
            assert "login" not in (url or "").lower(), (
                f"Still on login page after submit: {url}"
            )
        finally:
            await adapter.close()

    @pytest.mark.asyncio
    async def test_full_web_executor_pipeline(self):
        """Execute a complete test case through WebExecutor."""
        from apps.test_runner.executors.web.adapter import WebAdapter
        from apps.test_runner.executors.web.executor import WebExecutor
        from models.test_models import TestCaseDef
        from models.step_types import TestStep

        adapter = WebAdapter()
        executor = WebExecutor(adapter)

        steps = [
            TestStep(type="web_navigate", url="http://localhost:5173/login",
                     description="打开登录页"),
            TestStep(type="web_wait", timeout=2.0,
                     description="等待页面渲染"),
            TestStep(type="web_fill", selector='input[placeholder="账号"]',
                     value="admin", description="输入账号"),
            TestStep(type="web_fill", selector='.login-form input[type="password"]',
                     value="admin123", description="输入密码"),
            TestStep(type="web_click", selector=".login-form .el-button--primary",
                     description="点击登录"),
            TestStep(type="web_wait", timeout=3.0,
                     description="等待跳转"),
        ]
        case = TestCaseDef(
            id="E2E-LOGIN-001", title="真实浏览器登录测试",
            category="web", steps_data=steps, enabled=True,
            task_type="web_automation",
        )

        try:
            result = await executor.execute_case(case, iteration=1, run_id="e2e-001")
            assert result == "pass", (
                f"Login test failed: {result}. "
                f"Step details: {executor._last_step_details}"
            )
            assert len(executor._last_step_details) == 6, (
                f"Expected 6 step_details, got {len(executor._last_step_details)}"
            )
            # All steps should pass
            failures = [d for d in executor._last_step_details if d["result"] != "pass"]
            assert not failures, f"Some steps failed: {failures}"
        finally:
            await adapter.close()
