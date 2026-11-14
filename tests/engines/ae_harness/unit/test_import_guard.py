"""ae_harness 观测层守护：不引入后端依赖、不反向依赖创建层。

只读源码做导入扫描（契约对拍），不导入被测模块、不联网。
扫描规则与「采集层零依赖」一致：
- 不得导入 django / backend（观测层不进后端）；
- 不得导入创建层（身份由调用方传入，观测层不回头读配置）。
"""

from __future__ import annotations

import ast

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

EVENT_DIR = Path(__file__).resolve().parents[4] / "engines" / "ae_harness" / "event"
MIDDLEWARE_DIR = Path(__file__).resolve().parents[4] / "engines" / "ae_harness" / "middleware"

# 禁止出现在观测层里的绝对导入前缀。
FORBIDDEN_PREFIXES = ("django", "backend", "engines.agents", "engines.ae_harness.agents")
# 观测层的最小规模：识别规则退化时计数骤降，测试随即失败，而不是给出虚假的「全部干净」。
MIN_FILES = 3


def _imports_from_source(source: str) -> list[str]:
    """取出源码里的绝对导入模块名（相对导入记为 `.目标`）。

    Args:
        source: 一段 Python 源码。

    Returns:
        导入的模块名列表；相对导入以点开头。
    """
    tree = ast.parse(source)
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * (node.level or 0)
            names.append(f"{prefix}{node.module or ''}")
    return names


def _violations(names: list[str]) -> list[str]:
    """挑出命中禁止前缀的导入名。

    Args:
        names: 模块名列表。

    Returns:
        违规的导入名；没有则为空列表。
    """
    hits: list[str] = []
    for name in names:
        if name in {".agents", "..agents"}:
            hits.append(name)
            continue
        if any(name == prefix or name.startswith(f"{prefix}.") for prefix in FORBIDDEN_PREFIXES):
            hits.append(name)
    return hits


def test_scanner_detects_violation():
    """自检：扫描器对合成违规源码必须报出，否则守护形同虚设。"""
    source = "import django\nfrom engines.ae_harness.agents.config import load_models\nfrom .usage import TokenUsage\n"
    hits = _violations(_imports_from_source(source))
    assert "django" in hits
    assert "engines.ae_harness.agents.config" in hits
    assert ".usage" not in hits


def test_event_layer_has_no_backend_or_creator_imports():
    """观测层不导入 django / backend / 创建层。"""
    files = sorted(EVENT_DIR.glob("*.py"))
    assert len(files) >= MIN_FILES, f"观测层文件数异常偏少：{len(files)}"

    offenders: list[str] = []
    for path in files:
        hits = _violations(_imports_from_source(path.read_text(encoding="utf-8")))
        offenders.extend(f"{path.name}: {name}" for name in hits)
    assert not offenders, "观测层出现禁止导入：" + ", ".join(offenders)


def test_usage_module_depends_on_stdlib_only():
    """用量形状模块只依赖标准库，可被任意消费方单独导入。"""
    source = (EVENT_DIR / "usage.py").read_text(encoding="utf-8")
    names = _imports_from_source(source)
    external = [name for name in names if not name.startswith(".")]
    assert set(external) <= {"__future__", "dataclasses", "typing"}


def test_middleware_layer_imports_no_package_module():
    """观测层零同包依赖：不 import 任何 engines.ae_harness.*，也不碰后端。"""
    files = sorted(MIDDLEWARE_DIR.glob("*.py"))
    assert len(files) >= 2, f"观测层文件数异常偏少：{len(files)}"

    offenders: list[str] = []
    for path in files:
        names = _imports_from_source(path.read_text(encoding="utf-8"))
        offenders.extend(
            f"{path.name}: {name}"
            for name in names
            if name.startswith("engines.ae_harness")
            or name.startswith("django")
            or name.startswith("backend")
        )
    assert not offenders, "观测层出现禁止导入：" + ", ".join(offenders)


def test_observer_allowed_external_imports():
    """观测实现只允许框架与标准库；识别规则退化时集合断言会立刻失败。"""
    source = (MIDDLEWARE_DIR / "observer.py").read_text(encoding="utf-8")
    roots = {
        name.split(".", 1)[0] for name in _imports_from_source(source) if not name.startswith(".")
    }
    assert roots <= {
        "__future__",
        "agentscope",
        "asyncio",
        "collections",
        "dataclasses",
        "datetime",
        "time",
        "typing",
    }
