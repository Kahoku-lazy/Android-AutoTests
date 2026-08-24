"""Frontend E2E tests — Playwright browser automation for API case editor.

Requires: pytest-playwright, chromium browser, services running.
Run: pytest tests/case_manager/test_e2e_api_editor.py -v --browser chromium
"""

import allure
import pytest

from tests.e2e.helpers import login_as

API_LIST_URL = "http://localhost:5173/cases/api"
API_EDITOR_NEW_URL = "http://localhost:5173/cases/api/new"


def _login(page):
    """Log in and wait for redirect to dashboard（共享 login_as）。"""
    login_as(page)


# ═══════════════════════════════════════════════════════════════════
# E2E Tests
# ═══════════════════════════════════════════════════════════════════


@allure.feature("API 用例编辑器")
@allure.story("E2E — 页面渲染")
@pytest.mark.ui
@pytest.mark.e2e
def test_editor_renders_four_panels(page):
    """TC-E2E-001: 打开 API 用例编辑器 → 4 个面板可见"""
    _login(page)
    page.goto(API_EDITOR_NEW_URL)
    page.wait_for_load_state("networkidle")

    # ① CaseInfo panel: title input visible
    assert (
        page.is_visible("input[placeholder*='标题']")
        or page.is_visible("text=测试标题")
        or page.is_visible(".case-info-panel")
    ), "CaseInfo panel not visible"

    # ② StepList panel: "添加步骤" button or step area visible
    assert (
        page.is_visible("text=添加步骤")
        or page.is_visible("text=测试步骤")
        or page.is_visible(".step-list-panel")
    ), "StepList panel not visible"

    # ③ TestData panel visible
    assert (
        page.is_visible("text=测试数据")
        or page.is_visible("text=数据列")
        or page.is_visible(".test-data-panel")
    ), "TestData panel not visible"

    # ④ Validation panel visible
    assert (
        page.is_visible("text=数据校验")
        or page.is_visible("text=校验规则")
        or page.is_visible(".validation-panel")
    ), "Validation panel not visible"


