"""枚举 /runner 的桶/tab 元素文本与 class。"""

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
    cands = page.eval_on_selector_all(
        "body *",
        """els => els.filter(e => e.children.length <= 2 && /(运行中|等待中|已完成|未完成|未执行|全部)/.test((e.innerText||'').trim()))
                 .map(e => ({tag: e.tagName, cls: (e.className||'').toString().slice(0,80), text: (e.innerText||'').trim().slice(0,24)}))""",
    )
    for c in cands[:12]:
        print(c)
    b.close()
