"""
Django settings for Android-AutoTests — pure API server, no frontend serving.
"""

import os

from pathlib import Path

from config.env import load_dotenv

# django-stubs：让 QuerySet/Manager 等在类型检查下更准确
try:
    import django_stubs_ext

    django_stubs_ext.monkeypatch()
except ImportError:
    pass

BASE_DIR = Path(__file__).resolve().parent.parent


# ── Load .env into os.environ（单一实现在 config/env.py；manage.py 不会自动加载）──
load_dotenv()

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

# 开发（DEBUG=True）默认放宽为 "*"；生产（DEBUG=False）默认只接受本机回环。
# 对外提供服务时必须显式设 DJANGO_ALLOWED_HOSTS（逗号分隔）——显式值始终优先。
ALLOWED_HOSTS = os.environ.get(
    "DJANGO_ALLOWED_HOSTS", "*" if DEBUG else "127.0.0.1,localhost"
).split(",")

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
    # Swagger UI 静态资产（SIDECAR 来源；离线/内网环境不依赖 CDN）
    "drf_spectacular_sidecar",
    # Framework
    "gateway",
    "shared",
    # Django Apps（11 个；其中 test_runner、evaluator 已下线，仅保留卸表迁移）
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
    "corsheaders.middleware.CorsMiddleware",
    # 工具网关内部令牌（JWT 豁免前缀的替代凭据；只在 /api/ai/tools/ 上生效）
    "gateway.internal_token.InternalToolTokenMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "gateway.middleware.JWTAuthenticationMiddleware",
    # CSRF 保护：必须排在 JWTAuthenticationMiddleware 之后——有效 JWT 的请求由该中间件
    # 置 request._dont_enforce_csrf_checks 豁免（浏览器无法跨站携带自定义 Authorization 头），
    # 后台 /admin/ 等 session 面则正常受保护。
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

# 路径约定：全部 /api/ 路由以 / 结尾（openspec/specs/api-path-convention）。
# 关闭 APPEND_SLASH，使缺失尾斜杠得到**确定的 404**，而不是 CommonMiddleware 的 301
# （301 会丢 Authorization 头 → 误报 401；可能把 POST 降级为 GET；且被浏览器长期缓存）。
APPEND_SLASH = False

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

# ── CORS — 开发放行前端 dev server；生产默认只放行白名单 ──
# 开发（DEBUG=True）默认放开全部来源；生产（DEBUG=False）默认关闭 allow-all，
# 改由 CORS_ALLOWED_ORIGINS（逗号分隔）精确控制。显式环境变量始终优先。
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

# ── 安全加固（生产显式开启；默认值不改变本地/现有 HTTP 部署的行为）──
# HSTS：确认全站 HTTPS 后再设置（例如 31536000 = 1 年）；0 = 关闭
SECURE_HSTS_SECONDS = int(os.environ.get("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = os.environ.get(
    "SECURE_HSTS_INCLUDE_SUBDOMAINS", "False"
).lower() in ("true", "1", "yes")
SECURE_HSTS_PRELOAD = os.environ.get("SECURE_HSTS_PRELOAD", "False").lower() in (
    "true",
    "1",
    "yes",
)
# HTTPS 跳转：仅供「Django 直接终止 TLS」的部署开启；
# 反向代理已终止 TLS 时必须保持 False，否则会 301 循环
SECURE_SSL_REDIRECT = os.environ.get("SECURE_SSL_REDIRECT", "False").lower() in (
    "true",
    "1",
    "yes",
)
# 反向代理场景：信任 X-Forwarded-Proto 以还原原始协议
if os.environ.get("SECURE_PROXY_SSL_HEADER", "").lower() in ("true", "1", "yes"):
    SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
# Cookie 安全标志：生产（DEBUG=False）默认开启，本地 HTTP 开发自动关闭
SESSION_COOKIE_SECURE = os.environ.get(
    "SESSION_COOKIE_SECURE", "False" if DEBUG else "True"
).lower() in ("true", "1", "yes")
CSRF_COOKIE_SECURE = os.environ.get("CSRF_COOKIE_SECURE", "False" if DEBUG else "True").lower() in (
    "true",
    "1",
    "yes",
)

# ── Database ──
DB_ENGINE = os.environ.get("DB_ENGINE", "mysql")

# ── 设备引擎（L1c 可替换插槽）──
# 上层经 engines.device.registry 工厂（open_engine / close_engine）取引擎；换引擎只改此配置。
# 注：设备交互无中间层（原 L2 会话层已于 2026-09-03 扁平化删除）。
DEVICE_ENGINE = os.environ.get("DEVICE_ENGINE", "u2")

# ── AI 引擎（L1c 可替换插槽，对齐 DEVICE_ENGINE）──
# 消费方 apps/ai_assistant/views_drf.py 经 engines.ai.registry 取引擎
# （get_ai_engine(settings.AI_ENGINE)）；换 AI 框架只改此配置。
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

# ── 知识库 RAG 嵌入模型（ollama 本地 / openai 兼容 API）──
EMBEDDING_PROVIDER = os.environ.get("EMBEDDING_PROVIDER", "ollama")
EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "nomic-embed-text")
EMBEDDING_API_KEY = os.environ.get("EMBEDDING_API_KEY", "")
EMBEDDING_BASE_URL = os.environ.get("EMBEDDING_BASE_URL", "")
EMBEDDING_DIMENSIONS = os.environ.get("EMBEDDING_DIMENSIONS", "")

