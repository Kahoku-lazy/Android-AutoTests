"""平台工具 — 普通 Python 函数 + FunctionTool 包装（框架能力，不重写）。

工具 = 普通函数（类型注解 + docstring 自动推导 schema），经 `PlatformFunctionTool`
包装。`user_id` 由工具构造时注入，不出现在 LLM 可见的 input_schema 里。
"""

from __future__ import annotations

import asyncio
import inspect
import json

from agentscope.message import Base64Source, DataBlock, TextBlock
from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.tool import FunctionTool, ToolChunk, Toolkit

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


# ═══════════════════════════════════════════════════════════════════
# 权限子类：user_id 注入 + 只读自动放行
# ═══════════════════════════════════════════════════════════════════


class PlatformFunctionTool(FunctionTool):
    """平台工具：构造时绑定 user_id，只读/内部锁自动放行、其余写操作 ASK。"""

    def __init__(
        self,
        func,
        user_id: str = "",
        is_read_only: bool = False,
        auto_allow: bool = False,
        is_concurrency_safe: bool = True,
    ):
        # 写工具（is_read_only=False）必须串行执行，否则模型一次返回多个 tool_call
        # 时 device_action/click_ratio 等会并发执行，破坏设备动作顺序。
        super().__init__(
            func,
            is_read_only=is_read_only,
            is_concurrency_safe=is_concurrency_safe,
        )
        self._user_id = user_id
        self._auto_allow = auto_allow
        # 从 LLM 可见 schema 中移除 user_id（运行时注入，不暴露给模型）
        props = self.input_schema.get("properties", {})
        props.pop("user_id", None)
        required = self.input_schema.get("required", [])
        if "user_id" in required:
            required.remove("user_id")

    async def call(self, **kwargs):
        kwargs.setdefault("user_id", self._user_id)
        # 同步 handler 转线程执行，避免 async 上下文直调同步 Django ORM 触发
        # SynchronousOnlyOperation（平台 handler 均为同步函数，返回 JSON 字符串）。
        if inspect.iscoroutinefunction(self._func):
            return await super().call(**kwargs)
        result = await asyncio.to_thread(self._func, **kwargs)
        return self._convert_func_result_to_chunk(result)

    async def check_permissions(self, tool_input, context):
        if self.is_read_only:
            return PermissionDecision(PermissionBehavior.ALLOW, "只读工具直接放行")
        if self._auto_allow:
            return PermissionDecision(PermissionBehavior.ALLOW, "平台内部锁，自动放行")
        return PermissionDecision(PermissionBehavior.ASK, "写工具需确认")


# ═══════════════════════════════════════════════════════════════════
# 设备管理工具
# ═══════════════════════════════════════════════════════════════════


def get_online_devices(user_id: str = "") -> str:
    """查询平台当前在线的 Android 设备列表（不含使用中设备）。"""
    from apps.device_pool.api import get_online_devices as _f

    return _jsonable(_f())


def list_devices(user_id: str = "") -> str:
    """查询设备管理中的全部设备及状态（在线/使用中），含使用人、锁定人、剩余占用时间。"""
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


def device_action(
    serial: str,
    action: str,
    package: str = "",
    x: int = 0,
    y: int = 0,
    direction: str = "up",
    distance: int = 500,
    text: str = "",
    clear_first: bool = True,
    user_id: str = "",
) -> str:
    """控制指定 Android 设备执行 UI 动作：启动/停止 App、点击坐标、长按、滑动、返回、输入文本、读取当前前台；每次返回 package/activity 用于判断页面是否跳转。
    Args:
        serial: 设备序列号（先 list_devices 查询）
        action: 动作类型: start_app/stop_app/click/long_click/swipe/back/input_text/current
        package: start_app/stop_app 时的包名
        x: 点击/输入坐标 x（像素）
        y: 点击/输入坐标 y（像素）
        direction: swipe 方向: up/down/left/right，默认 up
        distance: swipe 距离，默认 500
        text: input_text 的文本
        clear_first: input_text 前是否清空，默认 True
    """
    from apps.device_pool.api import device_action as _f

    return _jsonable(
        _f(
            serial=serial,
            action=action,
            package=package,
            x=x or None,
            y=y or None,
            direction=direction,
            distance=distance,
            text=text,
            clear_first=bool(clear_first),
        )
    )


