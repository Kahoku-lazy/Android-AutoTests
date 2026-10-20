"""引擎 OCR 工具：实现存在、只读、且不装配给任何角色。"""

from __future__ import annotations

import ast
import shutil
import subprocess

from pathlib import Path

import pytest

from PIL import Image

from engines.agents import tools_config
from engines.agents.tools import tool_ocr

pytestmark = pytest.mark.unit


def test_ocr_spec_exists_and_is_read_only():
    """工具规格存在，且只读。"""
    specs = tool_ocr.ocr_tool_specs()
    assert [spec.name for spec in specs] == ["ocr_page"]
    assert specs[0].read_only is True


def test_ocr_is_not_assigned_to_any_role():
    """执行/验收的基础工具与全部可开关组都不得包含 OCR。"""
    names = set(tools_config.EXECUTOR_BASIC_TOOL_NAMES)
    names.update(tools_config.VERIFIER_BASIC_TOOL_NAMES)
    for group in tools_config.EXECUTOR_TOOL_GROUPS:
        names.update(group.tool_names)
    assert "ocr_page" not in names


def test_ocr_payload_filters_texts_and_normalizes_center(tmp_path, monkeypatch):
    """文本过滤按忽略大小写的子串匹配，中心点按截图尺寸归一化。"""
    shot = tmp_path / "shot.png"
    Image.new("RGB", (200, 400), "white").save(shot)
    monkeypatch.setattr(
        tool_ocr,
        "_recognize",
        lambda _path: [
            {"text": "设置", "confidence": 0.9, "coordinates": [[20, 40], [60, 80]]},
            {"text": "WiFi", "confidence": 0.8, "coordinates": [[100, 100], [180, 180]]},
        ],
    )

    payload = tool_ocr._ocr_payload(str(shot), "设置")

    assert payload["screen_w"] == 200
    assert payload["screen_h"] == 400
    assert [item["text"] for item in payload["texts"]] == ["设置"]
    assert payload["texts"][0]["center"] == [0.2, 0.15]


def test_ocr_payload_without_filter_returns_all(tmp_path, monkeypatch):
    """不传过滤文本时返回整页全部条目。"""
    shot = tmp_path / "shot.png"
    Image.new("RGB", (100, 100), "white").save(shot)
    monkeypatch.setattr(
        tool_ocr,
        "_recognize",
        lambda _path: [
            {"text": "甲", "confidence": 0.7, "coordinates": [[0, 0], [10, 10]]},
            {"text": "乙", "confidence": 0.6, "coordinates": [[20, 20], [40, 40]]},
        ],
    )

    payload = tool_ocr._ocr_payload(str(shot), "")

    assert [item["text"] for item in payload["texts"]] == ["甲", "乙"]


def test_vision_package_is_only_referenced_by_ocr_tool():
    """页面文本识别包只出现在自身与引擎 OCR 工具中。"""
    root = Path(__file__).resolve().parents[3]
    needle = "engines" + ".vision"
    allowed = {
        root / "engines" / "__init__.py",
        root / "engines" / "agents" / "tools" / "tool_ocr.py",
    }
    skip = {"__pycache__", ".venv", "venv", "node_modules", ".git"}
    hits: list[Path] = []
    for path in root.rglob("*.py"):
        if skip.intersection(path.parts):
            continue
        if path.is_relative_to(root / "engines" / "vision"):
            continue
        if needle in path.read_text(encoding="utf-8"):
            hits.append(path)
    assert set(hits) == allowed


def test_ocr_tool_imports_vision_only_inside_function():
    """工具模块顶层不导入识别包，避免引擎启动拉起 cnocr。"""
    path = Path(__file__).resolve().parents[3] / "engines" / "agents" / "tools" / "tool_ocr.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))
    needle = "engines" + ".vision"
    for node in tree.body:
        modules: list[str] = []
        if isinstance(node, ast.ImportFrom) and node.module:
            modules.append(node.module)
        elif isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        assert all(not name.startswith(needle) for name in modules)


_SKIP_DIRS = {"__pycache__", ".venv", "venv", "node_modules", ".git"}


def _retired_vision_hits(root: Path) -> list[str]:
    """扫出引用已退役识别路径的 Python 文件（拼接字面量，避免自身命中）。"""
    needles = ("utils" + ".vision", "utils" + " import vision")
    hits: list[str] = []
    for path in root.rglob("*.py"):
        if _SKIP_DIRS.intersection(path.parts):
            continue
        text = path.read_text(encoding="utf-8")
        if any(needle in text for needle in needles):
            hits.append(str(path.relative_to(root)))
    return hits


def test_retired_vision_package_is_gone():
    """已退役的 utils/vision 既不在工作区，也不被版本库跟踪。"""
    root = Path(__file__).resolve().parents[3]
    assert not (root / "utils" / "vision").exists()
    if shutil.which("git") is None:
        pytest.skip("git 不在 PATH，跳过版本库层断言")

    proc = subprocess.run(
        ["git", "ls-files", "--error-unmatch", "utils/vision"],
        cwd=root,
        capture_output=True,
        text=True,
    )
    assert proc.returncode != 0, f"utils/vision 仍被版本库跟踪：{proc.stdout.strip()}"


def test_no_source_references_retired_vision():
    """任何 Python 源码都不得引用已退役的识别路径。"""
    root = Path(__file__).resolve().parents[3]
    assert _retired_vision_hits(root) == []


def test_retired_vision_guard_catches_reintroduction(tmp_path):
    """守卫本身有效：模拟旧路径被重新 import 时必须命中。"""
    (tmp_path / "bad.py").write_text("from " + "utils" + ".vision import ocr\n", encoding="utf-8")
    assert _retired_vision_hits(tmp_path) == ["bad.py"]
