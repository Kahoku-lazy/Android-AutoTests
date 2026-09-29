"""点击证据的配对与切片 —— 任务步骤链路与模型调试台共用的唯一真相源。

工具侧只在**真正调设备之前**打点（只读工具不打），并把北京时间毫秒的 `action_time`
写进返回 JSON；截图工具返回 `screenshot_path`。本模块把「工具结果行」变成证据：

- `extract_action_time`：从一段工具结果文本里取动作发出时刻（JSON 优先，正则兜底，
  兼容被展示层截断过的文本）。
- `build_executor_log_check`：按行序把有点击的行记成点击，并为每次点击配对**其后第一张**
  截图（已配对的不重复分配）；切片口径由调用方给出（任务链路传本步新增返回数，
  调试台传 0 —— 一轮对话就是一轮）。

两处必须完全一致：否则调试台看到的证据会与任务里看到的不一样。
"""

from __future__ import annotations

import json
import re

from typing import Any

ACTION_TIME_PATTERN = re.compile(r'"action_time"\s*:\s*"([^"]+)"')

__all__ = ["ACTION_TIME_PATTERN", "build_executor_log_check", "extract_action_time"]


def extract_action_time(text: str) -> str:
    """从一段工具结果文本里取动作发出时刻（JSON 优先，取不到再正则兜底）。"""
    if not text or "action_time" not in text:
        return ""
    try:
        data = json.loads(text)
    except (TypeError, ValueError):
        data = None
    if isinstance(data, dict) and data.get("action_time"):
        return str(data["action_time"])
    found = ACTION_TIME_PATTERN.search(text)
    return found.group(1) if found else ""


def _rows(result: Any, skip_results: int) -> list[dict]:
    """工具结果行（跳过 `skip_results` 条上下文里遗留的返回）。"""
    if result is None:
        return []
    return [
        item
        for item in (getattr(result, "tool_usage", None) or [])
        if isinstance(item, dict) and item.get("type") == "result"
    ][max(0, skip_results) :]


def build_executor_log_check(
    result: Any,
    skip_results: int = 0,
    log_evidence: dict | None = None,
    need_log: bool = False,
) -> dict:
    """执行侧点击证据：点击前时间点 + 点击后截图路径（+ 需日志时的 5 秒窗口证据）。

    每条点击配对其后**第一张**截图；已配对的截图不再分配给后续点击（一张截图不能同时证明
    两次点击），其后没有截图则留空串。`need_log` 为假时 `log` 恒为 None。

    Args:
        result: 角色结果（读 `tool_usage`）；None 表示没有结果。
        skip_results: 跳过上下文里前 N 条结果行（任务链路跳过上一步遗留的返回）。
        log_evidence: 已经取好的日志证据块（可空）。
        need_log: 本次是否附带日志证据。

    Returns:
        {"clicks": [{"action_time": str, "screenshot_path": str}], "log": dict | None}
    """
    clicks: list[dict] = []
    pending: list[dict] = []
    for item in _rows(result, skip_results):
        raw = item.get("output")
        text = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False, default=str)
        stamp = extract_action_time(text)
        if stamp:
            click = {"action_time": stamp, "screenshot_path": ""}
            clicks.append(click)
            pending.append(click)
        shot = str(item.get("screenshot_path") or "").replace("\\", "/").strip()
        if shot and pending:
            pending.pop(0)["screenshot_path"] = shot
    return {"clicks": clicks, "log": (log_evidence or None) if need_log else None}
