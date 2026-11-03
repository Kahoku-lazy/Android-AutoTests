"""门面守卫：模型实例只经 `engines.agents.models` 包入口获取。

扫描 `engines/**`（跳过 models 包自身）的源码，禁止两件事：
1. `from engines.agents.models.<子模块> import ...` / `import engines.agents.models.<子模块>`；
2. 直接构造 agentscope 的聊天 / 实时 / 嵌入 / 语音合成模型类。

另加两条数据边界：models 包内不得出现 `.yaml` 数据文件；包入口必须导出约定函数。
本测试只读源码，不导入被测模块、不联网。
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

REPO_ROOT = Path(__file__).resolve().parents[3]
ENGINES_DIR = REPO_ROOT / "engines"
MODELS_DIR = ENGINES_DIR / "agents" / "models"

# 这些类只允许在 models 包内构造
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

EXPECTED_FACADE = frozenset(
    {
        "DeepSeekModelConfig",
        "get_chat_model",
        "get_embedding",
        "get_embedding_model",
        "get_fallback_chat_model",
        "get_realtime",
        "get_realtime_model",
        "get_text",
        "get_tts_model",
        "model_supports_image",
    }
)


def _iter_engine_sources():
    """列出 engines 下除 models 包以外的 Python 文件。"""
    for path in sorted(ENGINES_DIR.rglob("*.py")):
        if MODELS_DIR in path.parents:
            continue
        yield path


def _parse(path: Path) -> ast.Module:
    """解析一个 Python 文件。"""
    return ast.parse(path.read_text(encoding="utf-8"), filename=str(path))


def _submodule_imports(tree: ast.Module) -> list[str]:
    """找出对 models 子模块的导入（应为空）。"""
    hits: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            if node.module.startswith("engines.agents.models."):
                hits.append(node.module)
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name.startswith("engines.agents.models."):
                    hits.append(alias.name)
    return hits


def _model_constructions(tree: ast.Module) -> list[str]:
    """找出直接构造 agentscope 模型类的调用（应为空）。"""
    hits: list[str] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        if isinstance(func, ast.Name) and func.id in AGENTSCOPE_MODEL_CLASSES:
            hits.append(func.id)
        elif isinstance(func, ast.Attribute) and func.attr in AGENTSCOPE_MODEL_CLASSES:
            hits.append(func.attr)
    return hits


def test_no_module_imports_models_submodules() -> None:
    """包外模块只能 import 包入口，不能 import 子模块。"""
    violations = []
    scanned = 0
    for path in _iter_engine_sources():
        scanned += 1
        for module in _submodule_imports(_parse(path)):
            violations.append(f"{path.relative_to(REPO_ROOT)}: {module}")

    assert scanned > 60, f"扫描量异常（{scanned} 个文件），import 识别可能失效"
    assert violations == [], "禁止 import models 子模块，请改用包入口：\n" + "\n".join(violations)


def test_no_model_construction_outside_models() -> None:
    """模型实例只能在 models 包内构造。"""
    violations = []
    for path in _iter_engine_sources():
        for name in _model_constructions(_parse(path)):
            violations.append(f"{path.relative_to(REPO_ROOT)}: {name}")

    assert violations == [], "禁止在 models 包外直接构造模型类：\n" + "\n".join(violations)


def test_models_package_holds_no_yaml_data() -> None:
    """模型数据归 config/data，models 包内不得有 yaml。"""
    yaml_files = [path.name for path in MODELS_DIR.rglob("*.yaml")]

    assert yaml_files == [], f"models 包内不允许数据文件：{yaml_files}"


def test_facade_exports_expected_surface() -> None:
    """包入口必须导出约定的取模型函数。"""
    tree = _parse(MODELS_DIR / "__init__.py")
    exported: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(
            isinstance(target, ast.Name) and target.id == "__all__" for target in node.targets
        ):
            exported = {element.value for element in node.value.elts}  # type: ignore[attr-defined]

    assert EXPECTED_FACADE <= exported, f"门面缺少：{sorted(EXPECTED_FACADE - exported)}"
