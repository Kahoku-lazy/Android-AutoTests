"""
模块功能：➡️ E2E 选择器常量：data-testid 与前端 DOM 一一对应，禁止在用例里散写 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/e2e/selectors.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 frontend/src 的 data-testid 约定
🏁
"""

# ── 登录页 ──
LOGIN_PAGE = "login-page"
LOGIN_MODE_LOGIN = "login-mode-login"
LOGIN_MODE_REGISTER = "login-mode-register"
MEETING_TITLE = "meeting-title"
LOGIN_USERNAME = "login-username"
LOGIN_PASSWORD = "login-password"
LOGIN_REMEMBER = "login-remember"
LOGIN_SUBMIT = "login-submit"
LOGIN_TO_REGISTER = "login-to-register"
LOGIN_ERROR_MESSAGE = "login-error-message"
LOGIN_ERROR_DISMISS = "login-error-dismiss"

# ── 注册卡（同一登录页的注册态）──
REGISTER_USERNAME = "register-username"
REGISTER_EMAIL = "register-email"
REGISTER_PASSWORD = "register-password"
REGISTER_PASSWORD2 = "register-password2"
REGISTER_SUBMIT = "register-submit"
REGISTER_TO_LOGIN = "register-to-login"

# ── 侧栏（登录后的落点，用于登出与账号断言）──
SIDEBAR_ACTIVE_ACCOUNT = "sidebar-active-account"
SIDEBAR_LOGOUT = "sidebar-logout"