def click_ratio(serial: str, nx: float, ny: float, user_id: str = "") -> str:
    """按归一化坐标点击（视觉模型看图后输出相对位置，工具换算成屏幕像素坐标）。
    Args:
        serial: 设备序列号
        nx: 横向相对位置 0~1（0=最左，1=最右）
        ny: 纵向相对位置 0~1（0=最上，1=最下）
    """
    from apps.device_pool.api import device_action as _action
    from apps.device_pool.api import use_device
    from apps.device_pool.pool import device as _device

    use_device(serial)
    info = _device.info()
    w = int(info.get("displayWidth", 0) or 1440)
    h = int(info.get("displayHeight", 0) or 3040)
    x = int(float(nx) * w)
    y = int(float(ny) * h)
    return _jsonable(_action(serial=serial, action="click", x=x, y=y))


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
    from apps.device_pool.api import device_action as _action
    from apps.device_pool.api import use_device
    from apps.device_pool.pool import device as _device

    use_device(serial)
    info = _device.info()
    w = int(info.get("displayWidth", 0) or 1440)
    h = int(info.get("displayHeight", 0) or 3040)
    x1 = int(float(nx1) * w)
    y1 = int(float(ny1) * h)
    x2 = int(float(nx2) * w)
    y2 = int(float(ny2) * h)
    return _jsonable(_action(serial=serial, action="drag", x=x1, y=y1, x2=x2, y2=y2))


def list_apps(serial: str, query: str = "", user_id: str = "") -> str:
    """列出设备已安装的应用包名（供获取被测 App 包名）。
    Args:
        serial: 设备序列号
        query: 包名关键词过滤
    """
    from apps.device_pool.api import list_apps as _f

    return _jsonable(_f(serial=serial, query=query or ""))


# ═══════════════════════════════════════════════════════════════════
# 设备检查器工具
# ═══════════════════════════════════════════════════════════════════


def capture_page(serial: str, method: str = "both", user_id: str = "") -> str:
    """抓取设备当前页面结构（JSON 元素 + 文本），并落库快照。
    Args:
        serial: 设备序列号
        method: 抓取方式: dump/both，默认 both
    """
    from apps.device_inspector.api import capture_snapshot

    data = capture_snapshot(user_id=user_id, serial=serial, method=method)
    actionable = data.get("actionable") or []
    texts = [
        {k: v for k, v in t.items() if k in ("text", "confidence", "x", "y", "width", "height")}
        for t in (data.get("texts") or [])
    ]
    trimmed = {
        "snapshot_id": data.get("snapshot_id"),
        "serial": data.get("serial"),
        "method": data.get("method"),
        "package": data.get("package"),
        "activity": data.get("activity"),
        "element_count": data.get("element_count"),
        "actionable_count": data.get("actionable_count"),
        "actionable": actionable[:50],
        "ocr_count": data.get("ocr_count"),
        "texts": texts[:50],
        "screenshot_path": data.get("screenshot_path"),
    }
    return _jsonable(trimmed)


def save_page_to_elements(
    snapshot_id: int,
    page_label: str,
    folder_path: str = "",
    include_ocr: bool = True,
    aliases: dict | None = None,
    user_id: str = "",
) -> str:
    """基于页面快照，按自定义目录/页面名写入元素定位。
    Args:
        snapshot_id: 快照ID
        page_label: 页面名称
        folder_path: 目录路径
        include_ocr: 是否包含 OCR 文本
        aliases: 元素别名
    """
    from apps.device_inspector.api import save_snapshot_to_elements

    return _jsonable(
        save_snapshot_to_elements(
            snapshot_id=int(snapshot_id),
            page_label=page_label,
            folder_path=folder_path,
            include_ocr=bool(include_ocr),
            aliases=aliases or None,
        )
    )


def screenshot_page(serial: str, user_id: str = "") -> ToolChunk:
    """截取设备当前屏幕并返回图片（给视觉模型看图）。轻量：仅校验设备 + 截图，不 dump/OCR/落库。
    Args:
        serial: 设备序列号
    """
    import base64
    import io as _io

    from pathlib import Path

    from django.conf import settings
    from PIL import Image

    from apps.device_inspector.api import capture_screen

    data = capture_screen(serial)
    shot_rel = data.get("screenshot_path") or ""
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
    return ToolChunk(
        content=[
            TextBlock(text=json.dumps(summary, ensure_ascii=False, default=str)),
            DataBlock(source=Base64Source(data=img_b64, media_type="image/jpeg")),
        ]
    )


