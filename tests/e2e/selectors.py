"""E2E data-testid 常量 — 与前端 DOM 一一对应，禁止在用例中散写脆弱选择器。"""

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
