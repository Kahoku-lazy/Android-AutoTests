"""Tool registry — the SINGLE source of truth for all platform business tools.

This module replaces:
  - agentscope_service/tools/tools_config.json  (schema definitions)
  - agentscope_service/platform_client.py       (handler dispatch)

AgentScope calls Django via POST /api/tools/{module}/{action} with a JSON body.
The ToolGatewayView resolves (module, action) → handler → calls it → returns JSON.
"""

from __future__ import annotations

from typing import Any, Callable

# ═══════════════════════════════════════════════════════════════════
# Tool Schemas — same structure as the old tools_config.json.
# These are served at GET /api/tools/schemas so AgentScope can
# dynamically build PlatformTool classes at startup.
# ═══════════════════════════════════════════════════════════════════

TOOL_CATEGORIES = [
    {"key": "设备管理", "icon": "📱", "color": "#6BCB77"},
    {"key": "元素定位", "icon": "🔍", "color": "#A78BFA"},
    {"key": "用例管理", "icon": "📋", "color": "#4ECDC4"},
    {"key": "测试执行", "icon": "▶️", "color": "#FFB5A7"},
    {"key": "知识库", "icon": "📊", "color": "#7C6F83"},
]

TOOL_SCHEMAS: list[dict[str, Any]] = [
    # ── 设备管理 ──
    {
        "name": "get_online_devices",
        "category": "设备管理",
        "icon": "📱",
        "summary": "查询平台当前在线的 Android 设备列表",
        "module": "devices",
        "action": "list_online",
        "params": [],
        "read_only": True,
    },
    {
        "name": "acquire_device",
        "category": "设备管理",
        "icon": "📱",
        "summary": "锁定一台在线设备用于独占测试",
        "module": "devices",
        "action": "acquire",
        "params": [
            {"name": "serial", "type": "string", "required": True, "desc": "设备序列号"},
            {
                "name": "timeout",
                "type": "integer",
                "required": False,
                "desc": "锁定超时秒数，默认300",
            },
        ],
        "read_only": False,
    },
    {
        "name": "release_device",
        "category": "设备管理",
        "icon": "📱",
        "summary": "释放已锁定的设备回设备池",
        "module": "devices",
        "action": "release",
        "params": [
            {"name": "serial", "type": "string", "required": True, "desc": "设备序列号"},
            {"name": "reason", "type": "string", "required": False, "desc": "释放原因"},
        ],
        "read_only": False,
    },
    # ── 元素定位 ──
    {
        "name": "search_elements",
        "category": "元素定位",
        "icon": "🔍",
        "summary": "搜索 Android UI 元素，返回 XPath 定位器",
        "module": "elements",
        "action": "search",
        "params": [
            {"name": "query", "type": "string", "required": True, "desc": "搜索关键词"},
            {"name": "limit", "type": "integer", "required": False, "desc": "最多返回条数"},
        ],
        "read_only": True,
    },
    {
        "name": "list_pages",
        "category": "元素定位",
        "icon": "🔍",
        "summary": "列出平台上已录制的所有页面",
        "module": "elements",
        "action": "list_pages",
        "params": [],
        "read_only": True,
    },
    {
        "name": "fetch_page_elements",
        "category": "元素定位",
        "icon": "🔍",
        "summary": "获取指定页面上所有元素及其 XPath",
        "module": "elements",
        "action": "fetch_page_elements",
        "params": [
            {"name": "page_id", "type": "integer", "required": False, "desc": "页面ID"},
            {"name": "page_label", "type": "string", "required": False, "desc": "页面名称"},
        ],
        "read_only": True,
    },
    # ── 用例管理 ──
    {
        "name": "save_case",
        "category": "用例管理",
        "icon": "📋",
        "summary": "创建或更新测试用例 (支持 UI/Storage/API/Web 四种类型)",
        "module": "cases",
        "action": "save_definition",
        "params": [
            {"name": "case_id", "type": "string", "required": True, "desc": "用例ID"},
            {"name": "title", "type": "string", "required": True, "desc": "用例名称"},
            {
                "name": "case_type",
                "type": "string",
                "required": False,
                "desc": "用例类型: ui_automation/storage/api_testing/web_automation",
            },
            {"name": "steps", "type": "array", "required": True, "desc": "测试步骤列表"},
        ],
        "read_only": False,
    },
    {
        "name": "get_case",
        "category": "用例管理",
        "icon": "📋",
        "summary": "获取测试用例完整详情",
        "module": "cases",
        "action": "get_definition",
        "params": [
            {"name": "case_id", "type": "string", "required": True, "desc": "用例ID"},
        ],
        "read_only": True,
    },
    {
        "name": "save_api_test_case",
        "category": "用例管理",
        "icon": "🌐",
        "summary": "创建或更新 API 测试用例（支持单接口 meta/request/cases 和多接口 case_info/steps/test_data 两种格式，自动探测）",
        "module": "cases",
        "action": "save_api_config",
        "params": [
            {
                "name": "case_id",
                "type": "string",
                "required": True,
                "desc": "用例ID（格式 API-YYYYMMDD-HHMMSS-XXXX）",
            },
            {
                "name": "config_json",
                "type": "object",
                "required": True,
                "desc": "完整 JSON 配置：单接口格式 meta/request/cases 或多接口格式 case_info/steps/test_data/validation",
            },
        ],
        "read_only": False,
    },
    {
        "name": "debug_case",
        "category": "用例管理",
        "icon": "📋",
        "summary": "检查用例的步骤和设备环境是否就绪",
        "module": "cases",
        "action": "get_case_detail",
        "params": [
            {"name": "case_id", "type": "string", "required": True, "desc": "用例ID"},
        ],
        "read_only": True,
    },
    # ── 测试执行 ──
    {
        "name": "run_test",
        "category": "测试执行",
        "icon": "▶️",
        "summary": "在指定设备上执行测试用例",
        "module": "runner",
        "action": "run_test",
        "params": [
            {"name": "run_id", "type": "string", "required": True, "desc": "运行ID"},
            {
                "name": "serial",
                "type": "string",
                "required": True,
                "desc": "设备序列号(必须先acquire_device)",
            },
            {"name": "case_ids", "type": "array", "required": True, "desc": "用例ID列表"},
        ],
        "read_only": False,
    },
    {
        "name": "get_run_results",
        "category": "测试执行",
        "icon": "▶️",
        "summary": "获取测试执行的结果详情",
        "module": "runner",
        "action": "get_run_results",
        "params": [
            {"name": "run_id", "type": "string", "required": True, "desc": "运行ID"},
        ],
        "read_only": True,
    },
    {
        "name": "stop_run",
        "category": "测试执行",
        "icon": "▶️",
        "summary": "停止正在执行的测试",
        "module": "runner",
        "action": "stop_run",
        "params": [
            {"name": "run_id", "type": "string", "required": True, "desc": "运行ID"},
        ],
        "read_only": False,
    },
    # ── 知识库 ──
    {
        "name": "search_knowledge_base",
        "category": "知识库",
        "icon": "📊",
        "summary": "检索项目文档 (PRD、架构设计、报错手册等)",
        "module": "knowledge",
        "action": "search",
        "params": [
            {"name": "query", "type": "string", "required": True, "desc": "搜索关键词"},
        ],
        "read_only": True,
    },
]