def analyze_page(serial: str = "", snapshot_id: int = 0, user_id: str = "") -> str:
    """抓取并分析页面结构：分区 + 元素功能名 + XPath + 页面意图（纯规则，无 LLM）。
    Args:
        serial: 设备序列号（与 snapshot_id 二选一）
        snapshot_id: 已有快照ID（优先）
    """
    if not serial and not snapshot_id:
        raise ValueError("缺少必填参数: serial 或 snapshot_id")
    from apps.device_inspector.api import analyze_snapshot, capture_snapshot

    if snapshot_id:
        sid = int(snapshot_id)
        data = analyze_snapshot(sid)
        if data is None:
            raise ValueError(f"快照不存在: {snapshot_id}")
    else:
        cap = capture_snapshot(user_id=user_id, serial=serial, method="dump")
        sid = cap["snapshot_id"]
        data = analyze_snapshot(sid)
    data["snapshot_id"] = sid
    return _jsonable(data)


def save_page_semantic(
    snapshot_id: int,
    page_summary: str = "",
    elements: list | None = None,
    cards: list | None = None,
    user_id: str = "",
) -> str:
    """提交页面语义命名（校验防幻觉，回填 func_name 到规则骨架元素）。
    Args:
        snapshot_id: 快照ID
        page_summary: 页面意图一句话
        elements: 元素语义命名列表
        cards: 卡片结构
    """
    from apps.device_inspector.api import analyze_snapshot

    from .llm_semantic import validate_semantic

    sid = int(snapshot_id)
    data = analyze_snapshot(sid)
    if data is None:
        raise ValueError(f"快照不存在: {snapshot_id}")

    semantic = validate_semantic(
        {"page_summary": page_summary, "elements": elements or [], "cards": cards or []},
        data.get("elements", []),
    )
    by_rid = {e["resource_id"]: e.get("func_name", "") for e in semantic["elements"]}
    for el in data.get("elements", []):
        rid = el.get("resource_id", "")
        if rid in by_rid:
            el["func_name"] = by_rid[rid]
    data["page_summary"] = semantic["page_summary"]
    data["cards"] = semantic["cards"]
    data["snapshot_id"] = sid
    return _jsonable(data)


# ═══════════════════════════════════════════════════════════════════
# 元素定位工具
# ═══════════════════════════════════════════════════════════════════


def search_elements(query: str, limit: int = 20, user_id: str = "") -> str:
    """按关键词搜索页面元素（文本/类名/resource_id/页面名）。
    Args:
        query: 搜索关键词
        limit: 最多返回条数
    """
    from django.db.models import Q

    from apps.element_locator.models import Element

    qs = Element.objects.select_related("page")
    if query:
        qs = qs.filter(
            Q(text_val__icontains=query)
            | Q(class_name__icontains=query)
            | Q(resource_id__icontains=query)
            | Q(page__label__icontains=query)
        )
    return _jsonable(list(qs[:limit]))


def list_pages(limit: int = 30, user_id: str = "") -> str:
    """列出元素定位中的页面列表。
    Args:
        limit: 最多返回条数
    """
    from apps.element_locator.models import Page

    qs = Page.objects.filter(is_folder=False).order_by("-created_at")
    return _jsonable(list(qs[:limit]))


def fetch_page_elements(
    page_id: int = 0, page_label: str = "", limit: int = 30, user_id: str = ""
) -> str:
    """按页面ID或页面名获取其下元素。
    Args:
        page_id: 页面ID
        page_label: 页面名称
        limit: 最多返回条数
    """
    from apps.element_locator.models import Element, Page

    qs = Element.objects.select_related("page")
    if page_id:
        qs = qs.filter(page_id=page_id)
    elif page_label:
        page = Page.objects.filter(label=page_label).first()
        if page:
            qs = qs.filter(page_id=page.id)
    return _jsonable(list(qs[:limit]))


def list_web_groups(limit: int = 50, user_id: str = "") -> str:
    """列出 Web 元素分组。
    Args:
        limit: 最多返回条数
    """
    from apps.element_locator.models import WebGroup

    return _jsonable(list(WebGroup.objects.order_by("sort_order", "name")[:limit]))


