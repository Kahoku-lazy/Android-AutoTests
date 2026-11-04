"""
文件名: ➡️ tool_device.py 🏁
路径: ➡️ engines/agents/tools/tool_device.py 🏁
模块功能：➡️ 引擎侧设备工具：工具函数本体与 `ToolSpec` 产出 🏁
Python 调试：➡️ python -m engines.agents.tools.tool_device 🏁
时间：➡️ 2026-10-20 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. click_ratio: 按已核对帧里的标记点点击；必须带 token，缺 token 直接报错不产生手势
2. tap_screen: 按已核对帧里的标记点点击或长按；同样必须带 token，可用 index 选第几个点
3. xpath_action: 按 xpath 或页面文案查元素；命中时把全部命中点画在一张图上（多点带序号）并签发 token
4. swipe_screen: 按方向滑动设备屏幕；只返回动作时间
5. drag_ratio: 按归一化坐标拖动（视觉模型看图后输出起终点相对位置，工具换算成屏幕像素坐标）；只返回动作时间
6. input_text: 向设备当前输入框输入文本（支持中文等非 ASCII 字符）；只返回动作时间
7. press_key: 按设备返回键（BACK）返回上一页；只返回动作时间
8. app_control: 启动或停止指定设备上的 App；返回启动/关闭时间点、包名与启停前后的前台应用
9. build_device_tools: 按固定顺序产出工具函数表
10. device_tool_specs: 按工具函数表产出 `ToolSpec` 列表
🏁
关联模块：➡️
1. engines.device.action: 导入 AppControl, Click, Drag, InputText, LongClick, PressKey 等
2. engines/agents/tools/tool_frame_cache.py: 核对帧里存多个标记点，点击按序号复用
3. engines/agents/tools/tool_img_b64.py: 命中多点时把全部点标在一张图上
4. utils.logs: 导入 agent_event_log, logging_now_stamp
🏁
测试：➡️
1. tests/engines/agents/test_tool_device.py: 单文件调试指令：python -m pytest tests/engines/agents/test_tool_device.py -vv -s --tb=sh
2. tests/engines/agents/test_tool_device_e2e.py: 单文件调试指令：python -m pytest tests/engines/agents/test_tool_device_e2e.py -vv -s --t
3. tests/engines/agents/test_xpath_action_coords.py: xpath_action 只返回文本与中心坐标，不点击
🏁
"""

from __future__ import annotations

import json
import re
import time
import unicodedata

from contextlib import contextmanager
from typing import Any, Callable

from engines.device.action import (
    AppControl,
    Click,
    Drag,
    InputText,
    LongClick,
    PressKey,
    Screenshot,
    Swipe,
    System,
    open_device,
)
from utils.logs import agent_event_log, logging_now_stamp

from . import tool_frame_cache as _frame_cache
from .tool_base import ToolSpec
from .tool_img_b64 import annotate_points

__all__ = [
    "app_control",
    "build_device_tools",
    "click_ratio",
    "device_tool_specs",
    "drag_ratio",
    "input_text",
    "press_key",
    "swipe_screen",
    "tap_screen",
    "xpath_action",
]

_READ_ONLY = frozenset({"screenshot_page", "xpath_action"})
# 取值白名单：非法值一律返回可读错误，不静默退回默认动作（点错、滑错方向的代价更大）
_TAP_MODES = ("click", "long_click")
_SWIPE_DIRECTIONS = ("up", "down", "left", "right")
# 一次最多试几个文案候选：一次 UI 树读取就能全部试完，成本封顶
_MAX_CANDIDATES = 3
# 取页面上所有带文案的节点，供归一化匹配使用
_TEXT_XPATH = "//*[@text]"
# 启停 App 后等前台切过来：monkey/force-stop 返回时窗口还没切（实测冷启动约 4s 才出现
# mCurrentFocus），最多等这么久；停止通常是第一次读到就已离开，不会真等。
_APP_SETTLE_TIMEOUT = 6.0
_APP_POLL_INTERVAL = 0.2
_TOOL_ORDER = (
    "screenshot_page",
    "click_ratio",
    "tap_screen",
    "xpath_action",
    "swipe_screen",
    "drag_ratio",
    "input_text",
    "press_key",
    "app_control",
)