# ═══════════════════════════════════════════════════════════════════
# Tool Handler Registry — (module, action) → handler function
#
# Each handler signature: handler(user_id: str, **kwargs) → dict | list | str | bool
# The ToolGatewayView extracts user_id from JWT and passes it as keyword.
# ═══════════════════════════════════════════════════════════════════

Handler = Callable[..., Any]
_TOOL_HANDLERS: dict[tuple[str, str], Handler] = {}

PROTECTED = object()  # sentinel for missing required params


def _register(module: str, action: str):
    """Decorator: register a handler for (module, action)."""

    def decorator(func: Handler) -> Handler:
        _TOOL_HANDLERS[(module, action)] = func
        return func

    return decorator


def resolve(module: str, action: str) -> Handler | None:
    """Look up the handler for (module, action). Returns None if not found."""
    return _TOOL_HANDLERS.get((module, action))


# ── Device handlers ──


@_register("devices", "list_online")
def _devices_list_online(user_id: str, **kwargs):
    from apps.device_pool.api import get_online_devices

    return get_online_devices()


@_register("devices", "acquire")
def _devices_acquire(user_id: str, serial: str = PROTECTED, timeout: int = 300, **kwargs):
    if serial is PROTECTED:
        raise ValueError("缺少必填参数: serial")
    from apps.device_pool.api import acquire_device

    return acquire_device(serial, user_id=int(user_id), timeout=timeout)


@_register("devices", "release")
def _devices_release(user_id: str, serial: str = PROTECTED, reason: str = "manual", **kwargs):
    if serial is PROTECTED:
        raise ValueError("缺少必填参数: serial")
    from apps.device_pool.api import release_device

    return release_device(serial, reason=reason)


# ── Element handlers ──


@_register("elements", "search")
def _elements_search(user_id: str, query: str = "", limit: int = 20, **kwargs):
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
    return list(qs[:limit])


