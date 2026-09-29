"""平台工具 — 框架无关的纯函数 + 工具注册表（Django 层）。

工具 = 普通函数（类型注解 + docstring 自动推导 schema），只调各 App api.py。
框架包装（PlatformFunctionTool / build_toolkit）在 `engines.ai.agentscope.tool_wrapper`，
经 `TaskRequest.tools` 注入引擎；`user_id` 由包装层构造时注入。
"""

from __future__ import annotations

import inspect
import json
import logging
import re
import time

from contextlib import contextmanager
from datetime import datetime, timezone

logger = logging.getLogger("ai_assistant")

# ═══════════════════════════════════════════════════════════════════
# 结果序列化辅助
# ═══════════════════════════════════════════════════════════════════


def _model_to_dict(obj) -> dict:
    """Django model 实例 → 字段 dict（stringify，防懒加载 ORM）。"""
    data = {}
    for field in obj._meta.fields:
        val = getattr(obj, field.attname, "")
        data[field.name] = str(val) if val is not None else ""
    return data


def _jsonable(obj) -> str:
    """任意结果 → JSON 字符串（Django model 实例转字段 dict）。"""
    if hasattr(obj, "_meta"):  # Django model
        return json.dumps(_model_to_dict(obj), ensure_ascii=False, default=str)
    if isinstance(obj, (list, tuple)):
        items = [_model_to_dict(x) if hasattr(x, "_meta") else x for x in obj]
        return json.dumps(items, ensure_ascii=False, default=str)
    if isinstance(obj, (dict, str, int, float, bool)):
        return obj if isinstance(obj, str) else json.dumps(obj, ensure_ascii=False, default=str)
    return json.dumps(obj, ensure_ascii=False, default=str)


def _action_stamp() -> str:
    """动作发出时刻（北京时间毫秒）—— 在真正调设备之前取，供验收前筛选日志证据。"""
    from engines.device.logbus import now_stamp

    return now_stamp()


def _with_action_time(payload: str, action_time: str) -> str:
    """把动作发出时刻并进工具结果的 JSON（结果不是 JSON 对象时原样返回）。"""
    try:
        data = json.loads(payload)
    except (TypeError, ValueError):
        return payload
    if not isinstance(data, dict):
        return payload
    data["action_time"] = action_time
    return json.dumps(data, ensure_ascii=False, default=str)


@contextmanager
def _device_engine(serial: str):
    """打开目标设备引擎（短连接，退出即断开）；先校验设备可用并切为当前设备。"""
    from apps.device_pool.api import use_device
    from apps.device_pool.models import Device
    from engines.device.registry import close_engine, open_engine

    use_device(serial)
    dev = Device.objects.get(serial=serial)
    engine = open_engine(serial, dev.connection_addr or serial)
    try:
        yield engine
    finally:
        close_engine(engine)


# ═══════════════════════════════════════════════════════════════════
# 设备管理工具（获取设备信息 + 执行控制操作）
# ═══════════════════════════════════════════════════════════════════


def list_devices(user_id: str = "") -> str:
    """查询设备管理中的全部设备及状态，返回设备列表。每个设备的字段含义：
    id=记录主键、serial=序列号(唯一标识，选设备用)、name=设备名、model=型号、
    brand=品牌、screen=分辨率(宽x高)、
    status=状态(ONLINE=在线空闲可用、BUSY=使用中不可用)、
    connection_type=连接类型(USB/WIFI)、connection_addr=无线连接地址(USB 为空)、
    locked=是否锁定(仅 WIFI 可为 true)、locked_by=锁定者、locked_at=锁定时间、
    occupied_by=占用者(空=未占用)、occupied_at=占用时间、connected_at=首次连接时间、
    added_by=配置者、last_seen=最后在线时间、is_current=是否当前活动设备、
    remaining=BUSY 占用中的剩余秒数(否则 0)。
    挑选设备时只用 status=ONLINE 的设备，用它的 serial。"""
    from apps.device_pool.api import list_devices as _f

    return _jsonable(_f(user_id=user_id))


def acquire_device(serial: str, timeout: int = 300, user_id: str = "") -> str:
    """锁定一台在线设备用于独占测试。
    Args:
        serial: 设备序列号
        timeout: 锁定超时秒数，默认300
    """
    from apps.device_pool.api import acquire_device as _f

    return _jsonable(_f(serial, user_id=int(user_id), timeout=timeout))


def release_device(serial: str, reason: str = "manual", user_id: str = "") -> str:
    """释放已锁定的设备回设备池。
    Args:
        serial: 设备序列号
        reason: 释放原因
    """
    from apps.device_pool.api import release_device as _f

    return _jsonable(_f(serial, reason=reason))


def app_control(
    serial: str,
    action: str,
    package: str = "",
    user_id: str = "",
) -> str:
    """启动或停止指定设备上的 App；每次返回 package/activity 用于判断页面是否跳转。
    Args:
        serial: 设备序列号（先 list_devices 查询）
        action: start_app 启动 / stop_app 停止
        package: 目标 App 包名
    """
    action_time = _action_stamp()
    with _device_engine(serial) as engine:
        if action == "start_app":
            if not package:
                raise ValueError("start_app 需要 package 参数")
            engine.start_app(package)
        elif action == "stop_app":
            if not package:
                raise ValueError("stop_app 需要 package 参数")
            engine.stop_app(package)
        else:
            raise ValueError(f"不支持的 App 动作: {action}")
        return _with_action_time(_jsonable(engine.app_current()), action_time)


