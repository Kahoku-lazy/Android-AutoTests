"""任务费用口径：只读 `task.cost_total`，不自带价目表重算。

唯一计算口径在引擎侧 `engines/agents/messaging/billing.py`（见
`tests/engines/agents/test_billing_eight_decimals.py`）。本文件守的是另一侧：
业务模块不得再引入第二份价目表，否则任务列表/详情会与仪表盘、任务报告对不上。
"""

from pathlib import Path
from types import SimpleNamespace

import pytest

from backend.apps.task_list.task_cost import task_cost

REPO_ROOT = Path(__file__).resolve().parents[3]
TASK_LIST_DIR = REPO_ROOT / "backend" / "apps" / "task_list"


@pytest.mark.unit
def test_task_cost_reads_cost_total_verbatim():
    """费用原样取 cost_total：8 位精度不被二次四舍五入。"""
    assert task_cost(SimpleNamespace(cost_total=0.01234567)) == pytest.approx(0.01234567)


@pytest.mark.unit
def test_task_cost_defaults_to_zero():
    """缺列或空值时给 0，不抛异常。"""
    assert task_cost(SimpleNamespace()) == 0.0
    assert task_cost(SimpleNamespace(cost_total=None)) == 0.0


@pytest.mark.unit
def test_task_cost_never_recomputes_from_tokens():
    """只有 token、没有 cost_total 时必须是 0 —— 这是「不再重算」的判定线。"""
    task = SimpleNamespace(input_tokens=100_000, output_tokens=5_000, cache_input_tokens=1_000)
    assert task_cost(task) == 0.0


@pytest.mark.unit
def test_task_list_keeps_no_second_price_table():
    """task_list 下不得出现 DeepSeek 价目表字面量（唯一口径在引擎侧）。"""
    offenders = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in sorted(TASK_LIST_DIR.rglob("*.py"))
        if "deepseek-flash" in path.read_text(encoding="utf-8")
    ]
    assert offenders == []