@_register("elements", "list_pages")
def _elements_list_pages(user_id: str, limit: int = 30, **kwargs):
    from apps.element_locator.models import Page

    qs = Page.objects.filter(is_folder=False).order_by("-updated_at")
    return list(qs[:limit])


@_register("elements", "fetch_page_elements")
def _elements_fetch_page_elements(
    user_id: str, page_id=None, page_label=None, limit: int = 30, **kwargs
):
    from apps.element_locator.models import Element, Page

    qs = Element.objects.select_related("page")
    if page_id:
        qs = qs.filter(page_id=page_id)
    elif page_label:
        page = Page.objects.filter(label=page_label).first()
        if page:
            qs = qs.filter(page_id=page.id)
    return list(qs[:limit])


# ── Case handlers ──


@_register("cases", "save_definition")
def _cases_save_definition(
    user_id: str,
    case_id: str = PROTECTED,
    title: str = "",
    case_type: str = "",
    steps=None,
    **kwargs,
):
    if case_id is PROTECTED:
        raise ValueError("缺少必填参数: case_id")

    ct = case_type or "ui_automation"
    filtered_kwargs = {k: v for k, v in kwargs.items() if k not in ("user_id",)}

    if ct == "api_testing":
        raise ValueError(
            "API 测试用例请使用 save_api_test_case 工具，"
            "传入完整的 config_json（含 case_info/steps/test_data/validation 四个模块）"
        )
    elif ct == "storage":
        from apps.case_manager.api import save_storage_definition

        return save_storage_definition(
            case_id=case_id, title=title, case_type=ct, steps=steps or [], **filtered_kwargs
        )
    elif ct == "web_automation":
        from apps.case_manager.api import save_web_definition

        return save_web_definition(
            case_id=case_id, title=title, case_type=ct, steps=steps or [], **filtered_kwargs
        )
    else:
        from apps.case_manager.api import save_definition

        return save_definition(
            case_id=case_id, title=title, case_type=ct, steps=steps or [], **filtered_kwargs
        )


@_register("cases", "save_api_config")
def _cases_save_api_config(
    user_id: str,
    case_id: str = PROTECTED,
    config_json: dict = PROTECTED,
    **kwargs,
):
    """AI writes complete config_json to an API test case."""
    if case_id is PROTECTED:
        raise ValueError("缺少必填参数: case_id")
    if config_json is PROTECTED:
        raise ValueError("缺少必填参数: config_json")
    from apps.case_manager.api_api import save_api_definition

    return save_api_definition(case_id=case_id, config_json=config_json, **kwargs)


@_register("cases", "get_definition")
def _cases_get_definition(user_id: str, case_id: str = PROTECTED, **kwargs):
    if case_id is PROTECTED:
        raise ValueError("缺少必填参数: case_id")
    from apps.case_manager.api_lock import find_case_across_types

    obj, _ = find_case_across_types(case_id)
    return obj


@_register("cases", "get_case_detail")
def _cases_get_case_detail(
    user_id: str, case_id: str = PROTECTED, case_type: str = "ui_automation", **kwargs
):
    if case_id is PROTECTED:
        raise ValueError("缺少必填参数: case_id")
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
    return model.objects.filter(id=case_id).select_related("directory").first()


# ── Runner handlers ──


@_register("runner", "run_test")
def _runner_run_test(
    user_id: str, run_id: str = PROTECTED, serial: str = PROTECTED, case_ids=None, **kwargs
):
    if run_id is PROTECTED:
        raise ValueError("缺少必填参数: run_id")
    if serial is PROTECTED:
        raise ValueError("缺少必填参数: serial")
    if not case_ids:
        raise ValueError("缺少必填参数: case_ids")
    from apps.test_runner.api import start_run

    return start_run(
        run_id=run_id,
        serial=serial,
        case_ids=case_ids,
        user_id=str(user_id),
        loop_count=1,
    )


@_register("runner", "get_run_results")
def _runner_get_run_results(user_id: str, run_id: str = PROTECTED, **kwargs):
    if run_id is PROTECTED:
        raise ValueError("缺少必填参数: run_id")
    from apps.test_runner.api import get_run_results

    return get_run_results(run_id)


@_register("runner", "stop_run")
def _runner_stop_run(user_id: str, run_id: str = PROTECTED, **kwargs):
    if run_id is PROTECTED:
        raise ValueError("缺少必填参数: run_id")
    from apps.test_runner.api import stop_run

    return stop_run(run_id)


# ── Knowledge handlers ──


@_register("knowledge", "search")
def _knowledge_search(user_id: str, query: str = "", sources: list | None = None, **kwargs):
    from .rag_service import search as kb_search

    return kb_search(query, top_k=5, sources=sources)