def search_web_elements(query: str = "", limit: int = 20, user_id: str = "") -> str:
    """按关键词搜索 Web 元素。
    Args:
        query: 搜索关键词
        limit: 最多返回条数
    """
    from django.db.models import Q

    from apps.element_locator.models import WebElement

    qs = WebElement.objects.select_related("group")
    if query:
        qs = qs.filter(
            Q(name__icontains=query)
            | Q(locator_value__icontains=query)
            | Q(page_url__icontains=query)
            | Q(description__icontains=query)
            | Q(tags__icontains=query)
        )
    return _jsonable(list(qs.order_by("name")[:limit]))


def list_api_groups(limit: int = 50, user_id: str = "") -> str:
    """列出 API 分组。
    Args:
        limit: 最多返回条数
    """
    from apps.element_locator.models import ApiGroup

    return _jsonable(list(ApiGroup.objects.order_by("sort_order", "name")[:limit]))


def search_api_endpoints(
    query: str = "", method: str = "", limit: int = 20, user_id: str = ""
) -> str:
    """按关键词搜索 API 端点。
    Args:
        query: 搜索关键词
        method: HTTP 方法过滤
        limit: 最多返回条数
    """
    from django.db.models import Q

    from apps.element_locator.models import ApiEndpoint

    qs = ApiEndpoint.objects.select_related("group")
    if query:
        qs = qs.filter(
            Q(name__icontains=query)
            | Q(url__icontains=query)
            | Q(description__icontains=query)
            | Q(tags__icontains=query)
        )
    if method:
        qs = qs.filter(method__iexact=method)
    return _jsonable(list(qs.order_by("name")[:limit]))


