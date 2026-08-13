"""E2E data-testid 常量 — 与前端 DOM 一一对应，禁止在用例中散写脆弱选择器。"""

# Login page
LOGIN_PAGE = "login-page"
LOGIN_USERNAME = "login-username"
LOGIN_PASSWORD = "login-password"
LOGIN_REMEMBER = "login-remember"
LOGIN_SUBMIT = "login-submit"
LOGIN_TO_REGISTER = "login-to-register"

# Register
REGISTER_USERNAME = "register-username"
REGISTER_EMAIL = "register-email"
REGISTER_PASSWORD = "register-password"
REGISTER_PASSWORD2 = "register-password2"
REGISTER_SUBMIT = "register-submit"
REGISTER_TO_LOGIN = "register-to-login"

# Error overlay
LOGIN_ERROR_OVERLAY = "login-error-overlay"
LOGIN_ERROR_MESSAGE = "login-error-message"
LOGIN_ERROR_DISMISS = "login-error-dismiss"

# Account switch prompt
ACCOUNT_SWITCH_PROMPT = "account-switch-prompt"
SWITCH_TO_EXISTING = "switch-to-existing"
ADD_NEW_ACCOUNT = "add-new-account"

# Sidebar
APP_SIDEBAR = "app-sidebar"
SIDEBAR_LOGOUT = "sidebar-logout"
SIDEBAR_ADD_ACCOUNT = "sidebar-add-account"
SIDEBAR_ACCOUNT_MENU = "sidebar-account-menu"
SIDEBAR_ACTIVE_ACCOUNT = "sidebar-active-account"

# localStorage / sessionStorage keys (token-storage.ts)
POOL_KEY = "auth_accounts"
ACTIVE_KEY = "auth_active"
SAVED_USERNAME_KEY = "saved_username"
