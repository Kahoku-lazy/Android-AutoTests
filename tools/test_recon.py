"""Reconnaissance script for Android-AutoTests webapp."""
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    page = browser.new_page()

    # Capture console logs
    page.on("console", lambda msg: print(f"  [CONSOLE:{msg.type}] {msg.text}"))

    print("=" * 60)
    print("NAVIGATING to http://localhost:5173")
    print("=" * 60)

    page.goto('http://localhost:5173')
    page.wait_for_load_state('networkidle')
    page.wait_for_timeout(2000)  # Extra time for Vue SPA to render

    # What page are we on?
    print(f"\nCurrent URL: {page.url}")
    print(f"Page title: {page.title()}")

    # Take screenshot
    page.screenshot(path='D:/Kahoku/Android-AutoTests/test_screenshots/recon_home.png', full_page=True)
    print("\nScreenshot saved to test_screenshots/recon_home.png")

    # Discover all buttons
    buttons = page.locator('button').all()
    print(f"\n--- Buttons ({len(buttons)}) ---")
    for i, btn in enumerate(buttons):
        try:
            text = btn.inner_text().strip() if btn.is_visible() else "[hidden]"
            print(f"  [{i}] {text[:80]}")
        except:
            print(f"  [{i}] [error reading]")

    # Discover links
    links = page.locator('a[href]').all()
    print(f"\n--- Links ({len(links)}) ---")
    for link in links[:15]:
        try:
            text = link.inner_text().strip()
            href = link.get_attribute('href')
            if text:
                print(f"  - {text[:60]} -> {href}")
        except:
            pass

    # Discover inputs
    inputs = page.locator('input, textarea, select').all()
    print(f"\n--- Inputs ({len(inputs)}) ---")
    for inp in inputs:
        try:
            name = inp.get_attribute('name') or inp.get_attribute('id') or inp.get_attribute('placeholder') or "[unnamed]"
            itype = inp.get_attribute('type') or 'text'
            print(f"  - {name} ({itype})")
        except:
            pass

    # Discover navigation items (sidebar)
    nav_items = page.locator('.el-menu-item, nav a, [class*="nav"], [class*="sidebar"] a, [class*="menu"] li').all()
    print(f"\n--- Nav Items ({len(nav_items)}) ---")
    for item in nav_items[:20]:
        try:
            text = item.inner_text().strip()
            if text:
                print(f"  - {text[:80]}")
        except:
            pass

    # Discover headings
    headings = page.locator('h1, h2, h3, h4').all()
    print(f"\n--- Headings ({len(headings)}) ---")
    for h in headings:
        try:
            text = h.inner_text().strip()
            if text:
                print(f"  - {text[:80]}")
        except:
            pass

    # Check page content for login form or main content
    body_text = page.locator('body').inner_text()
    print(f"\n--- Body text preview (first 500 chars) ---")
    print(body_text[:500])

    browser.close()
    print("\n=== DONE ===")