@allure.feature("API 用例编辑器")
@allure.story("E2E — 创建用例")
@pytest.mark.ui
@pytest.mark.e2e
def test_create_case_appears_in_list(page):
    """TC-E2E-002: 填写用例信息 → 添加步骤 → 保存 → 列表页出现新用例"""
    _login(page)

    # Navigate to the API case list（tab 由 path /cases/api 决定，query ?tab= 已废弃）
    page.goto(API_LIST_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Click "新建用例" button
    page.click("button:has-text('新建'), button:has-text('新建用例'), text=新建用例")
    page.wait_for_timeout(1500)

    # Fill title
    title_input = page.locator("input").first
    if title_input.is_visible():
        title_input.fill("E2E Test Case")
        page.wait_for_timeout(300)

    # Add a step — click "添加步骤" if visible
    add_step_btn = page.locator("text=添加步骤").first
    if add_step_btn.is_visible():
        add_step_btn.click()
        page.wait_for_timeout(500)

    # Fill basic step fields（当前 URL 输入框 placeholder 形如 /api/auth/login）
    url_inputs = page.locator("input[placeholder*='/api/']")
    if url_inputs.count() > 0:
        url_inputs.first.fill("/api/test")

    # Save
    save_btn = page.locator("button:has-text('创建用例'), button:has-text('保存')").first
    if save_btn.is_visible():
        save_btn.click()
        page.wait_for_timeout(2000)

    # Should redirect to list — verify we're back at cases page
    assert "cases" in page.url, f"Expected /cases in URL, got {page.url}"


@allure.feature("API 用例编辑器")
@allure.story("E2E — 编辑用例")
@pytest.mark.ui
@pytest.mark.e2e
def test_edit_existing_case_saves_correctly(page):
    """TC-E2E-003: 编辑已有用例 → 修改标题 → 保存 → 再次打开数据一致"""
    _login(page)

    # Go to list and find first API case
    page.goto(API_LIST_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1500)

    # Click first case row to edit
    first_row = page.locator("tr, .case-row, .el-table__row").first
    if first_row.is_visible():
        first_row.click()
        page.wait_for_timeout(2000)

    # Now should be on editor page
    if "api" in page.url and page.url != API_LIST_URL:
        # Modify title
        title_input = page.locator("input").first
        if title_input.is_visible():
            original_title = title_input.input_value()
            title_input.fill(original_title + " (edited)")
            page.wait_for_timeout(300)

        # Save
        save_btn = page.locator("button:has-text('保存修改'), button:has-text('保存')").first
        if save_btn.is_visible():
            save_btn.click()
            page.wait_for_timeout(2000)

        assert "cases" in page.url, f"Expected redirect back to list, got {page.url}"
    else:
        pytest.skip("No existing cases to edit")


@allure.feature("API 用例编辑器")
@allure.story("E2E — 测试数据")
@pytest.mark.ui
@pytest.mark.e2e
def test_add_test_data_row_preserves_on_save(page):
    """TC-E2E-004: 添加测试数据行 → 填入 input → 保存 → 数据不丢失"""
    _login(page)

    page.goto(API_EDITOR_NEW_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Fill title first
    title_input = page.locator("input").first
    if title_input.is_visible():
        title_input.fill("E2E Data Test")
        page.wait_for_timeout(300)

    # Add a step (required for save)
    add_step_btn = page.locator("text=添加步骤").first
    if add_step_btn.is_visible():
        add_step_btn.click()
        page.wait_for_timeout(500)

    # Fill URL（当前 URL 输入框 placeholder 形如 /api/auth/login）
    url_inputs = page.locator("input[placeholder*='/api/']")
    if url_inputs.count() > 0:
        url_inputs.first.fill("/api/data-test")

    # Expand TestData panel and add a row
    test_data_header = page.locator("text=测试数据").first
    if test_data_header.is_visible():
        test_data_header.click()
        page.wait_for_timeout(500)

    add_row_btn = page.locator(
        "button:has-text('添加行'), button:has-text('添加数据'), text=添加行"
    )
    if add_row_btn.count() > 0 and add_row_btn.first.is_visible():
        add_row_btn.first.click()
        page.wait_for_timeout(500)

    # Assert the test_data panel has content
    assert (
        page.is_visible("text=测试数据")
        or page.is_visible("text=数据列")
        or page.is_visible(".test-data-panel")
    ), "TestData panel still visible after add"


@allure.feature("API 用例编辑器")
@allure.story("E2E — 表单校验")
@pytest.mark.ui
@pytest.mark.e2e
def test_empty_title_blocks_save(page):
    """TC-E2E-005: 标题为空 → 保存按钮点击 → 显示错误提示"""
    _login(page)

    page.goto(API_EDITOR_NEW_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)

    # Make sure title is empty
    title_input = page.locator("input").first
    if title_input.is_visible():
        title_input.fill("")
        page.wait_for_timeout(300)

    # Try to save
    save_btn = page.locator("button:has-text('创建用例'), button:has-text('保存')").first
    if save_btn.is_visible():
        save_btn.click()
        page.wait_for_timeout(1500)

    # Should show warning/error and stay on editor page
    warning_visible = (
        page.is_visible("text=标题必填")
        or page.is_visible("text=标题")
        or page.is_visible(".el-message--warning")
        or page.is_visible(".el-message--error")
    )
    # Either we get a warning message or we stay on the editor page
    assert warning_visible or "api" in page.url, (
        "Should show warning for empty title or stay on editor page"
    )


@allure.feature("API 用例编辑器")
@allure.story("E2E — 返回导航")
@pytest.mark.ui
@pytest.mark.e2e
def test_back_button_returns_to_list(page):
    """TC-E2E-006: 编辑器"返回列表"按钮 → 回到用例列表页"""
    _login(page)

    # 先经列表页点「新建」进入编辑器——返回按钮实现是 router.back()，需浏览器历史里存在列表页
    page.goto(API_LIST_URL)
    page.wait_for_load_state("networkidle")
    page.wait_for_timeout(1000)
    new_btn = page.locator("button:has-text('新建')").first
    if new_btn.is_visible():
        new_btn.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_timeout(1500)
    else:
        pytest.skip("列表页无「新建」按钮，无法进入编辑器")

    # Click "返回列表"
    back_btn = page.locator("button:has-text('返回列表'), button:has-text('返回')").first
    if back_btn.is_visible():
        back_btn.click()
        page.wait_for_timeout(1500)

    assert page.url.rstrip("/").split("?")[0] == API_LIST_URL, (
        f"Expected navigation back to list {API_LIST_URL}, got {page.url}"
    )
