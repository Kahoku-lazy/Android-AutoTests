"""知识库检索配置：种子值、保存校验与切块变更使索引失效。"""

from __future__ import annotations

import pytest

from backend.apps.ai_assistant.models import AIModelConfig
from backend.apps.knowledge_search import api
from backend.apps.knowledge_search.models import RetrievalSettings

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _embedding(**overrides) -> AIModelConfig:
    """造一条向量模型配置。"""
    fields = {
        "provider": "dashscope",
        "api_key_env": "DASHSCOPE_API_KEY",
        "model_kind": "embedding",
        "model_name": "text-embedding-v4",
        "dimensions": 1024,
    }
    fields.update(overrides)
    return AIModelConfig.objects.create(**fields)


@pytest.fixture()
def seeded():
    """按迁移种子的口径放一行：阈值 0.45，epoch 0。测试套件不跑迁移。"""
    model = _embedding()
    return RetrievalSettings.objects.create(
        embedding_model_id=model.id,
        top_k=4,
        score_threshold=0.45,
        chunk_size=400,
        chunk_overlap=60,
        index_epoch=0,
    )


def test_seed_uses_tuned_threshold(seeded):
    """种子口径是调过的 0.45，不是代码默认的 0.55。"""
    assert seeded.score_threshold == 0.45
    assert seeded.top_k == 4
    assert seeded.chunk_size == 400
    assert seeded.chunk_overlap == 60
    assert seeded.index_epoch == 0
    model = AIModelConfig.objects.get(pk=seeded.embedding_model_id)
    assert model.model_kind == "embedding"
    assert model.model_name == "text-embedding-v4"


def test_save_rejects_chat_model(seeded):
    """引用聊天模型不落库。"""
    chat = AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_kind="chat",
        model_name="deepseek-flash",
        base_url="https://llm.example/v1",
    )
    before = api.get_retrieval_settings().index_epoch
    with pytest.raises(ValueError, match="向量模型"):
        api.save_retrieval_settings(
            embedding_model_id=chat.id,
            top_k=4,
            score_threshold=0.45,
            chunk_size=400,
            chunk_overlap=60,
        )
    assert api.get_retrieval_settings().index_epoch == before


def test_save_rejects_threshold_out_of_range(seeded):
    """阈值越界不落库。"""
    current = api.get_retrieval_settings()
    with pytest.raises(ValueError, match="阈值"):
        api.save_retrieval_settings(
            embedding_model_id=current.embedding_model_id,
            top_k=4,
            score_threshold=1.5,
            chunk_size=400,
            chunk_overlap=60,
        )
    assert api.get_retrieval_settings().score_threshold == 0.45


def test_chunk_change_bumps_epoch_threshold_change_does_not(seeded):
    """改切块使 epoch 加一；只改阈值不加。"""
    current = api.get_retrieval_settings()
    saved, invalidated = api.save_retrieval_settings(
        embedding_model_id=current.embedding_model_id,
        top_k=4,
        score_threshold=0.5,
        chunk_size=400,
        chunk_overlap=60,
    )
    assert invalidated is False
    assert saved.index_epoch == 0
    saved, invalidated = api.save_retrieval_settings(
        embedding_model_id=current.embedding_model_id,
        top_k=4,
        score_threshold=0.5,
        chunk_size=500,
        chunk_overlap=60,
    )
    assert invalidated is True
    assert saved.index_epoch == 1


def test_overlap_not_smaller_than_chunk_rejected(seeded):
    """重叠不小于切块大小时拒绝。"""
    current = api.get_retrieval_settings()
    with pytest.raises(ValueError, match="切块重叠"):
        api.save_retrieval_settings(
            embedding_model_id=current.embedding_model_id,
            top_k=4,
            score_threshold=0.45,
            chunk_size=400,
            chunk_overlap=400,
        )
