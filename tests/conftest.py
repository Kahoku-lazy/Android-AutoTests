"""tests/ 三层测试框架的全局公共 fixture。

目录按被测模块分，模块内再按测试类型分（unit / integration / api / e2e），见 tests/AGENTS.md。
共享设施：
  - tests/api/      接口测试夹具与 YAML 用例（scripts 已按模块归位）
  - tests/api_kit/  接口测试加载器与 JSONSchema
  - tests/e2e/      端到端夹具（用例已按模块归位）
  - tests/arch/     跨模块契约测试

共享 fixture 只放跨层通用的最小项；各层专属 fixture 放各自 conftest.py。
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