def tap_screen(
    serial: str,
    mode: str = "click",
    x: int = 0,
    y: int = 0,
    user_id: str = "",
) -> str:
    """按像素坐标点击或长按设备屏幕；每次返回 package/activity 用于判断页面是否跳转。
    Args:
        serial: 设备序列号（先 list_devices 查询）
        mode: click 点击 / long_click 长按
        x: 坐标 x（像素）
        y: 坐标 y（像素）
    """
    action_time = _action_stamp()
    with _device_engine(serial) as engine:
        if mode == "click":
            if not x or not y:
                raise ValueError("click 需要 x/y 坐标")
            engine.click(x, y)
        elif mode == "long_click":
            if not x or not y:
                raise ValueError("long_click 需要 x/y 坐标")
            engine.long_click(x, y)
        else:
            raise ValueError(f"不支持的点击方式: {mode}")
        return _with_action_time(_jsonable(engine.app_current()), action_time)


def swipe_screen(
    serial: str,
    direction: str = "up",
    distance: int = 500,
    user_id: str = "",
) -> str:
    """按方向滑动设备屏幕；每次返回 package/activity 用于判断页面是否跳转。
    Args:
        serial: 设备序列号（先 list_devices 查询）
        direction: 滑动方向 up/down/left/right，默认 up
        distance: 滑动距离，默认 500
    """
    action_time = _action_stamp()
    with _device_engine(serial) as engine:
        engine.swipe_direction(direction or "up", int(distance or 500))
        return _with_action_time(_jsonable(engine.app_current()), action_time)


def press_key(serial: str, user_id: str = "") -> str:
    """按设备返回键（BACK）返回上一页；每次返回 package/activity 用于判断页面是否跳转。
    Args:
        serial: 设备序列号（先 list_devices 查询）
    """
    action_time = _action_stamp()
    with _device_engine(serial) as engine:
        engine.press_key("back")
        return _with_action_time(_jsonable(engine.app_current()), action_time)


def input_text(
    serial: str,
    text: str,
    clear_first: bool = True,
    user_id: str = "",
) -> str:
    """向设备当前输入框输入文本；每次返回 package/activity 用于判断页面是否跳转。
    Args:
        serial: 设备序列号（先 list_devices 查询）
        text: 要输入的文本
        clear_first: 输入前是否清空输入框，默认 True
    """
    action_time = _action_stamp()
    with _device_engine(serial) as engine:
        engine.input_text(text or "", clear_first=bool(clear_first))
        return _with_action_time(_jsonable(engine.app_current()), action_time)


def current_app(serial: str, user_id: str = "") -> str:
    """只读设备当前前台 App（package/activity/pid），不改变设备状态。
    Args:
        serial: 设备序列号（先 list_devices 查询）
    """
    with _device_engine(serial) as engine:
        return _jsonable(engine.app_current())


def click_ratio(serial: str, nx: float, ny: float, user_id: str = "") -> str:
    """按归一化坐标点击（视觉模型看图后输出相对位置，工具换算成屏幕像素坐标）。
    Args:
        serial: 设备序列号
        nx: 横向相对位置 0~1（0=最左，1=最右）
        ny: 纵向相对位置 0~1（0=最上，1=最下）
    """
    from apps.device_pool.api import use_device
    from apps.device_pool.models import Device
    from engines.device.registry import close_engine, open_engine

    use_device(serial)
    dev = Device.objects.get(serial=serial)
    engine = open_engine(serial, dev.connection_addr or serial)
    action_time = _action_stamp()
    try:
        engine.click_ratio(nx, ny)
        return _with_action_time(_jsonable(engine.app_current()), action_time)
    finally:
        close_engine(engine)


def drag_ratio(
    serial: str,
    nx1: float,
    ny1: float,
    nx2: float,
    ny2: float,
    user_id: str = "",
) -> str:
    """按归一化坐标拖动（视觉模型看图后输出起终点相对位置，工具换算成屏幕像素坐标）。
    Args:
        serial: 设备序列号
        nx1: 起点横向相对位置 0~1（0=最左，1=最右）
        ny1: 起点纵向相对位置 0~1（0=最上，1=最下）
        nx2: 终点横向相对位置 0~1
        ny2: 终点纵向相对位置 0~1
    """
    from apps.device_pool.api import use_device
    from apps.device_pool.models import Device
    from engines.device.registry import close_engine, open_engine

    use_device(serial)
    dev = Device.objects.get(serial=serial)
    engine = open_engine(serial, dev.connection_addr or serial)
    action_time = _action_stamp()
    try:
        engine.drag_ratio(nx1, ny1, nx2, ny2)
        return _with_action_time(_jsonable(engine.app_current()), action_time)
    finally:
        close_engine(engine)


