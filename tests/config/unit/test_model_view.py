"""只读模型视图：按短名看规格，不造实例、不解密。"""

from __future__ import annotations

import pytest

from engines.agents.config.model_view import model_view

pytestmark = [pytest.mark.unit]


def _catalog() -> dict:
    return {
        "deepseek_flash": {
            "family": "chat",
            "model_name": "deepseek-flash",
            "api_key_env": "DEEPSEEK_API_KEY",
            "api_key": "sk-should-not-appear",
        },
        "omni": {
            "family": "realtime",
            "model_name": "qwen3.5-omni-plus-realtime",
            "voices": ["Tina", "Cherry"],
        },
        "text_embedding_v4": {
            "family": "embedding",
            "model_name": "text-embedding-v4",
            "dimensions": 1024,
        },
    }


def test_known_short_name_returns_declared_fields():
    view = model_view(_catalog(), "text_embedding_v4")

    assert view.model_name == "text-embedding-v4"
    assert view.family == "embedding"
    assert view.dimensions == 1024
    assert "sk-" not in repr(view)


def test_unknown_short_name_lists_choices():
    with pytest.raises(ValueError, match="deepseek_flash"):
        model_view(_catalog(), "missing")


def test_missing_secret_still_viewable():
    catalog = _catalog()
    catalog["deepseek_flash"]["api_key"] = None

    view = model_view(catalog, "deepseek_flash")

    assert view.model_name == "deepseek-flash"
    assert view.api_key_env == "DEEPSEEK_API_KEY"
    assert view.voices == ()


def test_voices_missing_is_empty_tuple():
    assert model_view(_catalog(), "deepseek_flash").voices == ()
    assert model_view(_catalog(), "omni").voices == ("Tina", "Cherry")
