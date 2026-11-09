"""workflow 边界契约：workflow 只编排，不创建角色、不改工具集。

对应 `engines/agents/AGENTS.md` 红线「禁止在 workflow/ 创建角色、配置提示词或绑定工具」。
判定口径按 AST 找「直接调用」：

- 直接把工厂交给工作流（`AgentSOPWorkflow(build_executor, build_verifier)`）是允许的；
- 用 lambda 包一层再交出去（`lambda: IncompleteHandoverGuard(build_executor())`）也是允许的：
  建角色的时机由装配方持有的工厂决定，workflow 只是转交；
- 在函数体里自己 `build_case_writer()` 并接着挂工具，就是越界。
"""

from __future__ import annotations

import ast
import pathlib

import pytest

pytestmark = [pytest.mark.unit]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
WORKFLOW_DIR = REPO_ROOT / "engines" / "agents" / "workflow"

# 角色装配入口：workflow 里出现对它们的直接调用即为越界
BUILDER_NAMES = frozenset(
    {
        "build_case_writer",
        "build_case_verifier",
        "build_knowledge_chat",
        "build_executor",
        "build_verifier",
        "build_ui_executor",
        "build_ui_verifier",
    }
)


def _lambda_calls(tree: ast.Module) -> set[tuple[int, int]]:
    """收集 lambda 体内的调用位置，这些是「延迟执行的工厂」。"""
    spans: set[tuple[int, int]] = set()
    for node in ast.walk(tree):
        if not isinstance(node, ast.Lambda):
            continue
        for inner in ast.walk(node.body):
            if isinstance(inner, ast.Call):
                spans.add((inner.lineno, inner.col_offset))
    return spans


def _called_names(tree: ast.Module) -> list[tuple[int, str]]:
    """列出源码里直接调用到的函数名（排除 lambda 内的延迟调用）。"""
    deferred = _lambda_calls(tree)
    hits: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if (node.lineno, node.col_offset) in deferred:
            continue
        func = node.func
        name = ""
        if isinstance(func, ast.Name):
            name = func.id
        elif isinstance(func, ast.Attribute):
            name = func.attr
        if name in BUILDER_NAMES:
            hits.append((node.lineno, name))
    return hits


def test_workflow_does_not_build_roles() -> None:
    """workflow 下任何模块都不得在函数体里自己创建角色。"""
    files = sorted(WORKFLOW_DIR.glob("*.py"))
    assert len(files) >= 8, f"扫描量异常（{len(files)} 个文件），识别可能失效"

    violations: list[str] = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for lineno, name in _called_names(tree):
            violations.append(f"{path.relative_to(REPO_ROOT)}:{lineno} 调用了 {name}")

    assert violations == [], "workflow 只能编排，角色装配请放到 case_roles / 调用方：\n" + "\n".join(
        violations
    )


def test_workflow_does_not_build_roles() -> None:
    """workflow 下任何模块都不得自己创建角色。"""
    files = sorted(WORKFLOW_DIR.glob("*.py"))
    assert len(files) >= 8, f"扫描量异常（{len(files)} 个文件），识别可能失效"

    violations: list[str] = []
    for path in files:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for lineno, name in _called_names(tree):
            violations.append(f"{path.relative_to(REPO_ROOT)}:{lineno} 调用了 {name}")

    assert violations == [], "workflow 只能编排，角色装配请放到 case_roles / 调用方：\n" + "\n".join(
        violations
    )


def test_case_authoring_workflow_delegates_assembly() -> None:
    """用例编写流水线只经成对装配入口取角色。"""
    source = (WORKFLOW_DIR / "case_goal_workflow.py").read_text(encoding="utf-8")

    assert "build_case_authoring_roles" in source
    for name in ("build_case_writer", "build_case_verifier", "build_case_artifact_tools"):
        assert name not in source, f"case_goal_workflow 不应再直接使用 {name}"