def xpath_action(
    serial: str,
    action: str,
    xpath: str,
    index: int = 0,
    timeout: float = 0,
    user_id: str = "",
) -> str:
    """通过 xpath 定位并控制设备元素：检查存在 / 读取文本 / 点击 / 长按。
    Args:
        serial: 设备序列号（先 list_devices 查询）
        action: 动作类型: exists/get_text/click/long_click
        xpath: 元素 xpath 表达式（如 //android.widget.TextView[@text='H6110']）
        index: 多匹配时第几个，默认 0
        timeout: exists 时等待元素出现的秒数，默认 0（立即）
    """
    from apps.device_pool.api import use_device
    from apps.device_pool.models import Device
    from engines.device.registry import close_engine, open_engine

    use_device(serial)
    dev = Device.objects.get(serial=serial)
    engine = open_engine(serial, dev.connection_addr or serial)
    try:
        if action == "exists":
            return _jsonable({"exists": engine.exists(xpath, timeout=timeout)})
        if action == "get_text":
            return _jsonable({"text": engine.get_text(xpath)})
        if action == "click":
            action_time = _action_stamp()
            ok = engine.click_xpath(xpath, index=index)
            return _with_action_time(
                _jsonable({"clicked": ok, "current": engine.app_current()}), action_time
            )
        if action == "long_click":
            action_time = _action_stamp()
            ok = engine.long_click_xpath(xpath, index=index)
            return _with_action_time(
                _jsonable({"clicked": ok, "current": engine.app_current()}), action_time
            )
        raise ValueError(f"不支持的 xpath 动作: {action}")
    finally:
        close_engine(engine)


def list_apps(serial: str, query: str = "", user_id: str = "") -> str:
    """列出设备已安装的应用包名（供获取被测 App 包名）。
    Args:
        serial: 设备序列号
        query: 包名关键词过滤
    """
    from apps.device_pool.api import use_device
    from apps.device_pool.models import Device
    from engines.device.registry import close_engine, open_engine

    use_device(serial)
    dev = Device.objects.get(serial=serial)
    engine = open_engine(serial, dev.connection_addr or serial)
    try:
        raw = engine.shell("pm list packages")
    finally:
        close_engine(engine)

    packages = []
    for line in (raw or "").splitlines():
        line = line.strip()
        if not line.startswith("package:"):
            continue
        pkg = line[len("package:") :].strip()
        if pkg and (not query or query.lower() in pkg.lower()):
            packages.append(pkg)
    return _jsonable({"packages": packages, "count": len(packages)})


# ═══════════════════════════════════════════════════════════════════
# 设备检查器工具
# ═══════════════════════════════════════════════════════════════════


def screenshot_page(serial: str, keep_local: bool = True, user_id: str = "") -> dict:
    """截取设备当前屏幕并返回图片（给视觉模型看图）。轻量：仅校验设备 + 截图，不 dump/OCR/落库。

    Args:
        serial: 设备序列号
        keep_local: True 时在 summary 中回传落盘相对路径/文件名（验收证据用）；
            False 时仍截屏给模型看图，但不暴露路径。截图文件始终由 capture_screen 落盘。
    """
    import base64
    import io as _io

    from pathlib import Path

    from django.conf import settings
    from PIL import Image

    from apps.device_inspector.api import capture_screen

    data = capture_screen(serial)
    shot_rel = (data.get("screenshot_path") or "").replace("\\", "/").strip()
    if not shot_rel:
        raise ValueError("截屏失败：未获取到截图路径")
    shot_file = Path(settings.MEDIA_ROOT) / shot_rel
    if not shot_file.is_file():
        raise ValueError("截屏失败：截图文件不存在")
    _img = Image.open(_io.BytesIO(shot_file.read_bytes()))
    _img.thumbnail((1280, 1280))
    if _img.mode not in ("RGB", "L"):
        _img = _img.convert("RGB")
    _buf = _io.BytesIO()
    _img.save(_buf, format="JPEG", quality=85)
    img_b64 = base64.b64encode(_buf.getvalue()).decode("ascii")

    summary = {
        "serial": data.get("serial"),
        "package": data.get("package"),
        "activity": data.get("activity"),
        "screen_w": data.get("screen_w"),
        "screen_h": data.get("screen_h"),
    }
    # 路径由工具回传真相，禁止依赖模型在 JSON 里抄路径
    if keep_local:
        summary["screenshot_path"] = shot_rel
        summary["screenshot_name"] = Path(shot_rel).name
    return {
        "image": {"base64": img_b64, "media_type": "image/jpeg"},
        "summary": summary,
    }


def ocr_page(serial: str, texts: str = "", user_id: str = "") -> str:
    """OCR 识别设备当前页面的文本，返回文本、置信度、原始角点坐标与归一化中心点。

    中心点为 0~1 的归一化坐标，可直接作为点击/拖拽工具的入参使用。
    页面文本很多时用 texts 收窄结果，避免返回无关文本。

    Args:
        serial: 设备序列号
        texts: 要查找的文本，可一次指定多个，用逗号/顿号/换行分隔（如「设置,WiFi」）；
            命中任一即返回（忽略大小写的子串匹配）；留空返回整页全部文本
    """
    from apps.device_inspector.api import ocr_screen

    return _jsonable(ocr_screen(serial, texts))


# ═══════════════════════════════════════════════════════════════════
# 设备日志（只读查询）
# ═══════════════════════════════════════════════════════════════════

LOG_SPAN_DEFAULT_SECONDS = 30.0
LOG_SPAN_MAX_SECONDS = 300.0
LOG_AT_FORMATS = ("%Y-%m-%d %H:%M:%S.%f", "%H:%M:%S.%f")


