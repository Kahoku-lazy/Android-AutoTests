"""任务费用读取（元）。本模块只读，不重算。

唯一计算口径在引擎侧：`engines/agents/messaging/billing.py::DeepSeekBilling`
（8 位小数、按每次模型调用时刻、含中国法定节假日）。结果经事件入库汇总到
`task_tasks.cost_total`：`fold.py` 算价 → `TaskEventSink` 写事件 →
`api.rollup_task_cost` 回写任务。

业务侧（任务列表 / 任务详情 / 任务报告 / 仪表盘）统一读这一列，避免"再算一遍"
导致同一任务在不同页面出现两个数。
"""

from __future__ import annotations


def task_cost(task) -> float:
    """任务费用（元）：直接取 `task.cost_total`，不做任何重算。

    Args:
        task: 任务对象或其替身。`cost_total` 缺失时按 0 处理。

    Returns:
        费用（元）。精度由数据库列决定（`DecimalField(max_digits=14, decimal_places=8)`）。
    """
    return float(getattr(task, "cost_total", 0) or 0)
