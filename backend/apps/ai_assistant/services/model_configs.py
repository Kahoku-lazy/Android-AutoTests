from backend.apps.ai_assistant.models import AIModelConfig, AIRole


class ModelConfigMissingError(Exception):
    pass


def get_model_config(config_id: int) -> AIModelConfig:
    config = AIModelConfig.objects.filter(id=config_id).first()
    if config is None:
        raise ModelConfigMissingError("所选模型配置不存在")
    return config


def list_model_configs(model_kind: str = ""):
    configs = AIModelConfig.objects.order_by("api_key_env", "model_name", "id")
    if model_kind:
        configs = configs.filter(model_kind=model_kind)
    return configs


def prepare_model_config(data: dict) -> dict:
    return {
        "provider": data["provider"],
        "api_protocol": data.get("api_protocol") or "",
        "model_kind": data.get("model_kind") or "chat",
        "voice": data.get("voice") or "",
        "api_key_env": data["api_key_env"],
        "base_url": data.get("base_url") or "",
        "model_name": data["model_name"],
        "dimensions": data.get("dimensions"),
    }


def update_model_config(config: AIModelConfig, data: dict) -> AIModelConfig:
    for field in (
        "provider",
        "api_protocol",
        "model_kind",
        "voice",
        "api_key_env",
        "base_url",
        "model_name",
        "dimensions",
    ):
        if field in data and data[field] is not None:
            setattr(config, field, data[field])
    config.save()
    return config


def delete_model_config(config: AIModelConfig) -> None:
    if AIRole.objects.filter(model_config=config).exists():
        raise ValueError("仍有 Agent 配置使用该模型，不能删除")
    if _used_by_retrieval(config):
        raise ValueError("仍被知识库检索使用，不能删除")
    config.delete()


def is_referenced(config: AIModelConfig) -> bool:
    return AIRole.objects.filter(model_config=config).exists()


def _used_by_retrieval(config: AIModelConfig) -> bool:
    from backend.apps.knowledge_search.models import RetrievalSettings

    return RetrievalSettings.objects.filter(embedding_model_id=config.id).exists()