def _parse_log_at(value: str):
    """解析查询时间点：支持完整时间与只给时刻（按当天北京时间）。非法值抛可读错误。"""
    from engines.device.logbus import BEIJING_TZ

    text = (value or "").strip()
    for fmt in LOG_AT_FORMATS:
        try:
            moment = datetime.strptime(text, fmt)
        except ValueError:
            continue
        if fmt.startswith("%H"):
            today = datetime.now(BEIJING_TZ).date()
            moment = datetime.combine(today, moment.time())
        return moment.replace(tzinfo=BEIJING_TZ)

    raise ValueError(
        f"时间点无法解析: {value!r}；期望 `YYYY-MM-DD HH:MM:SS.mmm` 或 `HH:MM:SS.mmm`（北京时间）"
    )


def _clamp_log_span(seconds: float) -> float:
    span = float(seconds or 0) or LOG_SPAN_DEFAULT_SECONDS
    return max(1.0, min(span, LOG_SPAN_MAX_SECONDS))


def read_device_log(
    at: str = "",
    seconds: float = 0,
    port: int = 0,
    keyword: str = "",
    user_id: str = "",
) -> str:
    """查询平台已采集的设备日志（只读，不连设备、不改设备状态）。
    排查「设备到底响应了没有」「某个功能点打印了没有」时用；不要每一步都调用。
    取数是**内存缓冲 + 已落盘的日志文件**：缓冲覆盖不到的更早时段会从日志文件回溯，
    因此查一个几分钟前的时刻同样查得到（不再受缓冲保留时长限制）。
    同一时间戳的日志会合并成一条（text 内保留换行），且**最新的时间排在最上面**。

    Args:
        at: 时间点（北京时间）。可写 `2026-09-28 13:05:37.500`，也可只写 `13:05:37.500`（按今天）。
            给了就返回**该时刻之后**一个跨度的日志；不传则返回**最近**一个跨度
        seconds: 跨度秒数，默认 30，最大 300
        port: 日志来源端口，默认平台配置的端口（现场 7005）；传未配置的端口不报错，返回「端口 X 未配置为日志来源」的结论
        keyword: 可选，只看包含该关键词的日志行（忽略大小写），并还原命中的功能模块 / 功能点
    """
    from engines.device.logbus import LogSourceUnknown, get_log_bus, merge_lines_by_timestamp

    from . import log_port_service

    bus = get_log_bus()
    if bus is None:
        raise ValueError("设备日志采集未启动：平台未开启日志采集（DEVICE_LOG_ENABLED）或无可用来源")

    span = _clamp_log_span(seconds)
    if at:
        start = _parse_log_at(at)
        start_epoch = start.timestamp()
        end_epoch = start_epoch + span
        start_stamp, end_stamp = _log_stamp(start_epoch), _log_stamp(end_epoch)
    else:
        end_epoch = time.time()
        start_epoch = end_epoch - span
        start_stamp, end_stamp = _log_stamp(start_epoch), _log_stamp(end_epoch)

    wanted = (keyword or "").strip()
    query = {
        "port": int(port) if port else 0,
        "channel": "",
        "from": start_stamp,
        "to": end_stamp,
        "span_seconds": span,
        "keyword": wanted,
    }

    # 已登记但开关关闭的端口：给可读结论（不报错、不去连端口、也不打开监听）
    disabled_port = log_port_service.disabled_port_note(int(port) if port else 0)
    if disabled_port:
        query["port"] = int(port)
        return json.dumps(
            {
                "query": query,
                "line_count": 0,
                "conclusion": "port_disabled",
                "note": disabled_port,
                "lines": [],
                "keyword_hits": [],
            },
            ensure_ascii=False,
        )

    try:
        found = bus.read_range(
            start_epoch=start_epoch,
            end_epoch=end_epoch,
            port=int(port) if port else None,
        )
    except LogSourceUnknown as exc:
        # 未配置的端口不是调用错误：返回可读结论（HTTP 200），由调用方/AI 自行改端口
        return json.dumps(
            {
                "query": query,
                "line_count": 0,
                "conclusion": "port_not_configured",
                "note": str(exc),
                "lines": [],
                "keyword_hits": [],
            },
            ensure_ascii=False,
        )

    rows = found["lines"]
    query["port"] = int(found["port"])
    query["channel"] = found["channel"]
    hits: list[dict] = []
    if wanted:
        matched = [line for line in rows if wanted.lower() in line.text.lower()]
        for line in matched:
            for name, features in bus.keywords.match(line.text):
                hits.append({"keyword": name, "timestamp": line.timestamp, "features": features})
        rows = matched

    if not rows:
        conclusion = "no_keyword_hit" if wanted else "no_log"
        note = (
            f"该时间范围内没有包含 {wanted!r} 的日志"
            if wanted
            else "该时间范围内无日志（已查内存缓冲与已落盘的日志文件）"
        )
    else:
        conclusion = "ok"
        note = ""

    raw_line_count = len(rows)
    merged = merge_lines_by_timestamp(rows)
    payload = {
        "query": query,
        "line_count": len(merged),
        "raw_line_count": raw_line_count,
        # 取数来源：缓冲 / 已落盘文件各取到多少行（排查「为什么以前查不到」用）
        "sources": {
            "buffer_lines": int(found.get("buffer_lines") or 0),
            "file_lines": int(found.get("file_lines") or 0),
        },
        "conclusion": conclusion,
        "note": note,
        "lines": merged,
        "keyword_hits": hits,
    }
    return json.dumps(payload, ensure_ascii=False, default=str)


