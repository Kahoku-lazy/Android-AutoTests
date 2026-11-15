"""知识库模块独立性守护：可整目录删除，不牵连 Harness 其它模块。

只读源码做导入扫描（契约对拍），不导入被测模块、不联网。
两侧边界都查：
- 知识库不得 import Harness 其它子包（否则删掉它会带走别人）；
- Harness 其它模块不得 import 知识库（本期尚未挂载，引用数必须为零）。
"""

from __future__ import annotations

import ast

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

HARNESS_DIR = Path(__file__).resolve().parents[4] / "engines" / "ae_harness"
KNOWLEDGE_DIR = HARNESS_DIR / "knowledge"

# 知识库不得依赖的相邻子包。
FORBIDDEN_SIBLINGS = (
    "engines.ae_harness.agents",
    "engines.ae_harness.assistant",
    "engines.ae_harness.event",
    "engines.ae_harness.middleware",
    "engines.ae_harness.workflow",
    "engines.ae_harness.tools",
)
# 最小规模：识别规则退化时计数骤降，测试随即失败。
MIN_KNOWLEDGE_FILES = 8


def _imports(source: str) -> list[str]:
    """取出源码里的导入模块名（相对导入记为 `.目标`）。

    Args:
        source: 一段 Python 源码。

    Returns:
        导入的模块名列表。
    """
    names: list[str] = []
    for node in ast.walk(ast.parse(source)):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * (node.level or 0)
            names.append(f"{prefix}{node.module or ''}")
    return names


def test_knowledge_does_not_import_harness_siblings():
    """知识库内部不出现对 Harness 其它子包的导入。"""
    files = sorted(KNOWLEDGE_DIR.rglob("*.py"))
    assert len(files) >= MIN_KNOWLEDGE_FILES

    offenders: list[str] = []
    for path in files:
        for name in _imports(path.read_text(encoding="utf-8")):
            if name.startswith(FORBIDDEN_SIBLINGS):
                offenders.append(f"{path.name}: {name}")
    assert offenders == []


def test_no_harness_module_references_knowledge():
    """本期不挂载：Harness 其它模块对知识库的引用数必须为零。"""
    callers: list[str] = []
    for path in sorted(HARNESS_DIR.rglob("*.py")):
        if KNOWLEDGE_DIR in path.parents:
            continue
        text = path.read_text(encoding="utf-8")
        if "engines.ae_harness.knowledge" in text:
            callers.append(path.relative_to(HARNESS_DIR).as_posix())
    assert callers == []
