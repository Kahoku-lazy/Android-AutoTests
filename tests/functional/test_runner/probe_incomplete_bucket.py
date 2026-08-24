"""点「未完成」桶，验证 TEST-STOP 任务显示「已停止」。"""

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    page = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    page.set_default_timeout(30000)
    page.goto("http://localhost:5173/login", wait_until="networkidle")
    page.fill('input[placeholder="账号"]', "admin")
    page.fill('input[placeholder="密码"]', "admin123")
    page.click('button:has-text("登录")')
    page.wait_for_function("!location.pathname.startsWith('/login')")
    page.goto("http://localhost:5173/runner", wait_until="networkidle")
    page.wait_for_selector('button:has-text("＋ 新建任务")')
    page.wait_for_timeout(2500)
    tabs = page.locator("button.filter-tab").all_inner_texts()
    print("[tabs]", tabs)
    page.locator('button.filter-tab:has-text("未完成")').first.click()
    page.wait_for_timeout(1500)
    rows = page.locator(".el-table__row").all_inner_texts()
    mine = [r for r in rows if "TEST-STOP" in r]
    print("[未完成桶 行] " + (mine[0].replace("\n", " | ")[:240] if mine else "未找到"))
    if mine:
        print("[含'已停止'标签]", "已停止" in mine[0])
    b.close()
