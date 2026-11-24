"""模型配置删除：被知识库检索引用时拒绝，未被引用时允许。"""

from __future__ import annotations

import pytest

from backend.apps.ai_assistant import api
from backend.apps.ai_assistant.models import AIModelConfig, AIRole
from backend.apps.ai_assistant.services.model_configs import delete_model_config
from backend.apps.knowledge_search.models import RetrievalSettings

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def test_referenced_embedding_model_cannot_be_deleted():
    """检索配置指向的向量模型删不掉，行还在。"""
    config = AIModelConfig.objects.create(
        provider="dashscope",
        api_key_env="DASHSCOPE_API_KEY",
        model_kind="embedding",
        model_name="text-embedding-v4",
        dimensions=1024,
    )
    RetrievalSettings.objects.create(
        embedding_model_id=config.id,
        top_k=4,
        score_threshold=0.45,
        chunk_size=400,
        chunk_overlap=60,
    )
    with pytest.raises(ValueError, match="知识库检索"):
        delete_model_config(config)
    assert AIModelConfig.objects.filter(pk=config.id).exists()


def test_embedding_model_cannot_bind_to_role():
    """向量模型绑不上 Agent 配置，原绑定保持不变。"""
    chat = AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_kind="chat",
        model_name="deepseek-flash",
        base_url="https://llm.example/v1",
    )
    embedding = AIModelConfig.objects.create(
        provider="dashscope",
        api_key_env="DASHSCOPE_API_KEY",
        model_kind="embedding",
        model_name="text-embedding-v4",
        dimensions=1024,
    )
    role = api.create_role("页面执行", chat.id, "原文")
    with pytest.raises(ValueError, match="聊天模型"):
        api.create_role("另一个", embedding.id)
    with pytest.raises(ValueError, match="聊天模型"):
        api.update_role(role, {"model_config_id": embedding.id})
    assert AIRole.objects.get(pk=role.pk).model_config_id == chat.id


def test_unreferenced_model_can_be_deleted():
    """没有被检索配置引用的模型可以删除。"""
    config = AIModelConfig.objects.create(
        provider="dashscope",
        api_key_env="DASHSCOPE_API_KEY",
        model_kind="embedding",
        model_name="text-embedding-spare",
        dimensions=1024,
    )
    delete_model_config(config)
    assert not AIModelConfig.objects.filter(pk=config.id).exists()
