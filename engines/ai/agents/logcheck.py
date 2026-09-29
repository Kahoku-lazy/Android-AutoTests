"""点击证据的配对与切片 + 日志证据文本渲染 —— 任务链路与模型调试台共用的唯一真相源。

工具侧只在**真正调设备之前**打点（只读工具不打），并把北京时间毫秒的 `action_time`
写进返回 JSON；截图工具返回 `screenshot_path`。本模块把「工具结果行」变成证据：

- `extract_action_time`：从一段工具结果文本里取动作发出时刻（JSON 优先，正则兜底，
  兼容被展示层截断过的文本）。
- `build_executor_log_check`：按行序把有点击的行记成点击，并为每次点击配对**其后第一张**
  截图（已配对的不重复分配）；切片口径由调用方给出（任务链路传本步新增返回数，
  调试台传 0 —— 一轮对话就是一轮）。
- `render_log_evidence`：把日志证据块渲染成给验收模型看的文本（等级标签的口径也在这里）。

两处必须完全一致：否则调试台看到的证据会与任务里看到的不一样。
"""

from __future__ import annotations

import json
import re

from typing import Any

ACTION_TIME_PATTERN = re.compile(r'"action_time"\s*:\s*"([^"]+)"')

# 日志证据等级（与 engines.device.logbus 的常量口径一致，此处只做展示）
GRADE_LABEL = {
    "strong": "强证据",
    "periodic": "疑似周期",
    "before_action": "动作前",
    "out_of_window": "超窗",
}

__all__ = [
    "ACTION_TIME_PATTERN",
    "GRADE_LABEL",
    "CHECK_TOOL_NAME",
    "build_executor_log_check",
    "checked_log_keywords",
    "detected_log_timestamp",
    "extract_action_time",
    "render_log_evidence",
]

# 验收侧的「按关键词规则检查日志」工具名：平台据它的调用来填 logAssertionInfo
CHECK_TOOL_NAME = "check_device_log"


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


def _tool_rows(result: Any, kind: str, name: str) -> list[dict]:
    """本轮工具轨迹里指定类型与工具名的行。"""
    return [
        item
        for item in (getattr(result, "tool_usage", None) or [])
        if isinstance(item, dict) and item.get("type") == kind and item.get("name") == name
    ]


def checked_log_keywords(result: Any) -> list[str]:
    """本轮验收里模型让日志检查工具查过的关键词（按调用顺序去重）。

    平台据此自动填 `logAssertionInfo`：模型自己写的那份可能漏写或写错，
    以实际工具调用为准。
    """
    keywords: list[str] = []
    for item in _tool_rows(result, "call", CHECK_TOOL_NAME):
        payload = item.get("input")
        if not isinstance(payload, dict):
            continue
        keyword = str(payload.get("keyword") or "").strip()
        if keyword and keyword not in keywords:
            keywords.append(keyword)
    return keywords


def detected_log_timestamp(result: Any) -> str:
    """本轮检查工具**确实检测到**时最早的命中时间戳（没有检测到返回空串）。

    只读工具返回的 JSON（`detected` / `timestamps`），不猜、不从模型正文里抄。
    """
    stamps: list[str] = []
    for item in _tool_rows(result, "result", CHECK_TOOL_NAME):
        raw = item.get("output")
        text = raw if isinstance(raw, str) else json.dumps(raw, ensure_ascii=False, default=str)
        try:
            data = json.loads(text)
        except (TypeError, ValueError):
            continue
        if not isinstance(data, dict) or not data.get("detected"):
            continue
        stamps.extend(str(stamp) for stamp in (data.get("timestamps") or []) if stamp)
    return min(stamps) if stamps else ""


def render_log_evidence(evidence: dict | None, action_time: str = "") -> str:
    """把日志证据块渲染成给验收模型看的文本（无证据时明确标注，便于降级判定）。

    任务链路（每步的验收输入）与模型调试台（验收对话的输入）共用这一份渲染：
    口径一旦分叉，同一份证据在两处就会读出不同的结论。
    """
    if not evidence:
        return "日志证据：无（本次未采集到设备日志证据，请只依据截图判断）。"
    source = str(evidence.get("channel") or "").strip()
    origin = f"来源 {source}，" if source and source != "*" else ""
    stamps = [str(item) for item in (evidence.get("action_times") or []) if item]
    if not stamps and evidence.get("action_time"):
        stamps = [str(evidence["action_time"])]
    action_text = "、".join(stamps) if stamps else (action_time or "-")
    lines: list[str] = [
        "设备日志证据（北京时间，基准=本步动作发出时刻，取证阈值 "
        f"{evidence.get('threshold_seconds')}s，动作前基线 {evidence.get('baseline_seconds')}s）：",
        f"- {origin}本步动作发出时间（{len(stamps)} 次）：{action_text}",
        f"- 窗口内日志行数：{evidence.get('window_line_count')}，结论：{evidence.get('conclusion')}",
    ]
    hits = evidence.get("hits") or []
    if hits:
        lines.append("- 窗口内命中：")
        for hit in hits:
            features = "、".join(
                f"#{item.get('id')} {item.get('module')}-{item.get('feature')}"
                for item in hit.get("features") or []
            )
            grade = GRADE_LABEL.get(str(hit.get("grade")), str(hit.get("grade")))
            hit_stamps = "、".join(hit.get("timestamps") or [])
            lines.append(
                f"  · [{grade}] 关键词 {hit.get('keyword')} → 功能点 {features}"
                f"（出现 {hit.get('count')} 次；{hit_stamps}）"
            )
            if hit.get("baseline_occurrences"):
                before = "、".join(
                    f"{item.get('timestamp')} {item.get('text')}"
                    for item in hit["baseline_occurrences"]
                )
                lines.append(f"    动作前已出现过同名日志：{before}")
    else:
        lines.append("- 窗口内无关键词命中。")
    if evidence.get("out_of_window"):
        out = "、".join(
            f"{item.get('keyword')}@{item.get('timestamp')}(+{item.get('delta_seconds')}s)"
            for item in evidence["out_of_window"]
        )
        lines.append(f"- 超出取证阈值、不作为本次证据：{out}")
    raw_lines = evidence.get("lines") or []
    if raw_lines:
        lines.append("- 窗口内原始日志：")
        lines.extend(f"  | {item.get('timestamp')} {item.get('text')}" for item in raw_lines)
    lines.append(
        "采信口径（从严）：疑似周期证据不得单独作为通过依据；只有截图证据同时成立才可判通过。"
    )
    return "\n".join(lines)
