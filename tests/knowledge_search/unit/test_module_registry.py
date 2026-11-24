"""知识库模块登记单测：校验规则与 CRUD。"""

from __future__ import annotations

import importlib

import pytest

from backend.apps.knowledge_search import api
from backend.apps.knowledge_search.models import KnowledgeModule

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


@pytest.fixture()
def data_dir(tmp_path):
    """造一个存在的资料目录。"""
    target = tmp_path / "docs"
    target.mkdir()
    return target


def test_create_module_persists(data_dir):
    """合法登记落库，资料目录取绝对路径。"""
    module = api.create_module(
        name="kb_a",
        description="测试库",
        data_dir=str(data_dir),
    )
    assert module.pk is not None
    assert module.data_dir == str(data_dir.resolve())
    assert module.enabled is True


@pytest.mark.parametrize("name", ["Bad", "1x", "bad-name", "", "kb a"])
def test_invalid_name_rejected(name, data_dir):
    """非法库名不落库。"""
    with pytest.raises(ValueError, match="库名不合法"):
        api.create_module(name=name, description="说明", data_dir=str(data_dir))
    assert KnowledgeModule.objects.count() == 0


def test_duplicate_name_rejected(data_dir):
    """重名不落库。"""
    api.create_module(name="kb_a", description="说明", data_dir=str(data_dir))
    other = data_dir.parent / "other"
    other.mkdir()
    with pytest.raises(ValueError, match="库名已存在"):
        api.create_module(name="kb_a", description="说明", data_dir=str(other))
    assert KnowledgeModule.objects.count() == 1


def test_empty_description_rejected(data_dir):
    """空说明不落库。"""
    with pytest.raises(ValueError, match="说明不能为空"):
        api.create_module(name="kb_a", description="  ", data_dir=str(data_dir))


def test_relative_or_missing_dir_rejected(tmp_path, data_dir):
    """相对路径与不存在目录不落库。"""
    with pytest.raises(ValueError, match="绝对路径"):
        api.create_module(name="kb_a", description="说明", data_dir="relative/docs")
    with pytest.raises(ValueError, match="不存在"):
        api.create_module(name="kb_a", description="说明", data_dir=str(tmp_path / "nope"))
    assert KnowledgeModule.objects.count() == 0


def test_overlapping_enabled_dirs_rejected(data_dir):
    """启用库目录相同或互相包含被拒绝；禁用库不参与隔离。"""
    api.create_module(name="kb_a", description="说明", data_dir=str(data_dir))
    with pytest.raises(ValueError, match="目录冲突"):
        api.create_module(name="kb_b", description="说明", data_dir=str(data_dir))
    child = data_dir / "sub"
    child.mkdir()
    with pytest.raises(ValueError, match="目录冲突"):
        api.create_module(name="kb_b", description="说明", data_dir=str(child))
    # 禁用库允许与启用库同目录
    api.create_module(name="kb_off", description="说明", data_dir=str(data_dir), enabled=False)
    assert KnowledgeModule.objects.count() == 2


def test_update_path_and_enabled(data_dir, tmp_path):
    """改路径与启停落库。"""
    module = api.create_module(name="kb_a", description="说明", data_dir=str(data_dir))
    new_dir = tmp_path / "new_docs"
    new_dir.mkdir()
    updated = api.update_module(module.pk, data_dir=str(new_dir), enabled=False)
    assert updated.data_dir == str(new_dir.resolve())
    assert updated.enabled is False


def test_update_unknown_field_and_missing_module(data_dir):
    """未知字段与不存在模块被拒绝。"""
    module = api.create_module(name="kb_a", description="说明", data_dir=str(data_dir))
    with pytest.raises(ValueError, match="未知字段"):
        api.update_module(module.pk, owner="x")
    with pytest.raises(ValueError, match="模块不存在"):
        api.update_module(999999, enabled=False)


def test_delete_module_removes_row(data_dir):
    """删除只删登记，不存在时返回假。"""
    module = api.create_module(name="kb_a", description="说明", data_dir=str(data_dir))
    assert api.delete_module(module.pk) is True
    assert api.delete_module(module.pk) is False
    assert KnowledgeModule.objects.filter(name="kb_a").count() == 0


def test_seed_migration_is_noop_without_engine_catalog():
    """引擎库目录文件已删除：种子迁移找不到文件时不导入、不报错。"""
    KnowledgeModule.objects.all().delete()
    seed_migration = importlib.import_module(
        "backend.apps.knowledge_search.migrations.0002_seed_modules"
    )

    class _Apps:
        def get_model(self, app_label, model_name):
            return KnowledgeModule

    seed_migration.seed_modules(_Apps(), None)
    assert KnowledgeModule.objects.count() == 0
