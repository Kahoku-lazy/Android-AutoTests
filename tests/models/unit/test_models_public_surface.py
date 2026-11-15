"""门面守卫：模型实例只在 models 包内构造，包外不 import 其子模块。

扫描 `engines/**` 与 `backend/**`（跳过 models 自身）的源码，禁止两件事：
1. import `engines.agents.models` 的子模块；
2. 直接构造 agentscope 的聊天 / 实时 / 嵌入 / 语音合成模型类。

另加一条数据边界：models 包内不得出现 `.yaml` 数据文件。
本测试只读源码，不导入被测模块、不联网。
"""

from __future__ import annotations

import ast

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[3]
SCAN_DIRS = (REPO_ROOT / "engines", REPO_ROOT / "backend")
MODELS_DIR = REPO_ROOT / "engines" / "agents" / "models"

AGENTSCOPE_MODEL_CLASSES = frozenset(
    {
        "OpenAIChatModel",
        "DeepSeekChatModel",
        "DashScopeChatModel",
        "DashScopeRealtimeModel",
        "DashScopeEmbeddingModel",
        "DashScopeTTSModel",
    }
)


def _iter_sources():
    """列出 engines 与 backend 下、除 models 以外的 Python 文件。"""
    for root in SCAN_DIRS:
        for path in sorted(root.rglob("*.py")):
            if MODELS_DIR in path.parents or "__pycache__" in path.parts:
                continue
            yield path


def _parse(path: Path) -> ast.Module:
    """解析一个 Python 文件。"""
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _forbidden_imports(tree: ast.Module) -> list[str]:
    """找出 models 子模块导入。包入口导入是允许的。"""
    hits: list[str] = []
    for node in ast.walk(tree):
        module = ""
        if isinstance(node, ast.ImportFrom) and node.module:
            module = node.module
        elif isinstance(node, ast.Import):
            module = " ".join(alias.name for alias in node.names)
        if module.startswith("engines.agents.models."):
            hits.append(module)
    return hits


def _model_constructions(tree: ast.Module) -> list[str]:
    """找出直接构造 agentscope 模型类的调用。"""
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
        if name in AGENTSCOPE_MODEL_CLASSES:
            hits.append(name)
    return hits


def test_no_legacy_or_submodule_imports() -> None:
    """生产代码不 import models 子模块。"""
    violations = []
    scanned = 0
    for path in _iter_sources():
        scanned += 1
        for module in _forbidden_imports(_parse(path)):
            violations.append(f"{path.relative_to(REPO_ROOT)}: {module}")

    assert scanned > 60, f"扫描量异常（{scanned} 个文件），import 识别可能失效"
    assert violations == [], "禁止 import models 子模块，请改用包入口：\n" + "\n".join(violations)


def test_no_model_construction_outside_models() -> None:
    """模型实例只能在 models 包内构造。"""
    violations = []
    for path in _iter_sources():
        for name in _model_constructions(_parse(path)):
            violations.append(f"{path.relative_to(REPO_ROOT)}: {name}")

    assert violations == [], "禁止在 models 包外直接构造模型类：\n" + "\n".join(violations)


def test_models_holds_no_yaml_data() -> None:
    """模型数据归 config，models 包内不得有 yaml。"""
    yaml_files = [path.name for path in MODELS_DIR.rglob("*.yaml")]

    assert yaml_files == [], f"models 包内不允许数据文件：{yaml_files}"