def _catalog_features(bus, keyword: str) -> tuple[list[dict], bool]:
    """关键词表里该词的登记功能点（大小写不敏感）；未登记返回空表与 False。"""
    mapping = getattr(getattr(bus, "keywords", None), "mapping", {}) or {}
    if keyword in mapping:
        return list(mapping[keyword]), True
    lowered = keyword.lower()
    for name, features in mapping.items():
        if name.lower() == lowered:
            return list(features), True
    return [], False


def check_device_log(
    keyword: str,
    at: str = "",
    seconds: float = 0,
    port: int = 0,
    user_id: str = "",
) -> str:
    """按规则检查一个日志关键词在指定窗口内**有没有出现**（只读，不连设备、不改状态）。
    验收断言要看设备日志时用它：**只需报出要检查的关键词**（例如开关类 `switch_on`、
    关闭类 `switch_off`），由平台按与日志证据同一套规则判定「检测到 / 未检测到」，
    并给出出现的时间戳与功能点。不要自己翻原始日志行下结论。
    判定口径：**检测到 + 截图确认两个条件都满足才可判 PASS；未检测到必须判 FAIL**。

    Args:
        keyword: 要检查的日志关键词（必填，忽略大小写；可从输入给的关键词表里选）
        at: 取证基准时间点（北京时间）。给了就检查该时刻之后一个窗口；不传则检查最近一个窗口
        seconds: 窗口秒数，默认取平台取证阈值（5 秒），最大 300
        port: 日志来源端口，默认平台配置的端口（现场 7005）
    """
    from django.conf import settings

    from engines.device.logbus import LogSourceUnknown, get_log_bus, merge_lines_by_timestamp

    from . import log_port_service

    wanted = str(keyword or "").strip()
    span = float(seconds or 0) or float(
        getattr(settings, "DEVICE_LOG_WINDOW_SECONDS", LOG_SPAN_DEFAULT_SECONDS)
    )
    span = max(1.0, min(span, LOG_SPAN_MAX_SECONDS))
    if at:
        start = _parse_log_at(at)
        start_epoch = start.timestamp()
    else:
        start_epoch = time.time()
    end_epoch = start_epoch + span
    query = {
        "port": int(port) if port else 0,
        "channel": "",
        "from": _log_stamp(start_epoch),
        "to": _log_stamp(end_epoch),
        "span_seconds": span,
        "keyword": wanted,
    }

    def _payload(**extra) -> str:
        base = {
            "query": query,
            "detected": False,
            "conclusion": "",
            "timestamps": [],
            "hit_count": 0,
            "features": [],
            "keyword_known": False,
            "sources": {"buffer_lines": 0, "file_lines": 0},
            "lines": [],
            "note": "",
        }
        base.update(extra)
        return json.dumps(base, ensure_ascii=False, default=str)

    if not wanted:
        return _payload(
            conclusion="keyword_missing",
            note="需要给出要检查的日志关键词（例如开关类 switch_on / switch_off）",
        )

    disabled_port = log_port_service.disabled_port_note(int(port) if port else 0)
    if disabled_port:
        query["port"] = int(port)
        return _payload(conclusion="port_disabled", note=disabled_port)

    bus = get_log_bus()
    if bus is None:
        raise ValueError("设备日志采集未启动：平台未开启日志采集（DEVICE_LOG_ENABLED）或无可用来源")

    try:
        found = bus.read_range(
            start_epoch=start_epoch,
            end_epoch=end_epoch,
            port=int(port) if port else None,
        )
    except LogSourceUnknown as exc:
        return _payload(conclusion="port_not_configured", note=str(exc))

    query["port"] = int(found["port"])
    query["channel"] = found["channel"]
    rows = found["lines"]
    matched = [line for line in rows if wanted.lower() in line.text.lower()]
    features, known = _catalog_features(bus, wanted)
    timestamps = [line.timestamp for line in matched]

    if timestamps:
        conclusion = "hit"
        note = "" if known else f"已检测到，但 {wanted!r} 不在平台关键词表内（功能点无法标注）"
    elif not rows:
        conclusion = "no_log"
        note = "该窗口内没有任何日志（缓冲与已落盘的日志文件都没有）"
    else:
        conclusion = "no_hit"
        note = f"该窗口内有日志，但没有出现 {wanted!r}"
        if not known:
            note += "；该关键词不在平台关键词表内"

    return _payload(
        detected=bool(timestamps),
        conclusion=conclusion,
        timestamps=timestamps,
        hit_count=len(timestamps),
        features=features,
        keyword_known=known,
        sources={
            "buffer_lines": int(found.get("buffer_lines") or 0),
            "file_lines": int(found.get("file_lines") or 0),
        },
        lines=merge_lines_by_timestamp(matched),
        note=note,
    )


def _log_stamp(epoch: float) -> str:
    """epoch → 北京时间毫秒字符串（与采集层同一口径）。"""
    from engines.device.logbus import format_stamp

    return format_stamp(datetime.fromtimestamp(epoch, tz=timezone.utc))


# ═══════════════════════════════════════════════════════════════════
# 页面流工具
# ═══════════════════════════════════════════════════════════════════


