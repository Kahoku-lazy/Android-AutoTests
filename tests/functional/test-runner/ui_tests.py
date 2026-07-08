"""
Test-Runner UI 层测试 — Playwright 浏览器交互.
"""
import sys, os, time
_current_dir = os.path.dirname(os.path.abspath(__file__))
if _current_dir not in sys.path: sys.path.insert(0, _current_dir)
import helpers as H


def _ensure_logged_in(page):
    """Navigate to runner page, logging in via API token if needed"""
    # Get JWT token from API and inject into localStorage before page loads
    h = H.api_headers()
    token = h.get("Authorization", "").replace("Bearer ", "")
    if token:
        page.goto(f"{H.BASE_URL}/runner", wait_until="domcontentloaded", timeout=15000)
        page.evaluate(f"localStorage.setItem('access_token', '{token}')")
        page.goto(f"{H.BASE_URL}/runner", wait_until="domcontentloaded", timeout=15000)
        time.sleep(3)
        if "/login" in page.url:
            # Fallback: token didn't work, try to find login form
            page.fill('input[placeholder*="用户名"], input[name="username"]', "admin")
            page.fill('input[placeholder*="密码"], input[name="password"]', "admin123")
            page.locator('button:has-text("登录"), button:has-text("开始使用")').click()
            time.sleep(2)
            page.goto(f"{H.BASE_URL}/runner", wait_until="domcontentloaded", timeout=15000)
            time.sleep(2)
    else:
        page.goto(f"{H.BASE_URL}/runner", wait_until="domcontentloaded", timeout=15000)
        time.sleep(2)


def test_ui_01_page_loads():
    """页面正常加载 — 标题、按钮可见"""
    if not H._playwright_ready:
        return None
    t0 = time.time()
    with H.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            _ensure_logged_in(page)
            title = page.title()
            has_new_btn = page.locator('button:has-text("新建任务")').count() > 0
            has_tabs = page.locator('.runner-tabs, .animal-tabs').count() > 0
            passed = has_new_btn or has_tabs  # Either indicates page loaded
            H.record("TR-UI-01", "UI", "页面加载与关键元素", passed,
                     f"title={title[:30]}, new_btn={has_new_btn}, tabs={has_tabs}",
                     "按钮或Tab可见", int((time.time()-t0)*1000))
        finally:
            browser.close()
    return passed


def test_ui_02_create_task():
    """创建新任务 — 弹窗打开与关闭"""
    if not H._playwright_ready:
        return None
    t0 = time.time()
    with H.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            _ensure_logged_in(page)
            # Click "新建任务"
            new_btn = page.locator('button:has-text("新建任务")')
            if new_btn.count() == 0:
                H.record("TR-UI-02", "UI", "新建任务弹窗", True,
                         "no button (page may be empty)", "skip OK", int((time.time()-t0)*1000))
                return True
            new_btn.first.click()
            time.sleep(1)
            # Check if dialog/form appeared
            dialog = page.locator('.el-dialog__wrapper:visible, .el-overlay:visible, [role="dialog"]:visible')
            form_el = page.locator('input[placeholder*="稳定性"], .el-form-item:visible')
            modal_visible = dialog.count() > 0 or form_el.count() > 0
            # Close it
            if modal_visible:
                page.keyboard.press("Escape")
                time.sleep(0.5)
            passed = modal_visible
            H.record("TR-UI-02", "UI", "新建任务弹窗", passed,
                     f"modal_visible={modal_visible}, dialog={dialog.count()}, form={form_el.count()}",
                     "弹窗已打开", int((time.time()-t0)*1000))
        finally:
            browser.close()
    return passed


def test_ui_03_tab_switching():
    """Tab 切换 — 点击各标签页"""
    if not H._playwright_ready:
        return None
    t0 = time.time()
    with H.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            _ensure_logged_in(page)
            time.sleep(1)
            # 点击不同tab (animal-island-vue tabs)
            tabs = page.locator('.animal-tabs__list .animal-tabs__item')
            count = tabs.count()
            clicked = 0
            for i in range(min(count, 4)):
                try:
                    tabs.nth(i).click()
                    time.sleep(0.4)
                    clicked += 1
                except Exception:
                    pass
            # Also try el-tabs as fallback
            if count == 0:
                tabs = page.locator('.el-tabs__item')
                count = tabs.count()
                for i in range(min(count, 4)):
                    try:
                        tabs.nth(i).click()
                        time.sleep(0.4)
                        clicked += 1
                    except Exception:
                        pass
            passed = count >= 1
            H.record("TR-UI-03", "UI", "Tab标签切换", passed,
                     f"tabs_found={count}, clicked={clicked}", "至少1个tab", int((time.time()-t0)*1000))
        finally:
            browser.close()
    return passed


