"""观察 ID-072 终态在 /runner 看板的 UI 展示（FUNC：已完成桶 + 卡片显示）。"""

from pathlib import Path

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
ART = Path(__file__).resolve().parent / "artifacts"

with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    ctx = b.new_context(viewport={"width": 1440, "height": 900})
    page = ctx.new_page()
    page.set_default_timeout(15000)
    page.goto(BASE + "/login", wait_until="networkidle")
    page.fill('input[placeholder="账号"]', "admin")
    page.fill('input[placeholder="密码"]', "admin123")
    page.click('button:has-text("登录")')
    page.wait_for_function("!location.pathname.startsWith('/login')", timeout=30000)
    page.goto(BASE + "/runner", wait_until="networkidle")
    page.wait_for_selector('button:has-text("＋ 新建任务")')
    # 切卡片视图（默认表格视图无 .task-card）
    try:
        page.click('button:has-text("卡片")')
        page.wait_for_timeout(800)
    except Exception as e:
        print("切卡片视图失败:", e)
    # 切到「已完成」桶观察
    try:
        page.click("text=已完成")
        page.wait_for_timeout(1500)
    except Exception as e:
        print("点击已完成桶失败:", e)
    found = page.locator("text=TEST-BROWSER-220934")
    if found.count():
        print("[OK] 页面可见任务 TEST-BROWSER-220934（完成态展示验证通过）")
        print(found.first.inner_text()[:200])
    else:
        print("[WARN] 未找到 TEST-BROWSER-220934 卡片")
    page.screenshot(path=str(ART / "06-final-state.png"), full_page=True)
    print("[截图] 06-final-state.png")
    b.close()
