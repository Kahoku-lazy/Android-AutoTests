"""从模块登记（DB 真相源）派生平台知识库目录 yaml。

本模块不 import engines：引擎整目录删除后模块登记面仍可用。
defaults 段只读复制引擎自带目录的调优参数；引擎校验在检索装载时复用
（retrieval 经 load_config(bases_path=…) 再过一遍同一套规则）。
"""

from __future__ import annotations

from pathlib import Path

import yaml

from django.conf import settings

from .models import KnowledgeModule


def bases_file() -> Path:
    """
    平台检索库目录 yaml 的落盘路径。

    Returns:
        settings.KNOWLEDGE_SEARCH_BASES_FILE 指向的路径。
    """
    return Path(settings.KNOWLEDGE_SEARCH_BASES_FILE)


def engine_bases_file() -> Path:
    """
    引擎自带库目录 yaml 的路径（只读参照）。

    Returns:
        engines/ae_harness/knowledge/config/knowledge_bases.yaml 的绝对路径。
    """
    return (
        Path(settings.REPO_ROOT)
        / "engines"
        / "ae_harness"
        / "knowledge"
        / "config"
        / "knowledge_bases.yaml"
    )


def sync_yaml() -> Path:
    """
    由 DB 全量重生成平台库目录 yaml。

    Returns:
        写入的文件路径。

    Raises:
        OSError: 目标目录不可写。
    """
    payload: dict = {"defaults": _defaults()}
    for module in KnowledgeModule.objects.order_by("name"):
        payload[module.name] = {
            "description": module.description,
            "data_dir": module.data_dir,
            "enabled": module.enabled,
        }
    target = bases_file()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        yaml.safe_dump(payload, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    return target


def _defaults() -> dict:
    """
    只读复制引擎自带目录的 defaults 段，保留调优后的检索参数。

    Returns:
        defaults 字典；引擎文件缺失或损坏时为空字典（引擎装载会用内置默认）。
    """
    try:
        raw = yaml.safe_load(engine_bases_file().read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    defaults = raw.get("defaults")
    return dict(defaults) if isinstance(defaults, dict) else {}


def defaults() -> dict:
    """
    公开读取引擎调优参数（评测快照目录用）。

    Returns:
        defaults 字典。
    """
    return _defaults()
