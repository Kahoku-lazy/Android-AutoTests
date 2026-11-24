"""模型配置写库。只登记连接参数，不创建模型实例。"""

from backend.apps.ai_assistant.models import AIModelConfig, AIRole


class ModelConfigMissingError(Exception):
    """请求的模型配置不存在。"""


def get_model_config(config_id: int) -> AIModelConfig:
    """按主键取模型配置。

    Args:
        config_id: 模型配置主键。

    Returns:
        模型配置行。

    Raises:
        ModelConfigMissingError: 主键不存在。
    """
    config = AIModelConfig.objects.filter(id=config_id).first()
    if config is None:
        raise ModelConfigMissingError("所选模型配置不存在")
    return config


def list_model_configs(model_kind: str = ""):
    """返回模型配置。传入类型时只返回该类型，供 Agent 配置下拉过滤。"""
    configs = AIModelConfig.objects.order_by("api_key_env", "model_name", "id")
    if model_kind:
        configs = configs.filter(model_kind=model_kind)
    return configs


def prepare_model_config(data: dict) -> dict:
    """把入参收成待写入字段。不写库。"""
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
    """修改一条模型配置。未提交的字段保持原值。"""
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
    """删除一条模型配置。已被 Agent 配置引用时拒绝。

    Raises:
        ValueError: 仍有 Agent 配置引用这条模型配置。
    """
    if AIRole.objects.filter(model_config=config).exists():
        raise ValueError("仍有 Agent 配置使用该模型，不能删除")
    if _used_by_retrieval(config):
        raise ValueError("仍被知识库检索使用，不能删除")
    config.delete()


def is_referenced(config: AIModelConfig) -> bool:
    """这条模型配置是否已被 Agent 配置引用。"""
    return AIRole.objects.filter(model_config=config).exists()


def _used_by_retrieval(config: AIModelConfig) -> bool:
    """知识库检索配置是否引用这条模型。只读对方的表，不调写库。"""
    from backend.apps.knowledge_search.models import RetrievalSettings

    return RetrievalSettings.objects.filter(embedding_model_id=config.id).exists()
