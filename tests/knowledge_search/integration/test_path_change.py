from __future__ import annotations

import pytest

from backend.apps.ai_assistant.models import AIModelConfig
from backend.apps.knowledge_search import api, retrieval
from backend.apps.knowledge_search.models import RetrievalSettings

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@pytest.fixture(autouse=True)
def _settings_row():
    model = AIModelConfig.objects.create(
        provider="dashscope",
        api_key_env="DASHSCOPE_API_KEY",
        model_kind="embedding",
        model_name="text-embedding-v4",
        dimensions=1024,
    )
    RetrievalSettings.objects.create(
        embedding_model_id=model.id,
        top_k=4,
        score_threshold=0.45,
        chunk_size=400,
        chunk_overlap=60,
    )


def test_path_change_switches_engine_catalog(tmp_path):
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()

    module = api.create_module(name="kb_a", description="说明", data_dir=str(old_dir))
    config = retrieval._platform_config()
    assert config.base("kb_a").data_dir == old_dir.resolve()

    api.update_module(module.pk, data_dir=str(new_dir))
    switched = retrieval._platform_config()
    assert switched.base("kb_a").data_dir == new_dir.resolve()
    assert all(spec.data_dir != old_dir.resolve() for spec in switched.bases)


def test_disable_module_excludes_it_from_enabled_bases(tmp_path):
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    api.create_module(name="kb_a", description="说明", data_dir=str(dir_a))
    module_b = api.create_module(name="kb_b", description="说明", data_dir=str(dir_b))
    api.update_module(module_b.pk, enabled=False)
    config = retrieval._platform_config()
    assert [spec.name for spec in config.enabled_bases()] == ["kb_a"]
    assert config.base("kb_b") is not None
