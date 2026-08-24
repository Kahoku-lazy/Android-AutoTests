"""抽取 /runner 页面任务区文本，验证 TEST-BROWSER 任务的展示状态。"""

from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"

with sync_playwright() as p:
    b = p.chromium.launch(headless=False)
    page = b.new_context(viewport={"width": 1440, "height": 900}).new_page()
    page.set_default_timeout(30000)
    page.goto(BASE + "/login", wait_until="networkidle")
    page.fill('input[placeholder="账号"]', "admin")
    page.fill('input[placeholder="密码"]', "admin123")
    page.click('button:has-text("登录")')
    page.wait_for_function("!location.pathname.startsWith('/login')", timeout=30000)
    page.goto(BASE + "/runner", wait_until="networkidle")
    page.wait_for_selector('button:has-text("＋ 新建任务")')
    page.wait_for_timeout(2500)
    # 枚举含"已完成"文本的可点元素
    cands = page.eval_on_selector_all(
        "body *",
        """els => els.filter(e => e.children.length <= 2 && (e.innerText||'').trim().startsWith('已完成'))
                 .map(e => ({tag: e.tagName, cls: e.className.slice(0,60), text: (e.innerText||'').trim().slice(0,30)}))""",
    )
    print("[已完成候选] " + str(cands[:8]))
    # 点击 tab（若有 class 含 tab 的候选则用它）
    tab = page.locator('.filter-tab:has-text("已完成"), [class*="tab"]:has-text("已完成")').first
    if tab.count():
        tab.click()
        page.wait_for_timeout(2000)
        print("[已点击 已完成 tab]")
    # 表格行文本（含状态列）
    rows = page.locator(".el-table__row").all_inner_texts()
    print(f"[表格行数] {len(rows)}")
    for r in rows:
        if "TEST-BROWSER" in r or "01-启动" in r:
            print("[行] " + r.replace("\n", " | ")[:220])
    body = page.inner_text("body")
    print("[含 TEST-BROWSER]", "TEST-BROWSER-220934" in body)
    idx = body.find("TEST-BROWSER-220934")
    if idx >= 0:
        print("[上下文] " + body[max(0, idx - 100) : idx + 140].replace("\n", " | "))
    b.close()