def create_page_flow(
    from_page_id: int,
    to_page_id: int,
    trigger_element_id: int = 0,
    trigger_action: str = "click",
    user_id: str = "",
) -> str:
    """幂等建立页面跳转关系（页面流）。
    Args:
        from_page_id: 起始页面 ID
        to_page_id: 目标页面 ID
        trigger_element_id: 触发元素 ID
        trigger_action: 触发动作，默认 click
    """
    from apps.element_locator.api import get_or_create_flow

    flow, created = get_or_create_flow(
        from_page_id=int(from_page_id),
        to_page_id=int(to_page_id),
        trigger_element_id=int(trigger_element_id) if trigger_element_id else None,
        trigger_action=trigger_action or "click",
    )
    return json.dumps({"flow_id": flow.id, "created": created}, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════════
# 用例管理工具
# ═══════════════════════════════════════════════════════════════════


def save_case(
    case_id: str,
    title: str,
    case_type: str = "ui_automation",
    steps: list | None = None,
    directory_id: int = 0,
    package_name: str = "",
    enabled: bool = True,
    priority: str = "P1",
    user_id: str = "",
) -> str:
    """保存一条测试用例定义。
    Args:
        case_id: 用例ID
        title: 用例名称
        case_type: 用例类型，默认 ui_automation
        steps: 步骤列表
        directory_id: 目录ID
        package_name: 包名
        enabled: 是否启用
        priority: 优先级，默认 P1
    """
    from apps.case_manager.api import save_ai_definition
    from shared.users import resolve_username

    ok, payload = save_ai_definition(
        case_id=case_id,
        title=title,
        case_type=case_type or "ui_automation",
        steps=steps or [],
        directory_id=directory_id or None,
        package_name=package_name,
        enabled=bool(enabled),
        priority=priority,
        created_by=resolve_username(user_id),
    )
    if not ok:
        raise ValueError(payload)
    return _jsonable(payload)


def save_api_test_case(case_id: str, config_json: dict, user_id: str = "") -> str:
    """把完整 config_json 写入一条 API 测试用例。
    Args:
        case_id: 用例ID
        config_json: 配置 JSON
    """
    from apps.case_manager.api_api import save_api_definition
    from shared.users import resolve_username

    return _jsonable(
        save_api_definition(
            case_id=case_id,
            config_json=config_json,
            created_by=resolve_username(user_id),
        )
    )


def get_case(case_id: str, user_id: str = "") -> str:
    """按 ID 获取用例定义的结构化 digest。
    Args:
        case_id: 用例ID
    """
    from apps.case_manager.api import get_case_digest

    data = get_case_digest(case_id)
    if data is None:
        raise ValueError(f"用例不存在: {case_id}")
    return _jsonable(data)


def debug_case(case_id: str, case_type: str = "ui_automation", user_id: str = "") -> str:
    """按 ID 获取用例详情（调试用）。
    Args:
        case_id: 用例ID
        case_type: 用例类型，默认 ui_automation
    """
    from apps.case_manager.models import TestDefinition
    from apps.case_manager.models_api import ApiTestCase
    from apps.case_manager.models_storage import StorageTestCase
    from apps.case_manager.models_web import WebTestCase

    model_map = {
        "ui_automation": TestDefinition,
        "storage": StorageTestCase,
        "api_testing": ApiTestCase,
        "web_automation": WebTestCase,
    }
    model = model_map.get(case_type, TestDefinition)
    obj = model.objects.filter(id=case_id).select_related("directory").first()
    return _jsonable(obj) if obj else "{}"


def list_case_directories(case_type: str = "", user_id: str = "") -> str:
    """列出用例目录。
    Args:
        case_type: 用例类型过滤
    """
    from apps.case_manager.models import CaseDirectory

    qs = CaseDirectory.objects.order_by("sort_order", "name")
    if case_type:
        qs = qs.filter(case_type=case_type)
    return _jsonable(list(qs))


def search_cases(
    query: str = "", case_type: str = "", directory_id: int = 0, limit: int = 20, user_id: str = ""
) -> str:
    """按关键词搜索测试用例。
    Args:
        query: 搜索关键词
        case_type: 用例类型
        directory_id: 目录ID
        limit: 最多返回条数，默认20
    """
    from django.db.models import Q

    from apps.case_manager.models import TestDefinition
    from apps.case_manager.models_api import ApiTestCase
    from apps.case_manager.models_storage import StorageTestCase
    from apps.case_manager.models_web import WebTestCase

    models = {
        "ui_automation": TestDefinition,
        "storage": StorageTestCase,
        "api_testing": ApiTestCase,
        "web_automation": WebTestCase,
    }
    types = [case_type] if case_type in models else list(models)
    rows = []
    for ct in types:
        qs = models[ct].objects.select_related("directory")
        if query:
            qs = qs.filter(Q(title__icontains=query) | Q(id__icontains=query))
        if directory_id:
            qs = qs.filter(directory_id=directory_id)
        for obj in qs.order_by("-updated_at")[:limit]:
            directory = getattr(getattr(obj, "directory", None), "name", "") or ""
            rows.append(
                {
                    "id": getattr(obj, "id", ""),
                    "title": getattr(obj, "title", ""),
                    "case_type": ct,
                    "directory": directory,
                    "priority": getattr(obj, "priority", "") or "",
                }
            )
    rows.sort(key=lambda r: r.get("updated_at") or "", reverse=True)
    return _jsonable(rows[:limit])


# ═══════════════════════════════════════════════════════════════════
# 测试执行工具
# ═══════════════════════════════════════════════════════════════════


def run_test(run_id: str, serial: str, case_ids: list, user_id: str = "") -> str:
    """在指定设备上执行一组测试用例。
    Args:
        run_id: 运行ID
        serial: 设备序列号
        case_ids: 用例ID列表
    """
    from apps.test_runner.api import start_run

    return _jsonable(
        start_run(
            run_id=run_id, serial=serial, case_ids=case_ids, user_id=str(user_id), loop_count=1
        )
    )


def get_run_results(run_id: str, user_id: str = "") -> str:
    """获取一次运行的完整结果（状态 + 用例结果）。
    Args:
        run_id: 运行ID
    """
    from apps.test_runner.api import get_run_results, get_run_status

    run_status = get_run_status(run_id)
    if run_status is None:
        raise ValueError(f"run 不存在: {run_id}")
    return _jsonable({"run_status": run_status, "results": get_run_results(run_id)})


def get_run_status(run_id: str, user_id: str = "") -> str:
    """查询一次运行的状态（状态/设备/用例快照/结果计数）。
    Args:
        run_id: 运行ID
    """
    from apps.test_runner.api import get_run_status

    data = get_run_status(run_id)
    if data is None:
        raise ValueError(f"run 不存在: {run_id}")
    return _jsonable(data)


def stop_run(run_id: str, user_id: str = "") -> str:
    """停止一次正在执行的运行。
    Args:
        run_id: 运行ID
    """
    from apps.test_runner.api import stop_run

    return _jsonable(stop_run(run_id))


def sleep(seconds: int, user_id: str = "") -> str:
    """暂停等待（1-30 秒），供 AI 轮询异步任务前主动等待。
    Args:
        seconds: 等待秒数，1-30
    """
    import time

    n = max(1, min(int(seconds), 30))
    time.sleep(n)
    return json.dumps({"slept_seconds": n}, ensure_ascii=False)


# ═══════════════════════════════════════════════════════════════════
# 工作流工具
# ═══════════════════════════════════════════════════════════════════


def list_page_flows(
    query: str = "", directory_id: int = 0, limit: int = 20, user_id: str = ""
) -> str:
    """列出页面流文档。
    Args:
        query: 搜索关键词
        directory_id: 目录ID
        limit: 最多返回条数
    """
    from apps.workflow.api import list_document_summaries

    return _jsonable(list_document_summaries(query=query, directory_id=directory_id, limit=limit))


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


def save_page_flow(
    title: str,
    start_package: str = "",
    pages: list | None = None,
    edges: list | None = None,
    directory_id: int = 0,
    user_id: str = "",
) -> str:
    """受控写图：结构化页面关系 → 生成页面流文档。
    Args:
        title: 页面流标题
        start_package: 起始包名
        pages: 页面列表
        edges: 页面关系边
        directory_id: 目录ID
    """
    from apps.workflow.api import build_page_flow_document

    if not pages:
        raise ValueError("缺少必填参数: pages")
    ok, payload, _status = build_page_flow_document(
        title=title,
        start_package=start_package or "",
        pages=pages or [],
        edges=edges or [],
        directory_id=int(directory_id) if directory_id else None,
    )
    if not ok:
        raise ValueError(payload)
    return _jsonable(payload)


# ═══════════════════════════════════════════════════════════════════
# 工具注册表：工具名 → (函数, is_read_only)
# ═══════════════════════════════════════════════════════════════════

# 设备管理类工具自动放行（不走 HITL）：acquire/release 是占用记账、device_action
# 是用户明确要求"控制设备"时的核心动作，均非需要逐次确认的危险操作。
AUTO_ALLOW_TOOLS = {
    "acquire_device",
    "release_device",
    "device_action",
    "click_ratio",
    "drag_ratio",
}

TOOLS: dict[str, tuple] = {
    # 设备管理
    "get_online_devices": (get_online_devices, True),
    "list_devices": (list_devices, True),
    "acquire_device": (acquire_device, False),
    "release_device": (release_device, False),
    "device_action": (device_action, False),
    "click_ratio": (click_ratio, False),
    "drag_ratio": (drag_ratio, False),
    "list_apps": (list_apps, True),
    # 设备检查器
    "capture_page": (capture_page, True),
    "save_page_to_elements": (save_page_to_elements, False),
    "screenshot_page": (screenshot_page, True),
    "analyze_page": (analyze_page, True),
    "save_page_semantic": (save_page_semantic, False),
    # 元素定位
    "search_elements": (search_elements, True),
    "list_pages": (list_pages, True),
    "fetch_page_elements": (fetch_page_elements, True),
    "list_web_groups": (list_web_groups, True),
    "search_web_elements": (search_web_elements, True),
    "list_api_groups": (list_api_groups, True),
    "search_api_endpoints": (search_api_endpoints, True),
    "create_page_flow": (create_page_flow, False),
    # 用例管理
    "save_case": (save_case, False),
    "get_case": (get_case, True),
    "save_api_test_case": (save_api_test_case, False),
    "debug_case": (debug_case, True),
    "list_case_directories": (list_case_directories, True),
    "search_cases": (search_cases, True),
    # 测试执行
    "run_test": (run_test, False),
    "get_run_results": (get_run_results, True),
    "get_run_status": (get_run_status, True),
    "stop_run": (stop_run, False),
    "sleep": (sleep, True),
    # 工作流
    "list_page_flows": (list_page_flows, True),
    "get_page_flow": (get_page_flow, True),
    "save_page_flow": (save_page_flow, False),
}


def build_toolkit(tool_names: list[str], user_id: str = "") -> Toolkit:
    """按工具名子集，从注册表取函数 → PlatformFunctionTool → Toolkit。"""
    tools = []
    for name in tool_names:
        func, read_only = TOOLS[name]
        tools.append(
            PlatformFunctionTool(
                func,
                user_id=user_id,
                is_read_only=read_only,
                auto_allow=name in AUTO_ALLOW_TOOLS,
                is_concurrency_safe=read_only,
            )
        )
    return Toolkit(tools=tools)


# ═══════════════════════════════════════════════════════════════════
# 工具分类元数据（供管理端 available-tools / 工具箱 / HTTP 网关）
# ═══════════════════════════════════════════════════════════════════

TOOL_CATEGORIES = [
    {"key": "设备管理", "icon": "📱", "color": "#6BCB77"},
    {"key": "设备检查器", "icon": "📸", "color": "#FFB5A7"},
    {"key": "元素定位", "icon": "🔍", "color": "#A78BFA"},
    {"key": "用例管理", "icon": "📋", "color": "#4ECDC4"},
    {"key": "测试执行", "icon": "▶️", "color": "#FFB5A7"},
    {"key": "工作流", "icon": "🧭", "color": "#38BDF8"},
]

_CATEGORY_ICON = {c["key"]: c["icon"] for c in TOOL_CATEGORIES}

# 工具名 → (分类, module, action)
TOOL_META: dict[str, tuple[str, str, str]] = {
    "get_online_devices": ("设备管理", "devices", "list_online"),
    "list_devices": ("设备管理", "devices", "list_all"),
    "acquire_device": ("设备管理", "devices", "acquire"),
    "release_device": ("设备管理", "devices", "release"),
    "device_action": ("设备管理", "devices", "action"),
    "click_ratio": ("设备管理", "devices", "click_ratio"),
    "drag_ratio": ("设备管理", "devices", "drag_ratio"),
    "list_apps": ("设备管理", "devices", "list_apps"),
    "capture_page": ("设备检查器", "inspector", "capture"),
    "save_page_to_elements": ("设备检查器", "inspector", "save_elements"),
    "screenshot_page": ("设备检查器", "inspector", "screenshot"),
    "analyze_page": ("设备检查器", "inspector", "analyze"),
    "save_page_semantic": ("设备检查器", "inspector", "save_semantic"),
    "search_elements": ("元素定位", "elements", "search"),
    "list_pages": ("元素定位", "elements", "list_pages"),
    "fetch_page_elements": ("元素定位", "elements", "fetch_page_elements"),
    "list_web_groups": ("元素定位", "elements", "list_web_groups"),
    "search_web_elements": ("元素定位", "elements", "search_web"),
    "list_api_groups": ("元素定位", "elements", "list_api_groups"),
    "search_api_endpoints": ("元素定位", "elements", "search_endpoints"),
    "create_page_flow": ("元素定位", "elements", "upsert_flow"),
    "save_case": ("用例管理", "cases", "save_definition"),
    "get_case": ("用例管理", "cases", "get_definition"),
    "save_api_test_case": ("用例管理", "cases", "save_api_config"),
    "debug_case": ("用例管理", "cases", "get_case_detail"),
    "list_case_directories": ("用例管理", "cases", "list_directories"),
    "search_cases": ("用例管理", "cases", "search"),
    "run_test": ("测试执行", "runner", "run_test"),
    "get_run_results": ("测试执行", "runner", "get_run_results"),
    "get_run_status": ("测试执行", "runner", "get_run_status"),
    "stop_run": ("测试执行", "runner", "stop_run"),
    "sleep": ("测试执行", "common", "sleep"),
    "list_page_flows": ("工作流", "workflow", "list_page_flows"),
    "get_page_flow": ("工作流", "workflow", "get_page_flow"),
    "save_page_flow": ("工作流", "workflow", "save_page_flow"),
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


# ── 工具子集（供各智能体装配）──

VISION_TOOLS = [
    # 设备管理
    "get_online_devices",
    "list_devices",
    "acquire_device",
    "release_device",
    "device_action",
    "click_ratio",
    "drag_ratio",
    "list_apps",
    # 设备检查器
    "capture_page",
    "screenshot_page",
    "analyze_page",
    "save_page_to_elements",
    "save_page_semantic",
]

# 验收模型工具：截图二次确认 + 页面分析
VERIFIER_TOOLS = ["screenshot_page", "analyze_page"]

REASONING_TOOLS = [
    # 元素定位
    "search_elements",
    "list_pages",
    "fetch_page_elements",
    "list_web_groups",
    "search_web_elements",
    "list_api_groups",
    "search_api_endpoints",
    "create_page_flow",
    # 用例管理
    "save_case",
    "get_case",
    "save_api_test_case",
    "debug_case",
    "list_case_directories",
    "search_cases",
    # 测试执行
    "run_test",
    "get_run_results",
    "get_run_status",
    "stop_run",
    "sleep",
    # 工作流
    "list_page_flows",
    "get_page_flow",
    "save_page_flow",
]