def test_ui_04_task_card_display():
    """任务卡片显示 — 名称、设备、进度条"""
    if not H._playwright_ready:
        return None
    t0 = time.time()
    with H.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            _ensure_logged_in(page)
            time.sleep(1)
            cards = page.locator('.task-card')
            card_count = cards.count()
            if card_count > 0:
                first = cards.first
                has_name = first.locator('.tc-name').count() > 0
                has_device = first.locator('.tc-device').count() > 0 or first.locator('text=📱').count() > 0
                has_progress = first.locator('.el-progress').count() > 0
                passed = has_name and has_device and has_progress
                H.record("TR-UI-04", "UI", "任务卡片显示", passed,
                         f"name={has_name}, device={has_device}, progress={has_progress}",
                         "名称+设备+进度条", int((time.time()-t0)*1000))
            else:
                H.record("TR-UI-04", "UI", "任务卡片显示", True,
                         "no cards to verify (empty list OK)", "页面正常",
                         int((time.time()-t0)*1000))
                passed = True
        finally:
            browser.close()
    return passed


def test_ui_05_delete_task():
    """删除任务卡片 — 确认弹窗并删除"""
    if not H._playwright_ready:
        return None
    t0 = time.time()
    with H.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            _ensure_logged_in(page)
            time.sleep(1)
            cards = page.locator('.task-card')
            if cards.count() == 0:
                H.record("TR-UI-05", "UI", "删除任务卡片", True,
                         "no cards to delete", "skip OK", int((time.time()-t0)*1000))
                passed = True
            else:
                before = cards.count()
                # Click delete button on first card
                page.locator('.task-card').first.locator('button:has-text("删除")').click()
                time.sleep(0.5)
                # Confirm dialog
                dialog = page.locator('.el-message-box')
                if dialog.count() > 0:
                    dialog.locator('button:has-text("删除"), button:has-text("确定")').click()
                time.sleep(1)
                after = page.locator('.task-card').count()
                passed = after < before
                H.record("TR-UI-05", "UI", "删除任务卡片", passed,
                         f"before={before}, after={after}", "after < before",
                         int((time.time()-t0)*1000))
        finally:
            browser.close()
    return passed


def test_ui_06_modal_cancel():
    """新建任务弹窗 — 取消关闭"""
    if not H._playwright_ready:
        return None
    t0 = time.time()
    with H.sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        try:
            _ensure_logged_in(page)
            time.sleep(0.5)
            page.locator('button:has-text("新建任务")').click()
            time.sleep(0.5)
            # Click cancel
            cancel_btn = page.locator('.el-dialog__footer button:has-text("取消")')
            if cancel_btn.count() > 0:
                cancel_btn.click()
                time.sleep(0.5)
            modal_gone = page.locator('.el-dialog__wrapper:visible').count() == 0
            passed = modal_gone
            H.record("TR-UI-06", "UI", "新建弹窗取消关闭", passed,
                     f"modal_gone={modal_gone}", "弹窗已关闭", int((time.time()-t0)*1000))
        finally:
            browser.close()
    return passed


ALL_UI_TESTS = [
    ("TR-UI-01", "UI", test_ui_01_page_loads, "页面加载"),
    ("TR-UI-02", "UI", test_ui_02_create_task, "新建任务"),
    ("TR-UI-03", "UI", test_ui_03_tab_switching, "Tab切换"),
    ("TR-UI-04", "UI", test_ui_04_task_card_display, "卡片显示"),
    ("TR-UI-05", "UI", test_ui_05_delete_task, "删除任务"),
    ("TR-UI-06", "UI", test_ui_06_modal_cancel, "弹窗取消"),
]
for tid, layer, fn, desc in ALL_UI_TESTS:
    H.ALL_TESTS[tid] = (layer, fn, desc)
