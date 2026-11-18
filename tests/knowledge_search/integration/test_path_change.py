"""改路径集成场景：登记 → 派生目录 → 引擎装载 → 改路径后目录切换。

不联网、不调嵌入 API；索引内容清理由引擎 test_knowledge_index.py 守护。
"""

from __future__ import annotations

import pytest
import yaml

from backend.apps.knowledge_search import api, registry
from engines.ae_harness.knowledge.config import load_config

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@pytest.fixture(autouse=True)
def _bases_file(tmp_path, settings):
    settings.KNOWLEDGE_SEARCH_BASES_FILE = tmp_path / "bases.yaml"


def test_path_change_switches_engine_catalog(tmp_path):
    """改路径后，引擎装载到的资料目录切到新目录，旧目录不再出现在目录里。"""
    old_dir = tmp_path / "old"
    new_dir = tmp_path / "new"
    old_dir.mkdir()
    new_dir.mkdir()
    (old_dir / "a.md").write_text("旧资料", encoding="utf-8")
    (new_dir / "b.md").write_text("新资料", encoding="utf-8")

    module = api.create_module(name="kb_a", description="说明", data_dir=str(old_dir))
    config = load_config(bases_path=registry.sync_yaml())
    assert config.base("kb_a").data_dir == old_dir.resolve()

    api.update_module(module.pk, data_dir=str(new_dir))
    payload = yaml.safe_load(registry.bases_file().read_text(encoding="utf-8"))
    assert payload["kb_a"]["data_dir"] == str(new_dir.resolve())
    assert str(old_dir.resolve()) not in registry.bases_file().read_text(encoding="utf-8")

    switched = load_config(bases_path=registry.bases_file())
    assert switched.base("kb_a").data_dir == new_dir.resolve()


def test_disable_module_excludes_it_from_enabled_bases(tmp_path):
    """停用模块仍在目录里，但不参与检索（enabled_bases 不含）。"""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    api.create_module(name="kb_a", description="说明", data_dir=str(dir_a))
    module_b = api.create_module(name="kb_b", description="说明", data_dir=str(dir_b))
    api.update_module(module_b.pk, enabled=False)
    config = load_config(bases_path=registry.sync_yaml())
    assert [spec.name for spec in config.enabled_bases()] == ["kb_a"]
    assert config.base("kb_b") is not None
