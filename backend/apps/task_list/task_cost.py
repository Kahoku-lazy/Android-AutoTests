from __future__ import annotations


def task_cost(task) -> float:
    return float(getattr(task, "cost_total", 0) or 0)