def _error(message: str) -> str:
    return json.dumps({"error": message}, ensure_ascii=False)


@contextmanager
def _device(serial: str):
    """打开一台设备，离开时断开。连接失败原样抛出。"""
    connection, info, control = open_device(System.ANDROID, str(serial))
    try:
        yield info, control
    finally:
        connection.disconnect()


def _foreground_app(info: Any) -> dict:
    """读一次前台应用；取不到时 package / activity 均为空串。"""
    app = info.current_app() or {}
    return {
        "package": str(app.get("package") or ""),
        "activity": str(app.get("activity") or ""),
    }


def _wait_app(info: Any, target: str, mode: str) -> dict:
    """等前台切到 `target`（mode=enter）或离开 `target`（mode=leave）。

    启停 App 是异步的：`monkey` / `am force-stop` 返回后窗口还要几百毫秒才切过来，
    立刻读会读到最后一次重绘之前的旧前台，所以这里轮询到切好为止。

    Args:
        info: 设备信息查询对象。
        target: 目标包名。
        mode: enter 等它出现 / leave 等它消失。

    Returns:
        切换后的前台应用；超时返回最后一次读到的值。
    """
    deadline = time.monotonic() + _APP_SETTLE_TIMEOUT
    while True:
        current = _foreground_app(info)
        settled = current["package"] == target if mode == "enter" else current["package"] != target
        if settled or time.monotonic() >= deadline:
            return current
        time.sleep(_APP_POLL_INTERVAL)


def _execute(
    serial: str,
    body: Callable[[Any, Any], dict],
    *,
    side_effect: bool = False,
    watch_app: tuple[str, str] | None = None,
) -> str:
    """执行一次动作并返回 JSON。连接失败与动作失败分开返回。

    Args:
        serial: 设备序列号。
        body: 在设备会话里执行的动作，返回要回传给模型的字段。
        side_effect: 有副作用时补 `action_time`（工具调用起始时刻）。
        watch_app: 监控前台切换时传 `(目标包名, enter|leave)`；会额外补
            `before_app` / `after_app`。只有启停 App 需要。

    Returns:
        JSON 字符串；失败时是 {"error": 可读原因}。
    """
    payload, error = _run_device(serial, body, side_effect=side_effect, watch_app=watch_app)
    if error:
        return error
    return json.dumps(payload, ensure_ascii=False, default=str)


def _run_device(
    serial: str,
    body: Callable[[Any, Any], dict],
    *,
    side_effect: bool = False,
    watch_app: tuple[str, str] | None = None,
) -> tuple[dict, str]:
    """执行一次动作，把「成功字段」与「失败原因」分开返回，供需要回图的工具使用。

    Args:
        serial: 设备序列号。
        body: 在设备会话里执行的动作，返回要回传给模型的字段。
        side_effect: 有副作用时补 `action_time`（工具调用起始时刻）。
        watch_app: 监控前台切换时传 `(目标包名, enter|leave)`。

    Returns:
        (字段字典, 错误 JSON 串)；成功时错误为空串，失败时字段为空字典。
    """
    stamp = logging_now_stamp() if (side_effect or watch_app) else ""
    opened = False
    try:
        with _device(serial) as (info, control):
            opened = True
            before = _foreground_app(info) if watch_app else None
            payload = dict(body(info, control) or {})
            if side_effect or watch_app:
                payload["action_time"] = stamp
            if watch_app and before is not None:
                target, mode = watch_app
                payload["before_app"] = before
                payload["after_app"] = _wait_app(info, target, mode)
            return payload, ""
    except Exception as exc:  # noqa: BLE001 - 设备侧失败一律转可读结论
        if opened:
            agent_event_log.warning(f"设备动作执行失败：{exc}")
            return {}, _error(f"动作执行失败：{exc}")
        agent_event_log.warning(f"打开设备失败：{exc}")
        return {}, _error(f"连接设备失败：{exc}")


