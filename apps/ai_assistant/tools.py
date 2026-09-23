"""平台工具 — 框架无关的纯函数 + 工具注册表（Django 层）。

工具 = 普通函数（类型注解 + docstring 自动推导 schema），只调各 App api.py。
框架包装（PlatformFunctionTool / build_toolkit）在 `engines.ai.agentscope.tool_wrapper`，
经 `TaskRequest.tools` 注入引擎；`user_id` 由包装层构造时注入。
"""

from __future__ import annotations

import inspect
import json

from contextlib import contextmanager

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
        return _jsonable(engine.app_current())


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
        return _jsonable(engine.app_current())


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
    with _device_engine(serial) as engine:
        engine.swipe_direction(direction or "up", int(distance or 500))
        return _jsonable(engine.app_current())


def press_key(serial: str, user_id: str = "") -> str:
    """按设备返回键（BACK）返回上一页；每次返回 package/activity 用于判断页面是否跳转。
    Args:
        serial: 设备序列号（先 list_devices 查询）
    """
    with _device_engine(serial) as engine:
        engine.press_key("back")
        return _jsonable(engine.app_current())


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
    with _device_engine(serial) as engine:
        engine.input_text(text or "", clear_first=bool(clear_first))
        return _jsonable(engine.app_current())


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
    try:
        engine.click_ratio(nx, ny)
        return _jsonable(engine.app_current())
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
    try:
        engine.drag_ratio(nx1, ny1, nx2, ny2)
        return _jsonable(engine.app_current())
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
            ok = engine.click_xpath(xpath, index=index)
            return _jsonable({"clicked": ok, "current": engine.app_current()})
        if action == "long_click":
            ok = engine.long_click_xpath(xpath, index=index)
            return _jsonable({"clicked": ok, "current": engine.app_current()})
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


def get_tool_debug_schema(name: str) -> dict:
    """按工具名返回调试用入参 schema（不含 user_id）。未注册则 ToolNotFoundError。"""
    if name not in TOOLS:
        raise ToolNotFoundError(name)
    func, read_only = TOOLS[name]
    parameters = []
    for pname, param in inspect.signature(func).parameters.items():
        if pname == "user_id":
            continue
        has_default = param.default is not inspect.Parameter.empty
        entry = {
            "name": pname,
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
