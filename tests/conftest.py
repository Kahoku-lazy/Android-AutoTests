"""
模块功能：➡️ tests/ 全局公共 fixture：MySQL 排序规则注册与 base_url 🏁
Python 调试：➡️ python -m pytest -c tests/pytest.ini tests/conftest.py 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 覆盖 被 tests/<模块>/ 下全部用例共用（无独立用例）
🏁
"""

import os

import pytest

from django.db.backends.signals import connection_created


def _register_mysql_collation(sender, connection, **kwargs):
    """SQLite 测试库没有 utf8mb4_bin，注册同名排序规则以保持区分大小写。"""
    if connection.vendor == "sqlite":
        connection.connection.create_collation("utf8mb4_bin", lambda a, b: (a > b) - (a < b))


connection_created.connect(_register_mysql_collation)

BASE_URL = os.environ.get("TEST_BASE_URL", "http://localhost:8766")


@pytest.fixture(scope="session")
def base_url() -> str:
    """被测后端根地址，默认 http://localhost:8766，可用 TEST_BASE_URL 覆盖。"""
    return BASE_URL