def _gesture(
    serial: str,
    body: Callable[[Any], dict],
    *,
    shot_after: bool,
) -> dict | str:
    """执行一次手势；需要时把点击后的页面图与动作时间一起回给模型。

    Args:
        serial: 设备序列号。
        body: 拿到设备控制对象后执行手势，返回要回传给模型的字段。
        shot_after: 是否在动作后截一张当前页面图。

    Returns:
        带图时为 {"image": {...}, "summary": {...}}；不出图时是 JSON 字符串；
        失败时是 {"error": 可读原因} 的 JSON 字符串。
    """

    def run(_info: Any, control: Any) -> dict:
        payload = dict(body(control) or {})
        if shot_after:
            shot = Screenshot(control).capture()
            payload["image"] = {
                "base64": shot["image_base64"],
                "media_type": shot["media_type"],
            }
        return payload

    payload, error = _run_device(serial, run, side_effect=True)
    if error:
        return error
    if not shot_after:
        return json.dumps(payload, ensure_ascii=False, default=str)
    image = payload.pop("image")
    return {"image": image, "summary": payload}


def _frame_or_error(serial: str, token: str) -> tuple[_frame_cache.Frame | None, str]:
    """取核对帧；没给 token 或 token 失效时返回错误串（点击类工具的硬门槛）。

    Args:
        serial: 设备序列号。
        token: 坐标核对（`mark_dot` 或 `xpath_action` 标记）签发的帧标识。

    Returns:
        (帧, 错误串)；成功时错误串为空，失败时帧为 None。
    """
    key = str(token or "").strip()
    if not key:
        return None, _error(
            "没有经过坐标核对确认的目标不能点击：先调用 xpath_action(texts=...) 或 "
            "mark_dot(...) 拿到 token，再带 token 点击"
        )
    frame = _frame_cache.get(serial, key)
    if frame is None:
        return None, _error("标记帧已过期或不属于该设备，请重新核对坐标后再点击")
    return frame, ""


def _frame_point(serial: str, token: str, index: int) -> tuple[tuple[int, int] | None, str]:
    """按帧标识与序号取要点击的像素点。

    Args:
        serial: 设备序列号。
        token: 核对帧标识。
        index: 帧内序号，从 1 起；单点帧可省略。

    Returns:
        (像素点, 错误串)；失败时点为 None。
    """
    frame, error = _frame_or_error(serial, token)
    if frame is None:
        return None, error
    number = int(index or 1)
    if number < 1 or number > len(frame.points):
        return None, _error(f"该帧没有第 {number} 个标记点；可选 1~{len(frame.points)}")
    return frame.points[number - 1], ""


def click_ratio(
    serial: str,
    nx: float,
    ny: float,
    token: str = "",
    index: int = 1,
    shot_after: bool = True,
) -> str | dict:
    """按帧内标记点点击（已核对过的坐标才允许点）。

    Args:
        serial: 设备序列号
        nx: 兼容保留：带 token 时不再参与定位
        ny: 兼容保留：带 token 时不再参与定位
        token: 核对帧标识；缺失时直接报错，不产生手势
        index: 帧内序号，从 1 起；多命中时用它挑要点的那个
        shot_after: 是否回传点击后的页面图，默认回传

    Returns:
        带图时为 {"image": {...}, "summary": {"x", "y", "action_time"}}；
        不出图或失败时是 JSON 字符串。
    """
    point, error = _frame_point(serial, token, index)
    if point is None:
        return error

    def body(control: Any) -> dict:
        return Click(control).by_coord(*point)

    return _gesture(serial, body, shot_after=shot_after)


