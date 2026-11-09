"""测试环境 Django 配置。

位置：`tests/test_settings.py`（测试相关代码统一收在 `tests/` 下）。
继承正式配置，覆盖以下项：
- 数据库：SQLite 内存库（测试间事务隔离，自动回滚）
- DEBUG：开启（测试中获取详细错误信息）

Channel layer 不再单独覆盖：正式配置本身就是 InMemory（Redis 已退役），测试与生产同构。
"""

from backend.config.settings import *  # noqa: F403

# ── 数据库：SQLite 内存库 ──
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    },
}

# ── 调试 ──
DEBUG = True

# ── CORS：测试环境允许全部来源 ──
CORS_ALLOW_ALL_ORIGINS = True
