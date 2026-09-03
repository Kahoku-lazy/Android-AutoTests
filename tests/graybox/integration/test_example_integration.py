"""灰盒·集成测试示例 — Django ORM + 数据库（django_db）。

演示集成测试写法；真实用例请替换为对应模块的 ORM/多模块协作测试。

注意：django_db 使用 config.test_settings（SQLite :memory:）。
部分 App 迁移链含 MySQL 专属 RunSQL（如 test_runner/0017、ai_assistant/0021），
SQLite 测试库可能无法建库；涉及这些 App 的集成测试需 mock 或显式跳过。
"""

import pytest

from django.contrib.auth import get_user_model


@pytest.mark.integration
@pytest.mark.django_db
def test_create_and_retrieve_user():
    user_model = get_user_model()
    user = user_model.objects.create_user(username="it_dummy", password="dummy-pass-123")
    fetched = user_model.objects.get(username="it_dummy")
    assert fetched.id == user.id
    assert fetched.check_password("dummy-pass-123")
