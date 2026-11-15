"""知识库目录装载：库名、目录冲突和禁用库。"""

from __future__ import annotations

from pathlib import Path

import pytest

from engines.agents.rag.catalog import load_knowledge_catalog

pytestmark = [pytest.mark.unit]


def _write(path: Path, text: str) -> Path:
    path.write_text(text, encoding="utf-8")
    return path


def test_catalog_loads_enabled_and_disabled_bases(tmp_path):
    path = _write(
        tmp_path / "knowledge_bases.yaml",
        """
product_manuals:
  description: 产品资料
  data_dir: manuals
  enabled: true
log_keywords:
  description: 日志关键词
  data_dir: keywords
  enabled: false
""",
    )

    specs = {spec.name: spec for spec in load_knowledge_catalog(path)}

    assert specs["product_manuals"].enabled is True
    assert specs["log_keywords"].enabled is False
    assert specs["product_manuals"].data_dir == (tmp_path / "manuals").resolve()


def test_catalog_rejects_overlapping_enabled_dirs(tmp_path):
    path = _write(
        tmp_path / "knowledge_bases.yaml",
        """
left:
  description: 左库
  data_dir: shared
right:
  description: 右库
  data_dir: shared/child
""",
    )

    with pytest.raises(ValueError, match="left 与 right"):
        load_knowledge_catalog(path)


def test_catalog_rejects_illegal_name(tmp_path):
    path = _write(
        tmp_path / "knowledge_bases.yaml",
        """
bad-name:
  description: 非法库名
  data_dir: docs
""",
    )

    with pytest.raises(ValueError, match="知识库名不合法"):
        load_knowledge_catalog(path)
