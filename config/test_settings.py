"""测试环境 Django 配置。

继承正式配置，覆盖以下项：
- 数据库：SQLite 内存库（测试间事务隔离，自动回滚）
- Channel Layers：InMemory（不依赖 Redis）
- DEBUG：开启（测试中获取详细错误信息）
"""

from config.settings import *  # noqa: F403

# ── 数据库：SQLite 内存库 ──
DB_ENGINE = "sqlite"  # noqa: F405
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

# ── Channel Layers：内存实现（无需 Redis）──
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# ── 调试 ──
DEBUG = True

# ── CORS：测试环境允许全部来源 ──
CORS_ALLOW_ALL_ORIGINS = True