def list_page_flows(query: str = "", user_id: str = "") -> str:
    """列出平台全部页面流文档（不截断）；每条含 directory_path（目录完整路径）与
    directory_depth（根目录下为 1，未归类为 0）。
    Args:
        query: 可选关键词，按标题或文档 ID 收窄；留空返回全部
    """
    from apps.workflow.api import list_document_summaries

    documents = list_document_summaries(query=query)
    return _jsonable({"total": len(documents), "documents": documents})


def get_page_flow(doc_id: str, user_id: str = "") -> str:
    """获取页面流文档的语义摘要。
    Args:
        doc_id: 文档ID
    """
    from apps.workflow.api import get_document_digest

    ok, data = get_document_digest(doc_id)
    if not ok:
        raise ValueError(data)
    return _jsonable(data)


# ═══════════════════════════════════════════════════════════════════
# 工具注册表：工具名 → (函数, is_read_only)
# ═══════════════════════════════════════════════════════════════════

# 设备管理/控制类工具自动放行（不走 HITL）：acquire/release 是占用记账、
# 其余是用户明确要求"控制设备"时的核心写动作（只读的 current_app 走只读分支放行）。
AUTO_ALLOW_TOOLS = {
    "acquire_device",
    "release_device",
    "app_control",
    "tap_screen",
    "swipe_screen",
    "press_key",
    "input_text",
    "click_ratio",
    "drag_ratio",
    "xpath_action",
}

TOOLS: dict[str, tuple] = {
    # 设备管理（获取设备信息）
    "list_devices": (list_devices, True),
    "acquire_device": (acquire_device, False),
    "release_device": (release_device, False),
    "list_apps": (list_apps, True),
    # 设备管理（执行控制操作）
    "app_control": (app_control, False),
    "tap_screen": (tap_screen, False),
    "swipe_screen": (swipe_screen, False),
    "press_key": (press_key, False),
    "input_text": (input_text, False),
    "current_app": (current_app, True),
    "click_ratio": (click_ratio, False),
    "drag_ratio": (drag_ratio, False),
    "xpath_action": (xpath_action, False),
    # 设备检查器
    "screenshot_page": (screenshot_page, True),
    # 视觉识别
    "ocr_page": (ocr_page, True),
    # 页面流工具（获取页面流信息）
    "list_page_flows": (list_page_flows, True),
    "get_page_flow": (get_page_flow, True),
    # 设备日志（只读查询）
    "read_device_log": (read_device_log, True),
    # 设备日志（只读：按关键词规则检查是否出现，验收侧用）
    "check_device_log": (check_device_log, True),
}


# ═══════════════════════════════════════════════════════════════════
# 工具分类元数据（供管理端 available-tools / 工具箱 / HTTP 网关）
# ═══════════════════════════════════════════════════════════════════

# 分类是工具箱「整类启停」的单位（views_drf.PlatformToolToggleAPIView 按 category 批量写库），
# 因此按工具性质分组：台账（不碰手机）/ 控制（会在手机上产生副作用）/ 信息（只读但要连设备）。
TOOL_CATEGORIES = [
    {"key": "设备管理", "icon": "📱", "color": "#6BCB77"},
    {"key": "设备控制", "icon": "🎮", "color": "#F7C948"},
    {"key": "设备信息", "icon": "📋", "color": "#4ECDC4"},
    {"key": "设备检查器", "icon": "📸", "color": "#FFB5A7"},
    {"key": "视觉识别工具", "icon": "🔍", "color": "#A78BFA"},
    {"key": "页面流工具", "icon": "🧭", "color": "#38BDF8"},
    {"key": "设备日志", "icon": "📜", "color": "#94A3B8"},
]

_CATEGORY_ICON = {c["key"]: c["icon"] for c in TOOL_CATEGORIES}

# 工具名 → (分类, module, action)
TOOL_META: dict[str, tuple[str, str, str]] = {
    # 设备管理：设备池台账，不操作手机
    "list_devices": ("设备管理", "devices", "list_all"),
    "acquire_device": ("设备管理", "devices", "acquire"),
    "release_device": ("设备管理", "devices", "release"),
    # 设备控制：会在手机上产生副作用，可整类关闭
    "app_control": ("设备控制", "devices", "app_control"),
    "tap_screen": ("设备控制", "devices", "tap_screen"),
    "swipe_screen": ("设备控制", "devices", "swipe_screen"),
    "press_key": ("设备控制", "devices", "press_key"),
    "input_text": ("设备控制", "devices", "input_text"),
    "click_ratio": ("设备控制", "devices", "click_ratio"),
    "drag_ratio": ("设备控制", "devices", "drag_ratio"),
    "xpath_action": ("设备控制", "devices", "xpath_action"),
    # 设备信息：只读，但要连设备取数
    "list_apps": ("设备信息", "devices", "list_apps"),
    "current_app": ("设备信息", "devices", "current_app"),
    "screenshot_page": ("设备检查器", "inspector", "screenshot"),
    "ocr_page": ("视觉识别工具", "inspector", "ocr"),
    "list_page_flows": ("页面流工具", "workflow", "list_page_flows"),
    "get_page_flow": ("页面流工具", "workflow", "get_page_flow"),
    # 设备日志：只读查询已采集的日志（不连设备、不改状态）
    "read_device_log": ("设备日志", "log", "read"),
    # 设备日志：只读按规则检查关键词是否出现（验收侧用）
    "check_device_log": ("设备日志", "log", "check"),
}


