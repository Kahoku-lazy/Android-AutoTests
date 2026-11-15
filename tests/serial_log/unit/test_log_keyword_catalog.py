"""关键词目录一致性：按型号目录里的关键词必须都在全量目录里登记。"""

from __future__ import annotations

import json
import re

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[3]
KEYWORDS_DIR = REPO_ROOT / "engines" / "agents" / "config" / "data" / "log_keywords"
FULL_CATALOG = REPO_ROOT / "backend" / "config" / "device_log_keywords.json"

_KEYWORD_LINE = re.compile(r"→\s*([a-z][a-z0-9_]*)\s*$")


def _md_keywords() -> dict[str, set[str]]:
    """型号 → 该文件里列出的关键词集合。"""
    found: dict[str, set[str]] = {}
    for path in sorted(KEYWORDS_DIR.glob("*.md")):
        keywords = set()
        for line in path.read_text(encoding="utf-8").splitlines():
            match = _KEYWORD_LINE.search(line.strip())
            if match:
                keywords.add(match.group(1))
        found[path.stem] = keywords
    return found


def test_catalog_files_exist():
    """至少维护了一个型号的目录。"""
    assert KEYWORDS_DIR.is_dir()
    assert _md_keywords(), "log_keywords 目录下没有任何型号文件"


def test_every_keyword_is_registered_in_full_catalog():
    """每个型号目录里的关键词都必须在全量目录里登记，防止拼错或臆造。"""
    registered = set(json.loads(FULL_CATALOG.read_text(encoding="utf-8"))["keywords"])
    unknown: list[str] = []
    for sku, keywords in _md_keywords().items():
        for keyword in sorted(keywords - registered):
            unknown.append(f"{sku}.md: {keyword}")

    assert unknown == [], "型号目录里出现全量目录未登记的关键词：\n" + "\n".join(unknown)


def test_each_catalog_lists_at_least_one_keyword():
    """每个型号文件都要给出可用的关键词，空文件视为没维护。"""
    empty = [sku for sku, keywords in _md_keywords().items() if not keywords]

    assert empty == [], f"这些型号文件里没有解析到关键词：{empty}"
