import os

from pathlib import Path

from backend.config.env import load_dotenv

try:
    import django_stubs_ext

    django_stubs_ext.monkeypatch()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent
REPO_ROOT = BASE_DIR.parent


load_dotenv()

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")

DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ("true", "1", "yes")

if not SECRET_KEY:
    if DEBUG:
        import warnings

        warnings.warn(
            "DJANGO_SECRET_KEY is not set! Encryption and JWT signing will be insecure.",
            RuntimeWarning,
        )
    else:
        raise RuntimeError(
            "DJANGO_SECRET_KEY must be set via environment variable or .env file "
            "when DEBUG=False (production mode)."
        )

ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "*" if DEBUG else "127.0.0.1,localhost"
).split(",")

ADMIN_USERS = {u.strip() for u in os.environ.get("ADMIN_USERS", "").split(",") if u.strip()}

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "channels",
    "rest_framework",
    "drf_spectacular",
    "drf_spectacular_sidecar",
    "backend.gateway",
    "backend.shared",
    "backend.apps.device_pool",
    "backend.apps.case_manager",
    "backend.apps.report_generator",
    "backend.apps.accounts",
    "backend.apps.ai_assistant",
    "backend.apps.task_list",
    "backend.apps.bug_manager",
    "backend.apps.serial_log",
    "backend.apps.dashboard",
    "backend.apps.usage_ledger",
    "backend.apps.ops_console",
    "backend.apps.knowledge_search",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "backend.gateway.middleware.JWTAuthenticationMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "backend.config.urls"

APPEND_SLASH = False

ASGI_APPLICATION = "backend.config.asgi.application"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

CORS_ALLOW_ALL_ORIGINS = os.environ.get(
    "CORS_ALLOW_ALL_ORIGINS", "True" if DEBUG else "False"
).lower() in (
    "true",
    "1",
    "yes",
)
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
    if origin.strip()
]
CORS_ALLOW_CREDENTIALS = True

SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", "False"
).lower() in ("true", "1", "yes")
SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "False").lower() in (
    "true",
    "1",
    "yes",
)
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "False").lower() in (
    "true",
    "1",
    "yes",
)
if os.environ.get("SECURE_PROXY_SSL_HEADER", "").lower() in ("true", "1", "yes"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SESSION_COOKIE_SECURE = os.environ.get(
    "SESSION_COOKIE_SECURE", "False" if DEBUG else "True"
).lower() in ("true", "1", "yes")
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "False" if DEBUG else "True").lower() in (
    "true",
    "1",
    "yes",
)

DB_ENGINE = os.environ.get("DB_ENGINE", "mysql")

DEVICE_ENGINE = os.environ.get("DEVICE_ENGINE", "u2")


if DB_ENGINE == "mysql":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.environ.get("DB_NAME", "android_autotests"),
            "USER": os.environ.get("DB_USER", "root"),
            "PASSWORD": os.environ.get("DB_PASSWORD", ""),
            "HOST": os.environ.get("DB_HOST", "127.0.0.1"),
            "PORT": os.environ.get("DB_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
                "connect_timeout": 5,
                "init_command": (
                    "SET sql_mode='STRICT_TRANS_TABLES', "
                    "character_set_connection=utf8mb4, "
                    "collation_connection=utf8mb4_unicode_ci"
                ),
            },
            "CONN_MAX_AGE": 30,
            "CONN_HEALTH_CHECKS": True,
        },
    }
elif DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": REPO_ROOT / "db.sqlite3",
        },
    }
else:
    raise RuntimeError(f"不支持的 DB_ENGINE={DB_ENGINE!r}，仅支持 mysql / sqlite")

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

JWT_ACCESS_TTL = int(os.environ.get("JWT_ACCESS_TTL", "3600"))
JWT_REFRESH_TTL = int(os.environ.get("JWT_REFRESH_TTL", "604800"))

MEDIA_LINK_SECRET = os.environ.get("MEDIA_LINK_SECRET", "").strip() or SECRET_KEY
MEDIA_LINK_TTL_SECONDS = int(os.environ.get("MEDIA_LINK_TTL_SECONDS", "900"))

DEVICE_LOG_ENABLED = os.environ.get("DEVICE_LOG_ENABLED", "1") not in ("0", "false", "False", "")
DEVICE_LOG_TCP_HOST = os.environ.get("DEVICE_LOG_TCP_HOST", "0.0.0.0")
DEVICE_LOG_ADVERTISE_HOST = os.environ.get("DEVICE_LOG_ADVERTISE_HOST", "").strip()
DEVICE_LOG_TCP_PORT = int(os.environ.get("DEVICE_LOG_TCP_PORT", "7005"))
DEVICE_LOG_SOURCE_SKU = os.environ.get("DEVICE_LOG_SOURCE_SKU", "H6810")
DEVICE_LOG_SOURCE_BAUD = int(os.environ.get("DEVICE_LOG_SOURCE_BAUD", "921600"))
DEVICE_LOG_SOURCES = os.environ.get("DEVICE_LOG_SOURCES", "")
DEVICE_LOG_SERIAL_PORT = os.environ.get("DEVICE_LOG_SERIAL_PORT", "")
DEVICE_LOG_SERIAL_BAUD = int(os.environ.get("DEVICE_LOG_SERIAL_BAUD", "115200"))
DEVICE_LOG_BUFFER_SECONDS = int(os.environ.get("DEVICE_LOG_BUFFER_SECONDS", "600"))
DEVICE_LOG_BUFFER_MAX_LINES = int(os.environ.get("DEVICE_LOG_BUFFER_MAX_LINES", "20000"))
DEVICE_LOG_WINDOW_SECONDS = float(os.environ.get("DEVICE_LOG_WINDOW_SECONDS", "5"))
DEVICE_LOG_BASELINE_SECONDS = float(os.environ.get("DEVICE_LOG_BASELINE_SECONDS", "30"))
DEVICE_LOG_KEYWORD_FILE = os.environ.get(
    "DEVICE_LOG_KEYWORD_FILE", str(BASE_DIR / "config" / "device_log_keywords.json")
)
DEVICE_LOG_LOG_DIR = os.environ.get("DEVICE_LOG_LOG_DIR", str(REPO_ROOT / "logs"))
DEVICE_LOG_FILE_MAX_BYTES = int(os.environ.get("DEVICE_LOG_FILE_MAX_BYTES", str(50 * 1024 * 1024)))
DEVICE_LOG_TAIL_LINES = int(os.environ.get("DEVICE_LOG_TAIL_LINES", "2000"))
DEVICE_LOG_TAIL_LINES_MAX = int(os.environ.get("DEVICE_LOG_TAIL_LINES_MAX", "20000"))

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "backend.shared.auth.drf_auth.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "backend.shared.renderers.EnvelopeJSONRenderer",
        *(["rest_framework.renderers.BrowsableAPIRenderer"] if DEBUG else []),
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "UNAUTHENTICATED_USER": None,
}