def list_tool_schemas() -> list[dict]:
    """工具 schema 列表（name/summary/category/icon/module/action/read_only），供管理端展示。"""
    schemas = []
    for name, (func, read_only) in TOOLS.items():
        category, module, action = TOOL_META[name]
        schemas.append(
            {
                "name": name,
                "summary": (func.__doc__ or "").strip().split("\n")[0],
                "category": category,
                "icon": _CATEGORY_ICON.get(category, "🔧"),
                "module": module,
                "action": action,
                "read_only": read_only,
            }
        )
    return schemas


def resolve_by_module_action(module: str, action: str):
    """(module, action) → 工具函数（供 HTTP 工具网关），找不到返回 None。"""
    for name, (cat, m, a) in TOOL_META.items():
        if m == module and a == action:
            return TOOLS[name][0]
    return None


# ═══════════════════════════════════════════════════════════════════
# 调试：入参 schema + 按名调用（JWT 管理面，非内部网关）
# ═══════════════════════════════════════════════════════════════════


class ToolNotFoundError(LookupError):
    """平台工具名未在 TOOLS 注册。"""


def _annotation_type_name(annotation) -> str:
    """类型注解 → 调试表单用的简单类型名（str/int/float/bool）。"""
    if annotation is inspect.Parameter.empty:
        return "str"
    if isinstance(annotation, str):
        base = annotation.split("|", 1)[0].strip()
        if base in ("int", "float", "bool", "str"):
            return base
        return "str"
    if annotation is int:
        return "int"
    if annotation is float:
        return "float"
    if annotation is bool:
        return "bool"
    return "str"


def _coerce_param(value, annotation):
    """按注解把表单/JSON 值转成工具期望类型；无法转换则 ValueError。"""
    type_name = _annotation_type_name(annotation)
    if value is None:
        return None
    if type_name == "bool":
        if isinstance(value, bool):
            return value
        if isinstance(value, str):
            low = value.strip().lower()
            if low in ("true", "1", "yes"):
                return True
            if low in ("false", "0", "no"):
                return False
        raise ValueError(f"无法转换为 bool: {value!r}")
    if type_name == "int":
        try:
            return int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"无法转换为 int: {value!r}") from exc
    if type_name == "float":
        try:
            return float(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"无法转换为 float: {value!r}") from exc
    return str(value) if value is not None else ""


def _normalize_debug_result(result):
    """工具返回 → 可 JSON 化对象（str 尝试 parse，与内部网关语义一致）。"""
    if isinstance(result, str):
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return result
    return result


# 调试候选登记：工具名 → 参数名 → 候选来源标识。
# 命中的参数在 schema 里声明候选来源，由 HTTP 视图按请求者身份解析成候选清单
# （见 views_tool_debug_drf）。只登记「需要 serial 并经开引擎取数」的设备管理工具：
# acquire/release 是设备池占用记账、不操作手机，不提供候选。
DEBUG_PARAM_OPTIONS: dict[tuple[str, str], str] = {
    ("list_apps", "serial"): "devices:available",
    ("input_text", "serial"): "devices:available",
    ("tap_screen", "serial"): "devices:available",
    ("swipe_screen", "serial"): "devices:available",
    ("press_key", "serial"): "devices:available",
    ("current_app", "serial"): "devices:available",
    ("click_ratio", "serial"): "devices:available",
    ("drag_ratio", "serial"): "devices:available",
    ("xpath_action", "serial"): "devices:available",
}

# ═══════════════════════════════════════════════════════════════════
# 参数中文名（调试表单标签唯一真相源）
# ═══════════════════════════════════════════════════════════════════

# 参数名 → 中文短名（跨工具复用）；未登记的参数回退英文名本身。
PARAM_LABELS: dict[str, str] = {
    "serial": "设备序列号",
    "timeout": "超时秒数",
    "reason": "释放原因",
    "package": "应用包名",
    "mode": "点击方式",
    "x": "横坐标",
    "y": "纵坐标",
    "direction": "滑动方向",
    "distance": "滑动距离",
    "text": "输入文本",
    "clear_first": "输入前清空",
    "nx": "横向相对位置",
    "ny": "纵向相对位置",
    "nx1": "起点横向位置",
    "ny1": "起点纵向位置",
    "nx2": "终点横向位置",
    "ny2": "终点纵向位置",
    "xpath": "元素 xpath",
    "index": "匹配序号",
    "keep_local": "保留本地截图",
    "texts": "要查找的文本",
    "doc_id": "页面流文档 ID",
    "at": "时间点",
    "seconds": "查询跨度（秒）",
    "port": "日志端口",
    "keyword": "日志关键词搜索",
}

# 工具级覆盖：同名参数在不同工具下语义不同时用这里（优先于 PARAM_LABELS）。
TOOL_PARAM_LABELS: dict[tuple[str, str], str] = {
    ("app_control", "action"): "应用动作类型",
    ("xpath_action", "action"): "元素动作类型",
    ("list_apps", "query"): "包名关键词",
    ("list_page_flows", "query"): "文档关键词",
    ("read_device_log", "keyword"): "日志关键词搜索",
    ("read_device_log", "at"): "日志时间点",
    ("read_device_log", "seconds"): "查询跨度（秒）",
    ("read_device_log", "port"): "日志端口",
    ("check_device_log", "keyword"): "要检查的日志关键词",
    ("check_device_log", "at"): "取证基准时间点",
    ("check_device_log", "seconds"): "窗口秒数（默认 5）",
    ("check_device_log", "port"): "日志端口",
}


