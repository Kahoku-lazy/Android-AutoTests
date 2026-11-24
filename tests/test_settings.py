"""
模块功能：➡️ 测试环境 Django 配置：继承生产 settings 并覆盖测试专用项 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/test_settings.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 被全部 pytest 用例加载（无独立用例）
🏁
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
