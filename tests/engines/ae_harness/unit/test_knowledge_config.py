"""知识库自带配置：向量模型字段、库目录隔离与密钥取值。

只读自带 yaml 与临时 yaml，不联网、不建索引。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.knowledge.config import load_config, load_secret

pytestmark = [pytest.mark.unit]

_MODELS = """
dashscope_embedding_v4:
  provider: dashscope
  api_key: DASHSCOPE_API_KEY
  model_name: text-embedding-v4
  dimensions: 1024
"""


def _write(tmp_path, models: str, bases: str):
    """把两份 yaml 写进临时目录并返回路径。

    Args:
        tmp_path: pytest 临时目录。
        models: 向量模型 yaml 正文。
        bases: 库目录 yaml 正文。

    Returns:
        (models 路径, bases 路径)。
    """
    models_path = tmp_path / "models.yaml"
    bases_path = tmp_path / "knowledge_bases.yaml"
    models_path.write_text(models, encoding="utf-8")
    bases_path.write_text(bases, encoding="utf-8")
    return models_path, bases_path


def test_bundled_config_loads_vector_model_only():
    """自带配置只含向量模型，且库目录里只有一个启用库。"""
    config = load_config()
    assert config.embedding.provider == "dashscope"
    assert config.embedding.dimensions == 1024
    assert [spec.name for spec in config.enabled_bases()] == ["product_manuals"]
    assert config.top_k == 4
    assert 0 < config.score_threshold <= 1


def test_chat_entry_is_rejected(tmp_path):
    """向量模型文件里出现 chat 字段时装载失败。"""
    models = """
dashscope_embedding_v4:
  provider: dashscope
  model_name: text-embedding-v4
  stream: true
"""
    bases = "product_manuals:\n  description: d\n  data_dir: sub\n  enabled: true\n"
    models_path, bases_path = _write(tmp_path, models, bases)
    with pytest.raises(ValueError):
        load_config(models_path=models_path, bases_path=bases_path)


def test_non_dashscope_provider_is_rejected(tmp_path):
    """provider 只允许 dashscope。"""
    models = "hunyuan:\n  provider: deepseek\n  model_name: x\n"
    bases = "product_manuals:\n  description: d\n  data_dir: sub\n  enabled: true\n"
    models_path, bases_path = _write(tmp_path, models, bases)
    with pytest.raises(ValueError):
        load_config(models_path=models_path, bases_path=bases_path)


def test_unknown_embedding_name_is_rejected(tmp_path):
    """defaults 引用不存在的向量模型短名时装载失败。"""
    bases = (
        "defaults:\n  embedding: missing_model\n"
        "product_manuals:\n  description: d\n  data_dir: sub\n  enabled: true\n"
    )
    models_path, bases_path = _write(tmp_path, _MODELS, bases)
    with pytest.raises(ValueError, match="未知向量模型"):
        load_config(models_path=models_path, bases_path=bases_path)


def test_overlapping_enabled_dirs_are_rejected(tmp_path):
    """两个启用库的资料目录互相包含时装载失败。"""
    bases = (
        "defaults:\n  embedding: dashscope_embedding_v4\n"
        "alpha:\n  description: a\n  data_dir: sub\n  enabled: true\n"
        "beta:\n  description: b\n  data_dir: sub/inner\n  enabled: true\n"
    )
    models_path, bases_path = _write(tmp_path, _MODELS, bases)
    with pytest.raises(ValueError, match="冲突"):
        load_config(models_path=models_path, bases_path=bases_path)


def test_unknown_base_field_is_rejected(tmp_path):
    """库条目出现未知字段时装载失败。"""
    bases = (
        "defaults:\n  embedding: dashscope_embedding_v4\n"
        "alpha:\n  description: a\n  data_dir: sub\n  enabled: true\n  top_k: 9\n"
    )
    models_path, bases_path = _write(tmp_path, _MODELS, bases)
    with pytest.raises(ValueError, match="未知字段"):
        load_config(models_path=models_path, bases_path=bases_path)


def test_load_secret_prefers_injected_environ():
    """注入的进程环境优先，且只返回值不打印。"""
    assert load_secret("DASHSCOPE_API_KEY", {"DASHSCOPE_API_KEY": "sk-demo"}) == "sk-demo"
    assert load_secret("MISSING_KEY", {}) == ""