SPECTACULAR_SETTINGS = {
    "TITLE": "Android-AutoTests API",
    "DESCRIPTION": (
        "Android UI 自动化测试平台 — 覆盖设备管理、文档式用例、AI 任务执行与验收、"
        "串口日志、测试报告与仪表盘。"
    ),
    "VERSION": "2.0.0",
    "SCHEMA_PATH_PREFIX": "/api",
    "ENUM_NAME_OVERRIDES": {
        "ApiProtocolEnum": ["deepseek", "dashscope", "openai"],
    },
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    "TAGS": [
        {"name": "dashboard", "description": "仪表盘：全平台只读聚合统计"},
        {"name": "devices", "description": "设备管理：扫描 / 连接 / 断开 / 激活 / 心跳 / 占用释放"},
        {"name": "cases", "description": "用例管理：项目 → 目录 → 文件 → 用例行"},
        {"name": "auth", "description": "登录鉴权：登录 / 注册 / 刷新 / 登出 / 当前用户"},
        {"name": "ai", "description": "AI 助手：智能体配置、任务发布 / 重跑 / 取消、任务清单"},
        {"name": "tasks", "description": "任务清单：任务提交、重跑、取消、事件流程报告"},
        {"name": "bugs", "description": "BUG 单管理：任务错误分类登记、检索与处理状态"},
        {
            "name": "reports",
            "description": "测试报告：已生成报告台账（SOP + 智能体）、报告数量统计",
        },
        {
            "name": "serial-log",
            "description": "串口日志：端口监听开关、当前日志查看与关键词对照表",
        },
        {"name": "ops", "description": "运营后台：账号列表 / 停用启用 / 重置密码"},
        {"name": "schema", "description": "OpenAPI schema 端点（drf-spectacular 自带）"},
    ],
}

UPLOAD_CLEANUP_MAX_AGE_DAYS = int(os.environ.get("UPLOAD_CLEANUP_MAX_AGE_DAYS", "7"))

DATA_UPLOAD_MAX_MEMORY_SIZE = 16 * 1024 * 1024

DEVICE_SERIAL = os.environ.get("DEVICE_SERIAL", "")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8766"))


_data_dir_env = os.environ.get("DATA_DIR", "").strip()
DATA_DIR = Path(_data_dir_env) if _data_dir_env else REPO_ROOT / "data"
if not DATA_DIR.is_absolute():
    DATA_DIR = REPO_ROOT / DATA_DIR

SCREENSHOT_DIR = DATA_DIR / "screenshots"
TASK_MEDIA_DIR = Path(os.environ.get("TASK_MEDIA_DIR", "").strip() or DATA_DIR / "task_media")
EXPORT_DIR = REPO_ROOT / "exports"
LOG_DIR = REPO_ROOT / "logs"

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_TZ = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STATIC_URL = "/static/"
STATIC_ROOT = REPO_ROOT / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = DATA_DIR / "uploads"

JAZZMIN_SETTINGS = {
    "site_title": "Android-AutoTests",
    "site_header": "AutoTests",
    "site_brand": "Android-AutoTests",
    "welcome_sign": "Android-AutoTests 管理后台",
    "copyright": "Android-AutoTests",
    "show_sidebar": True,
    "navigation_expanded": True,
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",
        "backend.apps.device_pool": "fas fa-mobile-alt",
        "backend.apps.case_manager": "fas fa-clipboard-list",
        "backend.apps.report_generator": "fas fa-chart-bar",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "sidebar_nav_small_text": False,
    "theme": "cosmo",
}


LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()

_LOG_HANDLERS = {
    "console": {
        "class": "logging.StreamHandler",
        "stream": "ext://sys.stdout",
        "formatter": "simple",
    },
}
_LOG_ROOT_HANDLERS = ["console"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "{levelname} {asctime} {name} {message}",
            "style": "{",
        },
    },
    "handlers": _LOG_HANDLERS,
    "root": {
        "handlers": _LOG_ROOT_HANDLERS,
        "level": LOG_LEVEL,
    },
    "loggers": {
        "django": {
            "handlers": _LOG_ROOT_HANDLERS,
            "level": LOG_LEVEL,
            "propagate": False,
        },
        "daphne": {
            "handlers": _LOG_ROOT_HANDLERS,
            "level": LOG_LEVEL,
            "propagate": False,
        },
    },
}