def tap_screen(
    serial: str,
    mode: str = "click",
    x: int = 0,
    y: int = 0,
    token: str = "",
    index: int = 1,
    shot_after: bool = True,
) -> str | dict:
    """按帧内标记点点击或长按（已核对过的坐标才允许操作）。

    Args:
        serial: 设备序列号（由上游任务给出）
        mode: click 点击 / long_click 长按；其它值报错
        x: 兼容保留：带 token 时不再参与定位
        y: 兼容保留：带 token 时不再参与定位
        token: 核对帧标识；缺失时直接报错，不产生手势
        index: 帧内序号，从 1 起；多命中时用它挑要按的那个
        shot_after: 是否回传动作后的页面图，默认回传

    Returns:
        带图时为 {"image": {...}, "summary": {"x", "y", "action_time"}}；
        不出图或失败时是 JSON 字符串。
    """
    chosen = str(mode or "").strip()
    if chosen not in _TAP_MODES:
        return _error(f"不支持的点击模式: {chosen or '(空)'}；可用：click / long_click")
    point, error = _frame_point(serial, token, index)
    if point is None:
        return error
    px, py = point
    actions = {
        "long_click": lambda control: LongClick(control).by_coord(px, py),
        "click": lambda control: Click(control).by_coord(px, py),
    }
    return _gesture(serial, actions[chosen], shot_after=shot_after)


def _loose(text: str) -> str:
    """归一化文案：NFKC、去掉全部空白、忽略大小写，用于容忍 App 的空格写法。

    Args:
        text: 原始文案。

    Returns:
        归一化后的比较用字符串。
    """
    return "".join(unicodedata.normalize("NFKC", str(text or "")).split()).casefold()


def _split_candidates(texts: str) -> list[str]:
    """把逗号/顿号分隔的文案候选拆开，最多保留 3 个。

    Args:
        texts: 逗号或顿号分隔的文案。

    Returns:
        去空后的候选列表。
    """
    items = [item.strip() for item in re.split(r"[,，、;；]", str(texts or "")) if item.strip()]
    return items[:_MAX_CANDIDATES]


def _quoted_text(xpath: str) -> str:
    """从 `@text='xxx'` / `@text="xxx"` 里取出文案，供归一化兜底匹配。

    Args:
        xpath: xpath 表达式。

    Returns:
        取到的文案；没有则返回空串。
    """
    matched = re.search(r"@text\s*=\s*'([^']*)'", xpath) or re.search(
        r'@text\s*=\s*"([^"]*)"', xpath
    )
    return matched.group(1) if matched else ""


def _unique_hits(found: list[dict] | None) -> list[dict]:
    """去重并按「先纵坐标、再横坐标」升序排列命中点。

    Args:
        found: 设备返回的元素列表。

    Returns:
        [{"text", "x", "y"}]，顺序即图上序号顺序。
    """
    seen: set[tuple[str, int, int]] = set()
    hits: list[dict] = []
    for item in found or []:
        hit = {
            "text": str(item.get("text") or ""),
            "x": int(item.get("x") or 0),
            "y": int(item.get("y") or 0),
        }
        key = (hit["text"], hit["x"], hit["y"])
        if key in seen:
            continue
        seen.add(key)
        hits.append(hit)
    return sorted(hits, key=lambda hit: (hit["y"], hit["x"]))


def _numbered(hits: list[dict]) -> list[dict]:
    """给命中点补上从 1 起的序号。

    Args:
        hits: 已排序的命中点。

    Returns:
        [{"index", "text", "x", "y"}]。
    """
    return [{"index": index, **hit} for index, hit in enumerate(hits, start=1)]


