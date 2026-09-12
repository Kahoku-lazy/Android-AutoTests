"""
Django settings for Android-AutoTests — pure API server, no frontend serving.
"""

import os

from pathlib import Path

# django-stubs：让 QuerySet/Manager 等在类型检查下更准确
try:
    import django_stubs_ext

    django_stubs_ext.monkeypatch()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


# ── Load .env into os.environ (manage.py doesn't auto-load it) ──
def _load_dotenv():
    env_file = BASE_DIR / ".env"
    if not env_file.exists():
        return
    with open(env_file, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            key, value = key.strip(), value.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = value


_load_dotenv()

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")

DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() in ("true", "1", "yes")

# Fail fast if SECRET_KEY is not set in production (DEBUG=False).
# Encryption, JWT signing, and session security all depend on a strong secret.
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

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "*").split(",")

# 设备管理管理员白名单（逗号分隔的用户名）。命中者全局查看所有设备（含锁定）。
# 默认空 = 无管理员，仅公开/自身设备可见。示例：ADMIN_USERS=admin,ops
ADMIN_USERS = {u.strip() for u in os.environ.get("ADMIN_USERS", "").split(",") if u.strip()}

# ── Application definition ──
INSTALLED_APPS = [
    # Admin theme (must be before django.contrib.admin)
    "jazzmin",
    # Django built-in
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Third-party
    "corsheaders",
    "channels",
    "rest_framework",
    "drf_spectacular",
    # Framework
    "gateway",
    "shared",
    # Django Apps (8)
    "apps.device_inspector",
    "apps.element_locator",
    "apps.device_pool",
    "apps.case_manager",
    "apps.workflow",
    "apps.test_runner",
    "apps.report_generator",
    "apps.accounts",
    "apps.ai_assistant",
    "apps.evaluator",
    "apps.dashboard",
]

MIDDLEWARE = [
    # 尾斜杠规范化必须最先（真机发现 #1：301 丢 Authorization 头 → 401）
    "gateway.normalize_slash.NormalizeTrailingSlashMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "gateway.middleware.JWTAuthenticationMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

ASGI_APPLICATION = "config.asgi.application"

# Templates — Django Admin + drf-spectacular Swagger UI 主题覆盖（templates/drf_spectacular/）
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

# ── CORS — allow frontend dev server ──
# 生产环境应设为 False，通过 CORS_ALLOWED_ORIGINS 精确控制
CORS_ALLOW_ALL_ORIGINS = os.environ.get("CORS_ALLOW_ALL_ORIGINS", "True").lower() in (
    "true",
    "1",
    "yes",
)
CORS_ALLOW_CREDENTIALS = True

# ── Database ──
DB_ENGINE = os.environ.get("DB_ENGINE", "mysql")

# ── 设备引擎（L1c 可替换插槽）──
# 调用方（DeviceSession）经 engines.device.registry 取引擎；换引擎只改此配置。
DEVICE_ENGINE = os.environ.get("DEVICE_ENGINE", "u2")

# ── AI 引擎（L1c 可替换插槽，对齐 DEVICE_ENGINE）──
# 调用方（engine_adapter）经 engines.ai.registry 取引擎；换 AI 框架只改此配置。
AI_ENGINE = os.environ.get("AI_ENGINE", "agentscope")


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
                "connect_timeout": 5,  # Fail fast on dead MySQL (was OS default 30s)
                "init_command": (
                    "SET sql_mode='STRICT_TRANS_TABLES', "
                    "character_set_connection=utf8mb4, "
                    "collation_connection=utf8mb4_unicode_ci"
                ),
            },
            "CONN_MAX_AGE": 30,  # Keep connections alive 30s (was 600 — too many sleeping connections)
            "CONN_HEALTH_CHECKS": True,  # Auto-detect and replace dead connections
        },
    }
elif DB_ENGINE == "sqlite":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        },
    }
else:
    raise RuntimeError(f"不支持的 DB_ENGINE={DB_ENGINE!r}，仅支持 mysql / sqlite")

# ── Redis ──
REDIS_HOST = os.environ.get("REDIS_HOST", "localhost")
REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))
REDIS_URL = os.environ.get("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")


# ── Channels layer ──
def _channel_layers_config():
    """Redis channel layer; JSON serializer avoids msgpack ABI issues on some Python builds."""
    try:
        import redis as _redis_check  # noqa: F401

        from channels_redis.core import RedisChannelLayer

        RedisChannelLayer(hosts=[REDIS_URL], serializer_format="json")
        return {
            "default": {
                "BACKEND": "channels_redis.core.RedisChannelLayer",
                "CONFIG": {
                    "hosts": [REDIS_URL],
                    "serializer_format": "json",
                },
            },
        }
    except Exception as exc:
        import logging

        logging.getLogger("config").warning(
            "Redis ChannelLayer unavailable (%s), using InMemoryChannelLayer",
            exc,
        )
        return {
            "default": {
                "BACKEND": "channels.layers.InMemoryChannelLayer",
            },
        }


CHANNEL_LAYERS = _channel_layers_config()

