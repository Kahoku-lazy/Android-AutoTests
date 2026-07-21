"""
Django settings for Android-AutoTests — pure API server, no frontend serving.
"""
import os
from pathlib import Path

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

SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY', '')

DEBUG = os.environ.get('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = ['*']

# ── Application definition ──
INSTALLED_APPS = [
    # Admin theme (must be before django.contrib.admin)
    'jazzmin',
    # Django built-in
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Third-party
    'corsheaders',
    'channels',
    # Framework
    'gateway',
    'shared',
    # Django Apps (7)
    'apps.element_locator',
    'apps.device_pool',
    'apps.case_manager',
    'apps.workflow',
    'apps.test_runner',
    'apps.report_generator',
    'apps.ai_assistant',
    'apps.evaluator',
    'apps.dashboard',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'gateway.middleware.JWTAuthenticationMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

ASGI_APPLICATION = 'config.asgi.application'

# Templates — minimal config for Django Admin only (frontend is served separately)
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ── CORS — allow frontend dev server ──
CORS_ALLOW_ALL_ORIGINS = True  # dev only
CORS_ALLOW_CREDENTIALS = True

# ── Database ──
DB_ENGINE = os.environ.get('DB_ENGINE', 'mysql')

if DB_ENGINE == 'mysql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.environ.get('DB_NAME', 'android_autotests'),
            'USER': os.environ.get('DB_USER', 'root'),
            'PASSWORD': os.environ.get('DB_PASSWORD', ''),
            'HOST': os.environ.get('DB_HOST', '127.0.0.1'),
            'PORT': os.environ.get('DB_PORT', '3306'),
            'OPTIONS': {
                'charset': 'utf8mb4',
                'init_command': (
                    "SET sql_mode='STRICT_TRANS_TABLES', "
                    "character_set_connection=utf8mb4, "
                    "collation_connection=utf8mb4_unicode_ci"
                ),
            },
            'CONN_MAX_AGE': 600,
        },
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'data' / 'app.db',
        },
    }

# ── Redis ──
REDIS_HOST = os.environ.get('REDIS_HOST', 'localhost')
REDIS_PORT = int(os.environ.get('REDIS_PORT', '6379'))
REDIS_URL = os.environ.get('REDIS_URL', f'redis://{REDIS_HOST}:{REDIS_PORT}/0')

# ── Channels layer ──
def _channel_layers_config():
    """Redis channel layer; JSON serializer avoids msgpack ABI issues on some Python builds."""
    try:
        import redis as _redis_check  # noqa: F401
        from channels_redis.core import RedisChannelLayer

        RedisChannelLayer(hosts=[REDIS_URL], serializer_format='json')
        return {
            'default': {
                'BACKEND': 'channels_redis.core.RedisChannelLayer',
                'CONFIG': {
                    'hosts': [REDIS_URL],
                    'serializer_format': 'json',
                },
            },
        }
    except Exception as exc:
        import logging
        logging.getLogger('config').warning(
            'Redis ChannelLayer unavailable (%s), using InMemoryChannelLayer', exc,
        )
        return {
            'default': {
                'BACKEND': 'channels.layers.InMemoryChannelLayer',
            },
        }


CHANNEL_LAYERS = _channel_layers_config()

# ── AgentScope ──
AGENTSCOPE_SERVICE_PORT = int(os.environ.get('AGENTSCOPE_PORT', '8000'))
AGENTSCOPE_SERVICE_URL = os.environ.get(
    'AGENTSCOPE_URL',
    f'http://127.0.0.1:{AGENTSCOPE_SERVICE_PORT}',
)
AGENTSCOPE_WORKSPACE_DIR = BASE_DIR / 'data' / 'agentscope_workspaces'
AGENTSCOPE_SERVICE_TITLE = 'Android-AutoTests Agent Service'
AGENTSCOPE_SERVICE_VERSION = '2.0.0'

# ── JWT ──
JWT_ACCESS_TTL = int(os.environ.get('JWT_ACCESS_TTL', '3600'))      # 1 hour
JWT_REFRESH_TTL = int(os.environ.get('JWT_REFRESH_TTL', '604800'))  # 7 days

# Chat upload temp files — cleanup_uploads management command
UPLOAD_CLEANUP_MAX_AGE_DAYS = int(os.environ.get('UPLOAD_CLEANUP_MAX_AGE_DAYS', '7'))

# ── Airtest migration feature flags (toggle per environment) ──
AIRTEST_ENABLED = os.environ.get('AIRTEST_ENABLED', 'True').lower() in ('true', '1', 'yes')

# ── Project-specific configuration ──
DEVICE_SERIAL = os.environ.get('DEVICE_SERIAL', '')
SCREENSHOT_INTERVAL = float(os.environ.get('SCREENSHOT_INTERVAL', '0.5'))
SERVER_PORT = int(os.environ.get('SERVER_PORT', '8765'))

# Paths
DATA_DIR = BASE_DIR / 'data'
SCREENSHOT_DIR = DATA_DIR / 'screenshots'
EXPORT_DIR = BASE_DIR / 'exports'
LOG_DIR = BASE_DIR / 'logs'

# Internationalization
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_TZ = False

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ── Static files (Django Admin + jazzmin theme) ──
# Django 5.1+ 默认 STATIC_URL=None，必须显式设置，否则 Admin 无样式
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']  # 项目自定义静态文件源目录

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
        "apps.test_runner": "fas fa-play-circle",
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