def param_label(name: str, tool_name: str = "") -> str:
    """参数中文名：工具级覆盖 → 通用表 → 回退英文名（绝不返回空串）。"""
    return TOOL_PARAM_LABELS.get((tool_name, name)) or PARAM_LABELS.get(name) or name


# ═══════════════════════════════════════════════════════════════════
# 工具 docstring 的 Args 段 → 参数中文说明
# ═══════════════════════════════════════════════════════════════════

_ARGS_SECTION = re.compile(r"^\s*Args\s*:\s*$")


def param_hints(func) -> dict[str, str]:
    """解析 docstring 的 `Args` 段：参数名 → 说明（续行并入）。取不到返回空表。"""
    doc = inspect.getdoc(func) or ""
    hints: dict[str, str] = {}
    current = ""
    in_args = False
    for line in doc.splitlines():
        if _ARGS_SECTION.match(line):
            in_args = True
            continue
        if not in_args:
            continue
        stripped = line.strip()
        if not stripped:
            continue
        match = re.match(r"^([a-z_][a-z0-9_]*)\s*:\s*(.*)$", stripped)
        if match:
            current = match.group(1)
            hints[current] = match.group(2).strip()
        elif current and line.startswith((" ", "\t")):
            hints[current] = f"{hints[current]} {stripped}".strip()
        else:
            # 缩进回到 Args 段之外（例如新的段落/小节）→ 结束解析
            break
    return hints


# 候选来源标识：可用设备。平台工具调试页（HTTP schema）与模型调试页（真机操作前校验）
# 共用下面的实现，避免两份过滤口径漂移。
_DEVICE_OPTIONS_SOURCE = "devices:available"


def available_device_options(user_id: str) -> list[dict]:
    """候选设备：对请求者可见、状态在线且当前未被占用。

    可见性口径复用 device_pool 的 api（与设备管理列表同源），本函数不另做可见性判定。
    """
    from apps.device_pool.api import list_devices
    from models.constants import DeviceStatus

    options = []
    for dev in list_devices(user_id=user_id):
        if dev.get("status") != DeviceStatus.ONLINE or dev.get("occupied_by"):
            continue
        serial = str(dev.get("serial") or "")
        if not serial:
            continue
        label = str(dev.get("name") or dev.get("model") or serial)
        options.append({"value": serial, "label": f"{label} ({serial})"})
    return options


def resolve_param_options(source: str, user_id: str) -> list[dict]:
    """候选来源标识 → 候选项清单；未知来源返回空清单。"""
    if source == _DEVICE_OPTIONS_SOURCE:
        return available_device_options(user_id)
    return []


def get_tool_debug_schema(name: str) -> dict:
    """按工具名返回调试用入参 schema（不含 user_id）。未注册则 ToolNotFoundError。

    每个参数含 `label`（中文名，未登记回退英文名）与 `hint`（docstring Args 段说明，缺失为空串），
    供调试页渲染「中文名（english_name）+ 必填/可选」。
    """
    if name not in TOOLS:
        raise ToolNotFoundError(name)
    func, read_only = TOOLS[name]
    hints = param_hints(func)
    parameters = []
    for pname, param in inspect.signature(func).parameters.items():
        if pname == "user_id":
            continue
        has_default = param.default is not inspect.Parameter.empty
        entry = {
            "name": pname,
            "label": param_label(pname, name),
            "hint": hints.get(pname, ""),
            "type": _annotation_type_name(param.annotation),
            "required": not has_default,
        }
        if has_default:
            entry["default"] = param.default
        options_source = DEBUG_PARAM_OPTIONS.get((name, pname))
        if options_source:
            entry["options_source"] = options_source
        parameters.append(entry)
    return {
        "name": name,
        "summary": (func.__doc__ or "").strip().split("\n")[0],
        "read_only": read_only,
        "parameters": parameters,
    }


def invoke_platform_tool(name: str, user_id: str, params: dict | None = None):
    """按名调用平台工具：丢弃 body.user_id，拒绝未知键，注入 JWT user_id。"""
    if name not in TOOLS:
        raise ToolNotFoundError(name)
    func, _read_only = TOOLS[name]
    raw = dict(params or {})
    raw.pop("user_id", None)

    sig = inspect.signature(func)
    allowed = {pname for pname in sig.parameters if pname != "user_id"}
    unknown = set(raw) - allowed
    if unknown:
        raise ValueError(f"未知参数: {', '.join(sorted(unknown))}")

    kwargs = {}
    for key, value in raw.items():
        kwargs[key] = _coerce_param(value, sig.parameters[key].annotation)

    for pname, param in sig.parameters.items():
        if pname == "user_id":
            continue
        if param.default is inspect.Parameter.empty and pname not in kwargs:
            raise ValueError(f"缺少必填参数: {pname}")

    result = func(user_id=str(user_id or ""), **kwargs)
    return _normalize_debug_result(result)