def xpath_action(serial: str, xpath: str = "", texts: str = "", confirm: bool = True) -> str | dict:
    """按 xpath 或页面文案查元素；命中时把命中点标在同一张图上并签发帧标识。

    Args:
        serial: 设备序列号（由上游任务给出）
        xpath: xpath 表达式（如 //android.widget.TextView[@text='H6110']）；给了 texts 时可省略
        texts: 页面上要匹配的文案，逗号或顿号分隔，最多 3 个；先精确匹配，再按去空白/全角归一化匹配
        confirm: 是否截图标出全部命中点并签发 token，默认开启；关掉时只回坐标

    Returns:
        命中且 confirm 时为 {"image": …, "summary": {"count", "items", "candidates", "token"}}；
        未命中、未开启 confirm 或出错时是 JSON 字符串。
    """
    candidates = _split_candidates(texts)
    pattern = str(xpath or "").strip()
    if not candidates and not pattern:
        return _error("请给出 xpath 或 texts 之一")

    def body(_info: Any, control: Any) -> dict:
        if candidates:
            nodes = control.find_xpath(_TEXT_XPATH) or []
            counts: dict[str, int] = {}
            hits: list[dict] = []
            for candidate in candidates:
                exact = [node for node in nodes if str(node.get("text") or "") == candidate]
                matched = exact or [
                    node for node in nodes if _loose(node.get("text")) == _loose(candidate)
                ]
                counts[candidate] = len(matched)
                hits.extend(matched)
            payload = {"candidates": counts, "hits": hits}
        else:
            found = control.find_xpath(pattern) or []
            quoted = _quoted_text(pattern)
            if not found and quoted:
                nodes = control.find_xpath(_TEXT_XPATH) or []
                found = [node for node in nodes if _loose(node.get("text")) == _loose(quoted)]
            payload = {"candidates": {pattern: len(found)}, "hits": found}
        if confirm and payload["hits"]:
            shot = Screenshot(control).capture()
            payload["shot"] = {
                "base64": shot["image_base64"],
                "media_type": shot["media_type"],
            }
        return payload

    payload, error = _run_device(serial, body)
    if error:
        return error

    hits = _unique_hits(payload["hits"])
    counts = payload.get("candidates") or {}
    if not hits:
        return json.dumps({"count": 0, "candidates": counts, "items": []}, ensure_ascii=False)
    shot = payload.get("shot")
    if not shot:
        return json.dumps(
            {"count": len(hits), "candidates": counts, "items": _numbered(hits)},
            ensure_ascii=False,
        )
    marked = annotate_points(shot["base64"], tuple((hit["x"], hit["y"]) for hit in hits))
    token = _frame_cache.put(
        serial,
        width=marked.width,
        height=marked.height,
        points=marked.points,
        image_b64=shot["base64"],
        media_type=marked.media_type,
    )
    return {
        "image": {"base64": marked.base64, "media_type": marked.media_type},
        "summary": {
            "count": len(hits),
            "candidates": counts,
            "items": _numbered(hits),
            "token": token,
        },
    }


def swipe_screen(serial: str, direction: str = "up", distance: int = 500) -> str:
    """按方向滑动设备屏幕；只返回动作时间。
    direction 只接受 up/down/left/right，其它值直接返回错误，不会退回 up。
    Args:
        serial: 设备序列号（由上游任务给出）
        direction: 滑动方向 up/down/left/right，默认 up；其它值报错
        distance: 滑动距离（像素），默认 500
    """
    chosen = str(direction or "").strip()
    if chosen not in _SWIPE_DIRECTIONS:
        return _error(f"不支持的滑动方向: {chosen or '(空)'}；可用：up / down / left / right")
    return _execute(
        serial,
        lambda info, control: Swipe(control).by_direction(chosen, int(distance or 500)),
        side_effect=True,
    )