# ── JWT ──
JWT_ACCESS_TTL = int(os.environ.get("JWT_ACCESS_TTL", "3600"))  # 1 hour
JWT_REFRESH_TTL = int(os.environ.get("JWT_REFRESH_TTL", "604800"))  # 7 days

# ── 内部服务凭据 ──
# 工具网关 `/api/ai/tools/` 免 JWT（服务间调用），改由 `X-Internal-Token` 校验；
# 留空 = 该前缀一律 401（fail-closed），不要在未配置时放开。
AI_TOOL_GATEWAY_TOKEN = os.environ.get("AI_TOOL_GATEWAY_TOKEN", "")

# ── Django REST Framework ──
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "shared.auth.drf_auth.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    # BrowsableAPIRenderer 只在 DEBUG 下注册：生产不需要 HTML 可浏览 API（JSON 契约不变）
    "DEFAULT_RENDERER_CLASSES": [
        "shared.renderers.EnvelopeJSONRenderer",
        *(["rest_framework.renderers.BrowsableAPIRenderer"] if DEBUG else []),
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
    # 文档页资产随包分发（drf-spectacular-sidecar）：断网环境仍可渲染
    "SWAGGER_UI_DIST": "SIDECAR",
    "SWAGGER_UI_FAVICON_HREF": "SIDECAR",
    # 分组中文说明：取代原手写文档的模块描述（顺序即 Swagger 分组顺序）
    "TAGS": [
        {"name": "dashboard", "description": "仪表盘：全平台只读聚合统计"},
        {"name": "devices", "description": "设备管理：扫描 / 连接 / 断开 / 激活 / 心跳 / 占用释放"},
        {
            "name": "inspector",
            "description": "设备检查器：快照抓取与页面回看（快照化，无 WS 截图流）",
        },
        {
            "name": "elements",
            "description": "元素定位：Android 页面 / Web 元素 / API 端点三类资产与目录",
        },
        {"name": "cases", "description": "用例管理：项目 → 目录 → 文件 → 用例行"},
        {"name": "workflow", "description": "工作流：编排文档 CRUD 与导入导出"},
        {"name": "auth", "description": "登录鉴权：登录 / 注册 / 刷新 / 登出 / 当前用户"},
        {"name": "ai", "description": "AI 助手：智能体、会话、知识库与任务发布"},
        {"name": "schema", "description": "OpenAPI schema 端点（drf-spectacular 自带）"},
    ],
}

# Chat upload temp files — cleanup_uploads management command
UPLOAD_CLEANUP_MAX_AGE_DAYS = int(os.environ.get("UPLOAD_CLEANUP_MAX_AGE_DAYS", "7"))

# AI 对话发图：5MB 图片 base64 约 6.7MB，须大于 Django 默认 2.5MB 请求体上限，
# 否则 chat_stream 读 body 时抛 RequestDataTooBig（超限图片由应用层 5MB 校验拦截）
DATA_UPLOAD_MAX_MEMORY_SIZE = 16 * 1024 * 1024

# ── Project-specific configuration ──
DEVICE_SERIAL = os.environ.get("DEVICE_SERIAL", "")
SERVER_PORT = int(os.environ.get("SERVER_PORT", "8766"))

# ADB server 地址（容器内连接宿主机 ADB daemon）：由 .env / 环境变量直接对 adb 与
# uiautomator2 生效（两者原生读取该环境变量），无需在 settings 里二次转发。

# Paths
# 数据根目录：.env 的 DATA_DIR 可指向外部盘/卷（如 D:\Govee\data）；留空用项目内 data/。
# 相对值按 BASE_DIR 解析，避免随进程 CWD 漂移。
_data_dir_env = os.environ.get("DATA_DIR", "").strip()
DATA_DIR = Path(_data_dir_env) if _data_dir_env else BASE_DIR / "data"
if not DATA_DIR.is_absolute():
    DATA_DIR = BASE_DIR / DATA_DIR

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
MEDIA_ROOT = DATA_DIR / "uploads"

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


# ── Logging — 始终配置 ──
# 曾经只在 DOCKER_CONTAINER=true 时定义，而该变量在整个仓库仅此一处引用、且仓库内无容器编排文件，
# 结果应用级 INFO 日志没有任何 handler（仅 logging.lastResort 输出 WARNING+），排障时看不到业务日志。
# 现在：本地（默认）控制台 + logs/django.log；容器只输出 stdout（由编排侧收集）。级别由 LOG_LEVEL 控制。
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
_IS_CONTAINER = os.environ.get("DOCKER_CONTAINER", "").lower() in ("true", "1", "yes")

_LOG_HANDLERS = {
    "console": {
        "class": "logging.StreamHandler",
        "stream": "ext://sys.stdout",
        "formatter": "simple",
    },
}
_LOG_ROOT_HANDLERS = ["console"]
if not _IS_CONTAINER:
    _LOG_HANDLERS["file"] = {
        "class": "logging.handlers.RotatingFileHandler",
        "filename": str(LOG_DIR / "django.log"),
        "maxBytes": 5 * 1024 * 1024,
        "backupCount": 3,
        "encoding": "utf-8",
        "delay": True,  # 日志目录尚未创建时延迟到首次写入再打开
        "formatter": "simple",
    }
    _LOG_ROOT_HANDLERS.append("file")

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
