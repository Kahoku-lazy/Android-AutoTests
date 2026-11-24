"""平台侧导入守卫：只依赖 ae_harness 原语与标准库，不碰控制台入口与后端。

只读源码做导入扫描（契约对拍），不导入被测模块、不联网。
"""

from __future__ import annotations

import ast

from pathlib import Path

import pytest

pytestmark = [pytest.mark.unit]

BRIDGE_DIR = Path(__file__).resolve().parents[4] / "engines" / "backend_bridge"

# 平台层绝对禁止的导入前缀：AgentScope 框架、控制台入口、后端与 Django。
# 框架类型一律经 ae_harness 的函数取得。
FORBIDDEN_PREFIXES = (
    "agentscope",
    "engines.ae_harness.assistant",
    "engines.ae_harness.workflow.sop_runner",
    "django",
    "apps",
    "backend",
)
# 允许的外部根：标准库 + 框架 + ae_harness 原语 + 共享基础设施（日志等）。
ALLOWED_ROOTS = {
    "__future__",
    "asyncio",
    "chinese_calendar",  # 模型费用按法定节假日判高峰（model_billing）
    "collections",  # 目标循环的可替换执行签名（goal_case）
    "dataclasses",
    "datetime",
    "decimal",  # 费用用 Decimal 保 8 位小数（model_billing）
    "engines",
    "json",  # 模型名单查询与结果校验（discover / fake_world / team_breakdown）
    "pathlib",
    "time",
    "typing",
    "urllib",  # 标准库发模型名单查询，不引第三方 HTTP 客户端（discover）
    "utils",
    "zoneinfo",  # 北京时间换算（model_billing）
}
MIN_FILES = 5


def _imports(path: Path) -> list[str]:
    """取出源码里的绝对导入模块名（相对导入以点开头）。"""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    names: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            prefix = "." * (node.level or 0)
            names.append(f"{prefix}{node.module or ''}")
    return names


def test_forbidden_imports_absent():
    """不得引用控制台入口、SOP 编排与后端。"""
    files = sorted(BRIDGE_DIR.rglob("*.py"))
    assert len(files) >= MIN_FILES, f"平台层文件数异常偏少：{len(files)}"

    offenders: list[str] = []
    for path in files:
        for name in _imports(path):
            if any(name == p or name.startswith(f"{p}.") for p in FORBIDDEN_PREFIXES):
                offenders.append(f"{path.name}: {name}")
    assert not offenders, "平台层出现禁止导入：" + ", ".join(offenders)


def test_allowed_external_roots_only():
    """外部依赖只允许标准库、框架与 engines 内的原语。"""
    files = sorted(BRIDGE_DIR.rglob("*.py"))
    offenders: list[str] = []
    for path in files:
        roots = {name.split(".", 1)[0] for name in _imports(path) if not name.startswith(".")}
        offenders.extend(f"{path.name}: {root}" for root in roots if root not in ALLOWED_ROOTS)
    assert not offenders, "平台层出现未登记依赖：" + ", ".join(offenders)


def test_only_ae_harness_primitives_used():
    """engines 内依赖只允许 ae_harness 的原语子包（agents/tools/event/middleware/workflow）。"""
    allowed = (
        "engines.ae_harness.agents",
        "engines.ae_harness.tools",
        "engines.ae_harness.event",
        "engines.ae_harness.middleware",
        "engines.ae_harness.workflow.sop",
        "engines.ae_harness.workflow.goal",
        "engines.ae_harness.workflow.team",
        "engines.backend_bridge",
    )
    offenders: list[str] = []
    for path in sorted(BRIDGE_DIR.rglob("*.py")):
        for name in _imports(path):
            if not name.startswith("engines."):
                continue
            if not any(name == prefix or name.startswith(f"{prefix}.") for prefix in allowed):
                offenders.append(f"{path.name}: {name}")
    assert not offenders, "平台层引用了未登记的原语：" + ", ".join(offenders)
