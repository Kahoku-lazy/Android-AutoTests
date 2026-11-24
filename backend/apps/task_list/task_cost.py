"""
模块功能：➡️ 任务费用读取（元）。本模块只读，不重算 🏁
Python 调试：➡️ python -m backend.apps.task_list.task_cost 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 task_list 的功能用例间接覆盖，未直接 import 本模块）
🏁
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