# ── AgentScope ──
AGENTSCOPE_SERVICE_PORT = int(os.environ.get("AGENTSCOPE_PORT", "8000"))
AGENTSCOPE_SERVICE_URL = os.environ.get(
    "AGENTSCOPE_URL",
    f"http://127.0.0.1:{AGENTSCOPE_SERVICE_PORT}",
)
AGENTSCOPE_WORKSPACE_DIR = BASE_DIR / "data" / "agentscope_workspaces"
AGENTSCOPE_SERVICE_TITLE = "Android-AutoTests Agent Service"
AGENTSCOPE_SERVICE_VERSION = "2.0.0"

# ── 知识库 RAG 嵌入模型（ollama 本地 / openai 兼容 API）──
EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY", "")
EMBEDDING_BASE_URL = os.environ.get("EMBEDDING_BASE_URL", "")
EMBEDDING_DIMENSIONS = os.environ.get("EMBEDDING_DIMENSIONS", "")

# ── JWT ──
JWT_ACCESS_TTL = int(os.environ.get("JWT_ACCESS_TTL", "3600"))  # 1 hour
JWT_REFRESH_TTL = int(os.environ.get("JWT_REFRESH_TTL", "604800"))  # 7 days

# ── Django REST Framework ──
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "shared.auth.drf_auth.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "shared.renderers.EnvelopeJSONRenderer",
        "rest_framework.renderers.BrowsableAPIRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "UNAUTHENTICATED_USER": None,
}

# ── drf-spectacular (OpenAPI 3.0 schema + Swagger UI) ──
SPECTACULAR_SETTINGS = {
    "TITLE": "Android-AutoTests API",
    "DESCRIPTION": (
        "Android UI 自动化测试平台 — 覆盖设备管理、元素定位、用例编排、"
        "测试执行、AI 助手、评测、报告生成全流程。"
    ),
    "VERSION": "2.0.0",
}

# Chat upload temp files — cleanup_uploads management command
UPLOAD_CLEANUP_MAX_AGE_DAYS = int(os.environ.get("UPLOAD_CLEANUP_MAX_AGE_DAYS", "7"))

# AI 对话发图：5MB 图片 base64 约 6.7MB，须大于 Django 默认 2.5MB 请求体上限，
# 否则 chat_stream 读 body 时抛 RequestDataTooBig（超限图片由应用层 5MB 校验拦截）
DATA_UPLOAD_MAX_MEMORY_SIZE = 16 * 1024 * 1024

# ── Airtest migration feature flags (toggle per environment) ──
AIRTEST_ENABLED = os.environ.get("AIRTEST_ENABLED", "True").lower() in ("true", "1", "yes")

# ── Project-specific configuration ──
DEVICE_SERIAL = os.environ.get("DEVICE_SERIAL", "")
SCREENSHOT_INTERVAL = float(os.environ.get("SCREENSHOT_INTERVAL", "0.5"))
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8766"))

# ADB server 地址 — 容器内连接宿主机 ADB daemon
# Android 调试桥 (adb) 和 uiautomator2 原生支持此环境变量
ANDROID_ADB_SERVER_ADDRESS = os.environ.get("ANDROID_ADB_SERVER_ADDRESS", "")
if ANDROID_ADB_SERVER_ADDRESS:
    os.environ["ANDROID_ADB_SERVER_ADDRESS"] = ANDROID_ADB_SERVER_ADDRESS

# Paths
DATA_DIR = BASE_DIR / "data"
SCREENSHOT_DIR = DATA_DIR / "screenshots"
EXPORT_DIR = BASE_DIR / "exports"
LOG_DIR = BASE_DIR / "logs"

# Internationalization
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_TZ = False

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Static files (Django Admin + jazzmin theme) ──
# Django 5.1+ 默认 STATIC_URL=None，必须显式设置，否则 Admin 无样式
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]  # 项目自定义静态文件源目录

# ── Media files (uploads) ──
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "data" / "uploads"

# ── Jazzmin Admin Theme ──
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
        "apps.element_locator": "fas fa-search",
        "apps.device_pool": "fas fa-mobile-alt",
        "apps.case_manager": "fas fa-clipboard-list",
    "apps.report_generator": "fas fa-chart-bar",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    # 自定义 CSS — 字体覆盖（中英文兼容字体栈）
    "custom_css": "css/admin-fonts.css",
}

# ── Jazzmin Theme 主题更换 ──
JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "sidebar_nav_small_text": False,
    "theme": "cosmo",
}


# ── Logging — 容器环境输出到 stdout，本地开发沿用文件日志 ──
if os.environ.get("DOCKER_CONTAINER", "").lower() in ("true", "1", "yes"):
    LOGGING = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "simple": {
                "format": "{levelname} {asctime} {name} {message}",
                "style": "{",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": "simple",
            },
        },
        "root": {
            "handlers": ["console"],
            "level": "INFO",
        },
        "loggers": {
            "django": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
            "daphne": {
                "handlers": ["console"],
                "level": "INFO",
                "propagate": False,
            },
        },
    }
