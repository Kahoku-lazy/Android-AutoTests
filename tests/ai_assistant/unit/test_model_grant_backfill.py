"""模型名单补齐：重复执行不产生第二条关系，普通用户保持空名单。"""

from __future__ import annotations

from importlib import import_module

import pytest

from django.contrib.auth import get_user_model

from backend.apps.ai_assistant.models import AIModelConfig, ModelUseGrant

migration = import_module("backend.apps.ai_assistant.migrations.0079_model_use_grant")

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def test_backfill_can_run_twice_without_duplicates():
    root = get_user_model().objects.create_user(
        username="backfill-root",
        password="pass",
        is_superuser=True,
    )
    plain = get_user_model().objects.create_user(username="backfill-plain", password="pass")
    config = AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name="deepseek-backfill",
    )

    migration.backfill_existing_use()
    migration.backfill_existing_use()

    assert ModelUseGrant.objects.filter(user_id=root.id, model_config=config).count() == 1
    assert ModelUseGrant.objects.filter(user_id=plain.id).count() == 0