def drag_ratio(serial: str, nx1: float, ny1: float, nx2: float, ny2: float) -> str:
    """按归一化坐标拖动（视觉模型看图后输出起终点相对位置，工具换算成屏幕像素坐标）；只返回动作时间。
    Args:
        serial: 设备序列号
        nx1: 起点横向相对位置 0~1（0=最左，1=最右）
        ny1: 起点纵向相对位置 0~1（0=最上，1=最下）
        nx2: 终点横向相对位置 0~1
        ny2: 终点纵向相对位置 0~1
    """
    return _execute(
        serial,
        lambda info, control: Drag(control).by_ratio(
            float(nx1), float(ny1), float(nx2), float(ny2)
        ),
        side_effect=True,
    )


def input_text(serial: str, text: str, clear_first: bool = True) -> str:
    """向设备当前输入框输入文本（支持中文等非 ASCII 字符）；只返回动作时间。
    Args:
        serial: 设备序列号（由上游任务给出）
        text: 要输入的文本
        clear_first: 输入前是否清空输入框，默认 True
    """
    return _execute(
        serial,
        lambda info, control: InputText(control).by_text(str(text or ""), bool(clear_first)),
        side_effect=True,
    )


def press_key(serial: str) -> str:
    """按设备返回键（BACK）返回上一页；只返回动作时间。
    Args:
        serial: 设备序列号（由上游任务给出）
    """
    return _execute(
        serial,
        lambda info, control: PressKey(control).back(),
        side_effect=True,
    )


def app_control(serial: str, action: str, package: str = "") -> str:
    """启动或停止指定设备上的 App；返回启动/关闭时间点、包名与启停前后的前台应用。
    action 只接受 start_app / stop_app，其它值报错；两个动作都必须给 package。
    Args:
        serial: 设备序列号（由上游任务给出）
        action: start_app 启动 / stop_app 停止
        package: 目标 App 包名
    """
    chosen = str(action or "").strip()
    if chosen not in ("start_app", "stop_app"):
        return _error(f"不支持的 App 动作: {chosen or '(空)'}；可用：start_app / stop_app")
    if not package:
        return _error(f"{chosen} 需要 package 参数")
    pkg = str(package)
    actions = {
        "stop_app": lambda info, control: AppControl(control).stop(pkg),
        "start_app": lambda info, control: AppControl(control).start(pkg),
    }
    # 启动等它进入前台、关闭等它离开前台，都在 _execute 里带上前后台快照
    mode = "enter" if chosen == "start_app" else "leave"
    return _execute(
        serial,
        actions[chosen],
        side_effect=True,
        watch_app=(pkg, mode),
    )


def build_device_tools() -> dict[str, Callable[..., Any]]:
    """按固定顺序产出工具函数表。"""

    def screenshot_page(serial: str) -> dict:
        """截取设备当前屏幕并返回无损图片（给视觉模型看图）。
        Args:
            serial: 设备序列号
        """
        opened = False
        try:
            with _device(serial) as (_info, control):
                opened = True
                shot = Screenshot(control).capture()
        except Exception as exc:  # noqa: BLE001 - 设备侧失败一律转可读结论
            if opened:
                agent_event_log.warning(f"截屏执行失败：{exc}")
            else:
                agent_event_log.warning(f"截屏连接失败：{exc}")
            return {"error": f"截屏失败：{exc}"}
        return {"image": {"base64": shot["image_base64"], "media_type": shot["media_type"]}}

    impls = {
        "click_ratio": click_ratio,
        "tap_screen": tap_screen,
        "xpath_action": xpath_action,
        "swipe_screen": swipe_screen,
        "drag_ratio": drag_ratio,
        "input_text": input_text,
        "press_key": press_key,
        "app_control": app_control,
        "screenshot_page": screenshot_page,
    }
    return {name: impls[name] for name in _TOOL_ORDER}


def device_tool_specs() -> list[ToolSpec]:
    """按工具函数表产出 `ToolSpec` 列表。"""
    return [
        ToolSpec(
            name=name,
            handler=func,
            read_only=name in _READ_ONLY,
            auto_allow=True,
        )
        for name, func in build_device_tools().items()
    ]
