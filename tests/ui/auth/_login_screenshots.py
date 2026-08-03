"""Login page UI test with step-by-step screenshots and click markers."""
import os
import sys
import io
import time
from datetime import datetime
from pathlib import Path

# Force UTF-8 output on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

from playwright.sync_api import sync_playwright

BASE_URL = "http://localhost:5173"
SCREENSHOT_DIR = Path(__file__).parent / "screenshots" / "login"


def ensure_dir() -> Path:
    """Create a timestamped output directory for this run."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    d = SCREENSHOT_DIR / ts
    d.mkdir(parents=True, exist_ok=True)
    return d


def step_screenshot(page, out_dir: Path, step_name: str, marker_x: int = None, marker_y: int = None):
    """Take a full-page screenshot. If coordinates given, inject a red dot marker."""
    if marker_x is not None and marker_y is not None:
        # Inject a visible red dot + label at the click position
        page.evaluate(
            f"""
            const dot = document.createElement('div');
            dot.id = '__test_marker';
            dot.style.cssText = 'position:fixed;z-index:99999;'
                + 'left:{marker_x - 12}px;top:{marker_y - 12}px;'
                + 'width:24px;height:24px;border-radius:50%;'
                + 'background:rgba(255,0,0,0.85);border:3px solid #fff;'
                + 'box-shadow:0 0 12px rgba(255,0,0,0.6);pointer-events:none;';
            const label = document.createElement('div');
            label.id = '__test_label';
            label.style.cssText = 'position:fixed;z-index:99999;'
                + 'left:{marker_x + 16}px;top:{marker_y - 10}px;'
                + 'background:#e00;color:#fff;padding:2px 8px;border-radius:4px;'
                + 'font:bold 12px sans-serif;pointer-events:none;white-space:nowrap;';
            label.textContent = '{step_name}';
            document.body.appendChild(dot);
            document.body.appendChild(label);
        """
        )
        page.wait_for_timeout(200)  # let marker render

    path = out_dir / f"{step_name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"  [screenshot] {step_name} → {path}")

    # Remove marker for next step
    page.evaluate(
        """
        const m = document.getElementById('__test_marker');
        const l = document.getElementById('__test_label');
        if (m) m.remove();
        if (l) l.remove();
    """
    )


def test_login():
    """Login flow: navigate → fill username → fill password → toggle remember → click login."""
    out_dir = ensure_dir()
    print(f"Screenshots: {out_dir}\n")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )
        page = context.new_page()

        # ── Step 1: Navigate to login page ──
        print("[1/5] Navigate to login page")
        page.goto(f"{BASE_URL}/login", wait_until="networkidle")
        page.wait_for_timeout(1000)
        step_screenshot(page, out_dir, "01_login_page_loaded")

        # ── Step 2: Fill username ──
        print("[2/5] Fill username")
        username_input = page.locator('input[placeholder="账号"]')
        username_input.wait_for(state="visible", timeout=5000)
        box = username_input.bounding_box()
        username_input.fill("admin")
        page.wait_for_timeout(500)
        step_screenshot(page, out_dir, "02_username_filled",
                        marker_x=int(box["x"] + box["width"] / 2),
                        marker_y=int(box["y"] + box["height"] / 2))

        # ── Step 3: Fill password ──
        print("[3/5] Fill password")
        password_input = page.locator('.login-form input[type="password"]')
        box = password_input.bounding_box()
        password_input.fill("admin123")
        page.wait_for_timeout(500)
        step_screenshot(page, out_dir, "03_password_filled",
                        marker_x=int(box["x"] + box["width"] / 2),
                        marker_y=int(box["y"] + box["height"] / 2))

        # ── Step 4: Toggle remember-me switch ──
        print("[4/5] Toggle remember-me")
        remember_switch = page.locator(".form-remember .el-switch")
        box = remember_switch.bounding_box()
        remember_switch.click()
        page.wait_for_timeout(500)
        step_screenshot(page, out_dir, "04_remember_toggled",
                        marker_x=int(box["x"] + box["width"] / 2),
                        marker_y=int(box["y"] + box["height"] / 2))

        # ── Step 5: Click login button ──
        print("[5/5] Click login button")
        login_btn = page.get_by_text("开始使用")
        login_btn.wait_for(state="visible", timeout=5000)
        box = login_btn.bounding_box()
        login_btn.click()
        page.wait_for_timeout(1500)

        # After login, should redirect to dashboard
        current_url = page.url
        step_screenshot(page, out_dir, "05_after_login_click",
                        marker_x=int(box["x"] + box["width"] / 2),
                        marker_y=int(box["y"] + box["height"] / 2))

        # ── Verify: should be on dashboard page ──
        if "/dashboard" in current_url or "/elements" in current_url:
            print(f"\n[OK] Login SUCCESS — redirected to: {current_url}")
        else:
            error_el = page.locator(".login-error")
            if error_el.is_visible():
                print(f"\n[WARN] Login returned error: {error_el.text_content()}")
            else:
                print(f"\n[WARN] Login: unexpected redirect to {current_url}")

        print(f"\nAll screenshots saved to: {out_dir}")
        browser.close()


if __name__ == "__main__":
    test_login()
