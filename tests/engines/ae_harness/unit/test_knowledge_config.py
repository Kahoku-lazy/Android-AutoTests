"""知识库配置：向量模型字段、库目录隔离与密钥取值。

参数直接传入，不读配置文件，不联网、不建索引。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.knowledge.config import build_config, load_secret

pytestmark = [pytest.mark.unit]

_EMBEDDING = {
    "provider": "dashscope",
    "api_key": "DASHSCOPE_API_KEY",
    "model_name": "text-embedding-v4",
    "dimensions": 1024,
}


def _base(name: str, data_dir, *, enabled: bool = True) -> dict:
    """造一条库参数。"""
    return {
        "name": name,
        "description": f"{name} 说明",
        "data_dir": str(data_dir),
        "enabled": enabled,
    }


def test_build_config_keeps_vector_model(tmp_path):
    """合法参数组装出向量模型与启用库。"""
    docs = tmp_path / "docs"
    docs.mkdir()
    config = build_config(_EMBEDDING, [_base("product_manuals", docs)], score_threshold=0.45)
    assert config.embedding.provider == "dashscope"
    assert config.embedding.dimensions == 1024
    assert [spec.name for spec in config.enabled_bases()] == ["product_manuals"]
    assert config.top_k == 4
    assert config.score_threshold == 0.45


def test_chat_field_is_rejected(tmp_path):
    """向量模型参数里出现 chat 字段时组装失败。"""
    docs = tmp_path / "docs"
    docs.mkdir()
    with pytest.raises(ValueError, match="stream"):
        build_config({**_EMBEDDING, "stream": True}, [_base("product_manuals", docs)])


def test_non_dashscope_provider_is_rejected(tmp_path):
    """provider 只允许 dashscope。"""
    docs = tmp_path / "docs"
    docs.mkdir()
    with pytest.raises(ValueError, match="provider"):
        build_config({**_EMBEDDING, "provider": "deepseek"}, [_base("product_manuals", docs)])


def test_overlapping_enabled_dirs_are_rejected(tmp_path):
    """两个启用库的资料目录互相包含时组装失败。"""
    outer = tmp_path / "sub"
    inner = outer / "inner"
    inner.mkdir(parents=True)
    with pytest.raises(ValueError, match="冲突"):
        build_config(
            _EMBEDDING,
            [_base("alpha", outer), _base("beta", inner)],
        )


def test_unknown_base_field_is_rejected(tmp_path):
    """库条目出现未知字段时组装失败。"""
    docs = tmp_path / "docs"
    docs.mkdir()
    base = _base("alpha", docs)
    base["top_k"] = 9
    with pytest.raises(ValueError, match="未知字段"):
        build_config(_EMBEDDING, [base])


def test_relative_data_dir_is_rejected(tmp_path):
    """资料目录必须是绝对路径。"""
    with pytest.raises(ValueError, match="绝对路径"):
        build_config(_EMBEDDING, [_base("alpha", "docs")])


def test_load_secret_prefers_injected_environ():
    """注入的进程环境优先，且只返回值不打印。"""
    assert load_secret("DASHSCOPE_API_KEY", {"DASHSCOPE_API_KEY": "sk-demo"}) == "sk-demo"
    assert load_secret("MISSING_KEY", {}) == ""
