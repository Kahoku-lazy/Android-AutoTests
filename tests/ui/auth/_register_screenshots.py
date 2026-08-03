"""Register page UI test with step-by-step screenshots and click markers."""
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
SCREENSHOT_DIR = Path(__file__).parent / "screenshots" / "register"


def ensure_dir() -> Path:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    d = SCREENSHOT_DIR / ts
    d.mkdir(parents=True, exist_ok=True)
    return d


def step_screenshot(page, out_dir: Path, step_name: str, marker_x: int = None, marker_y: int = None):
    """Take a full-page screenshot with optional red-dot click marker."""
    if marker_x is not None and marker_y is not None:
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
        page.wait_for_timeout(200)

    path = out_dir / f"{step_name}.png"
    page.screenshot(path=str(path), full_page=True)
    print(f"  [screenshot] {step_name} → {path}")

    # Clean marker
    page.evaluate(
        """
        const m = document.getElementById('__test_marker');
        const l = document.getElementById('__test_label');
        if (m) m.remove();
        if (l) l.remove();
    """
    )


def test_register():
    """Register flow: navigate → switch to register → fill fields → submit."""
    out_dir = ensure_dir()
    print(f"Screenshots: {out_dir}\n")

    # Generate a unique test username to avoid conflicts
    test_user = f"testuser_{int(time.time()) % 100000}"
    test_pass = "test123456"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=300)
        context = browser.new_context(
            viewport={"width": 1440, "height": 900},
            locale="zh-CN",
        )
        page = context.new_page()

        # ── Step 1: Navigate to login page ──
        print("[1/6] Navigate to login page")
        page.goto(f"{BASE_URL}/login?add=1", wait_until="networkidle")
        page.wait_for_timeout(1000)
        step_screenshot(page, out_dir, "01_login_page_loaded")

        # ── Step 2: Click "去注册" link to switch to register mode ──
        print("[2/6] Switch to register mode")
        register_link = page.get_by_text("去注册")
        register_link.wait_for(state="visible", timeout=5000)
        box = register_link.bounding_box()
        register_link.click()
        page.wait_for_timeout(800)
        step_screenshot(page, out_dir, "02_switched_to_register",
                        marker_x=int(box["x"] + box["width"] / 2),
                        marker_y=int(box["y"] + box["height"] / 2))

        # ── Step 3: Fill username ──
        print(f"[3/6] Fill username: {test_user}")
        username_input = page.locator('input[placeholder*="设置账号"]')
        username_input.wait_for(state="visible", timeout=5000)
        box = username_input.bounding_box()
        username_input.fill(test_user)
        page.wait_for_timeout(500)
        step_screenshot(page, out_dir, "03_username_filled",
                        marker_x=int(box["x"] + box["width"] / 2),
                        marker_y=int(box["y"] + box["height"] / 2))

        # ── Step 4: Fill password ──
        print("[4/6] Fill password")
        password_input = page.locator('.login-form input[placeholder*="设置密码"]')
        box = password_input.bounding_box()
        password_input.fill(test_pass)
        page.wait_for_timeout(500)
        step_screenshot(page, out_dir, "04_password_filled",
                        marker_x=int(box["x"] + box["width"] / 2),
                        marker_y=int(box["y"] + box["height"] / 2))

        # ── Step 5: Fill confirm password ──
        print("[5/6] Fill confirm password")
        confirm_input = page.locator('input[placeholder="确认密码"]')
        box = confirm_input.bounding_box()
        confirm_input.fill(test_pass)
        page.wait_for_timeout(500)
        step_screenshot(page, out_dir, "05_confirm_password_filled",
                        marker_x=int(box["x"] + box["width"] / 2),
                        marker_y=int(box["y"] + box["height"] / 2))

        # ── Step 6: Click register button ──
        print("[6/6] Click register button")
        register_btn = page.get_by_text("完成注册")
        register_btn.wait_for(state="visible", timeout=5000)
        box = register_btn.bounding_box()
        # Check if button is enabled (validation passed)
        is_disabled = register_btn.is_disabled()
        if not is_disabled:
            register_btn.click()
            page.wait_for_timeout(1500)
            current_url = page.url
            step_screenshot(page, out_dir, "06_after_register_click",
                            marker_x=int(box["x"] + box["width"] / 2),
                            marker_y=int(box["y"] + box["height"] / 2))
            if "/dashboard" in current_url:
                print(f"\n[OK] Register SUCCESS — redirected to: {current_url}")
                print(f"   Created account: {test_user} / {test_pass}")
            else:
                success_el = page.locator(".login-success")
                if success_el.is_visible():
                    print(f"\n[OK] Register SUCCESS — {success_el.text_content()}")
                else:
                    error_el = page.locator(".login-error")
                    if error_el.is_visible():
                        print(f"\n[WARN] Register error: {error_el.text_content()}")
                    else:
                        print(f"\n[WARN] Register: unexpected redirect to {current_url}")
        else:
            step_screenshot(page, out_dir, "06_register_button_disabled")
            print(f"\n[WARN] Register button is disabled — form validation failed")
            errors = page.locator(".login-error")
            if errors.is_visible():
                print(f"   Error: {errors.text_content()}")

        print(f"\nAll screenshots saved to: {out_dir}")
        browser.close()


if __name__ == "__main__":
    test_register()
