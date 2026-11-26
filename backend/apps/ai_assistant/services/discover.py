from engines.backend_bridge.models import discover_models
from engines.backend_bridge.models.catalog import expected_key


def discover_model_names(provider: str, api_key_env: str, base_url: str = "") -> dict:
    expected_key(provider)
    return discover_models(provider, api_key_env, base_url)
