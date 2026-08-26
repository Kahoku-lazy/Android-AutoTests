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
    {"key": "设备检查器", "icon": "📸", "color": "#FFB5A7"},
    {"key": "元素定位", "icon": "🔍", "color": "#A78BFA"},
    {"key": "用例管理", "icon": "📋", "color": "#4ECDC4"},
    {"key": "测试执行", "icon": "▶️", "color": "#FFB5A7"},
    {"key": "工作流", "icon": "🧭", "color": "#38BDF8"},
    {"key": "知识库", "icon": "📊", "color": "#7C6F83"},
]

TOOL_SCHEMAS: list[dict[str, Any]] = [
    # ── 设备管理 ──
    {
        "name": "get_online_devices",
        "category": "设备管理",
        "icon": "📱",
        "summary": "查询平台当前在线的 Android 设备列表（不含使用中设备；查看全部设备及状态请用 list_devices）",
        "module": "devices",
        "action": "list_online",
        "params": [],
        "read_only": True,
    },
    {
        "name": "list_devices",
        "category": "设备管理",
        "icon": "📱",
        "summary": "查询设备管理中的全部设备及状态（在线/使用中），含使用人、锁定人、剩余占用时间",
        "module": "devices",
        "action": "list_all",
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
    {
        "name": "device_action",
        "category": "设备管理",
        "icon": "🎮",
        "summary": "控制指定 Android 设备执行 UI 动作：启动/停止 App、点击坐标、长按、滑动、返回、输入文本、读取当前前台；每次返回 package/activity 用于判断页面是否跳转",
        "module": "devices",
        "action": "action",
        "params": [
            {
                "name": "serial",
                "type": "string",
                "required": True,
                "desc": "设备序列号（先 list_devices 查询）",
            },
            {
                "name": "action",
                "type": "string",
                "required": True,
                "desc": "动作类型: start_app/stop_app/click/long_click/swipe/back/input_text/current",
            },
            {
                "name": "package",
                "type": "string",
                "required": False,
                "desc": "start_app/stop_app 时的包名",
            },
            {"name": "x", "type": "integer", "required": False, "desc": "点击/输入坐标 x（像素）"},
            {"name": "y", "type": "integer", "required": False, "desc": "点击/输入坐标 y（像素）"},
            {
                "name": "direction",
                "type": "string",
                "required": False,
                "desc": "swipe 方向: up/down/left/right，默认 up",
            },
            {
                "name": "distance",
                "type": "integer",
                "required": False,
                "desc": "swipe 距离像素，默认 500",
            },
            {"name": "text", "type": "string", "required": False, "desc": "input_text 的文本"},
            {
                "name": "clear_first",
                "type": "boolean",
                "required": False,
                "desc": "input_text 前是否清空，默认 true",
            },
        ],
        "read_only": False,
    },
    {
        "name": "list_apps",
        "category": "设备管理",
        "icon": "📦",
        "summary": "列出设备已安装的包名（可按关键词过滤），用于获取被测 App 包名后再用 device_action(start_app) 启动",
        "module": "devices",
        "action": "list_apps",
        "params": [
            {
                "name": "serial",
                "type": "string",
                "required": True,
                "desc": "设备序列号（先 list_devices 查询）",
            },
            {
                "name": "query",
                "type": "string",
                "required": False,
                "desc": "包名关键词过滤（如 govee），留空返回全部",
            },
        ],
        "read_only": True,
    },
    # ── 设备检查器 ──
    {
        "name": "capture_page",
        "category": "设备检查器",
        "icon": "📸",
        "summary": "抓取指定设备当前页面（dump UI 层级/OCR 文字，可同时），返回解析 JSON 并落库为检查器快照；执行引擎占用中的设备不可用",
        "module": "inspector",
        "action": "capture",
        "params": [
            {
                "name": "serial",
                "type": "string",
                "required": True,
                "desc": "设备序列号（先 list_devices 查询）",
            },
            {
                "name": "method",
                "type": "string",
                "required": False,
                "desc": "获取方法: dump（UI 层级）/ ocr（屏幕文字）/ both（两者，默认）",
            },
        ],
        "read_only": True,
    },
    {
        "name": "save_page_to_elements",
        "category": "设备检查器",
        "icon": "📸",
        "summary": "把已抓取的检查器快照保存到元素定位（自定义目录与页面名称，目录不存在自动创建）",
        "module": "inspector",
        "action": "save_elements",
        "params": [
            {
                "name": "snapshot_id",
                "type": "integer",
                "required": True,
                "desc": "capture_page 返回的 snapshot_id",
            },
            {
                "name": "page_label",
                "type": "string",
                "required": True,
                "desc": "元素定位中的页面名称",
            },
            {
                "name": "folder_path",
                "type": "string",
                "required": False,
                "desc": "目标目录路径（如「登录模块/账号页」，用 / 分隔；不存在自动创建）",
            },
            {
                "name": "include_ocr",
                "type": "boolean",
                "required": False,
                "desc": "是否连同保存页面级 OCR 数据，默认 true",
            },
        ],
        "read_only": False,
    },
    {
        "name": "screenshot_page",
        "category": "设备检查器",
        "icon": "📸",
        "summary": "截取指定设备当前屏幕，返回截图图片（base64 PNG）供视觉模型直接查看，并落库检查器快照；执行引擎占用中的设备不可用",
        "module": "inspector",
        "action": "screenshot",
        "params": [
            {
                "name": "serial",
                "type": "string",
                "required": True,
                "desc": "设备序列号（先 list_devices 查询）",
            },
            {
                "name": "method",
                "type": "string",
                "required": False,
                "desc": "获取方法: dump（UI 层级）/ ocr（屏幕文字）/ both（两者，默认）",
            },
        ],
        "read_only": True,
    },
    {
        "name": "analyze_page",
        "category": "设备检查器",
        "icon": "📸",
        "summary": "抓取并分析页面结构（纯规则，无 LLM）：6层分区 + XPath + 交互指标；可对已有快照分析（snapshot_id）或抓取新快照（serial）。语义命名请先看返回的元素，再用 save_page_semantic 提交",
        "module": "inspector",
        "action": "analyze",
        "params": [
            {
                "name": "serial",
                "type": "string",
                "required": False,
                "desc": "设备序列号（与 snapshot_id 二选一，先 list_devices 查询）",
            },
            {
                "name": "snapshot_id",
                "type": "integer",
                "required": False,
                "desc": "已有快照ID（与 serial 二选一，优先 snapshot_id）",
            },
        ],
        "read_only": True,
    },
    {
        "name": "save_page_semantic",
        "category": "设备检查器",
        "icon": "📸",
        "summary": "提交页面结构分析的语义命名：给元素起中文功能名（func_name）、一句话页面意图（page_summary）、卡片角色（cards）；后端校验 resource_id 真实性防幻觉后合并到结构分析结果",
        "module": "inspector",
        "action": "save_semantic",
        "params": [
            {
                "name": "snapshot_id",
                "type": "integer",
                "required": True,
                "desc": "analyze_page 返回的 snapshot_id",
            },
            {
                "name": "page_summary",
                "type": "string",
                "required": False,
                "desc": "一句话页面意图总结",
            },
            {
                "name": "elements",
                "type": "array",
                "required": True,
                "desc": "元素语义命名列表，每项 {resource_id, func_name, metrics}；resource_id 必须来自 analyze_page 返回的元素，metrics 取值 可点击/可滚动/可勾选",
            },
            {
                "name": "cards",
                "type": "array",
                "required": False,
                "desc": "重复卡片结构列表，每项 {name, fields}",
            },
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
    {
        "name": "list_web_groups",
        "category": "元素定位",
        "icon": "🔍",
        "summary": "列出 Web 元素管理的全部分组（项目/模块/页面目录树，含文件夹）",
        "module": "elements",
        "action": "list_web_groups",
        "params": [],
        "read_only": True,
    },
    {
        "name": "search_web_elements",
        "category": "元素定位",
        "icon": "🔍",
        "summary": "搜索 Web 元素管理中的元素（名称/定位表达式/页面URL/描述/标签），返回定位方式与定位表达式",
        "module": "elements",
        "action": "search_web",
        "params": [
            {
                "name": "query",
                "type": "string",
                "required": False,
                "desc": "搜索关键词，留空返回全部",
            },
            {"name": "limit", "type": "integer", "required": False, "desc": "最多返回条数"},
        ],
        "read_only": True,
    },
    {
        "name": "list_api_groups",
        "category": "元素定位",
        "icon": "🔍",
        "summary": "列出 API 接口管理的全部分组（项目/模块/接口目录树，含文件夹）",
        "module": "elements",
        "action": "list_api_groups",
        "params": [],
        "read_only": True,
    },
    {
        "name": "search_api_endpoints",
        "category": "元素定位",
        "icon": "🔍",
        "summary": "搜索 API 接口管理中的接口（名称/URL/描述/标签，可按方法过滤），返回请求方法与 URL",
        "module": "elements",
        "action": "search_endpoints",
        "params": [
            {
                "name": "query",
                "type": "string",
                "required": False,
                "desc": "搜索关键词，留空返回全部",
            },
            {
                "name": "method",
                "type": "string",
                "required": False,
                "desc": "按请求方法过滤: GET/POST/PUT/DELETE/PATCH",
            },
            {"name": "limit", "type": "integer", "required": False, "desc": "最多返回条数"},
        ],
        "read_only": True,
    },
    # ── 用例管理 ──
    {
        "name": "save_case",
        "category": "用例管理",
        "icon": "📋",
        "summary": "创建或更新测试用例（UI/Storage/Web 三种类型；API 类型请用 save_api_test_case）。UI/Web 的 steps 会写入可执行步骤（steps_json）并在落库前校验：步骤类型必须合法且与平台匹配、点击/等待类必须带 xpath、断言类必须带 expected_text、Web 操作必须带 selector/url。adb_start_app/adb_kill_app 的 xpath 承载包名且可为空（空则回退用例 package_name）",
        "module": "cases",
        "action": "save_definition",
        "params": [
            {
                "name": "case_id",
                "type": "string",
                "required": True,
                "desc": "用例ID（唯一，建议 TC-YYYYMMDD-HHMMSS-XXXX 格式）",
            },
            {"name": "title", "type": "string", "required": True, "desc": "用例名称"},
            {
                "name": "case_type",
                "type": "string",
                "required": False,
                "desc": "用例类型: ui_automation/storage/web_automation（默认 ui_automation；api_testing 用 save_api_test_case）",
            },
            {
                "name": "steps",
                "type": "array",
                "required": True,
                "desc": "测试步骤列表，每步 {type, xpath, expected_text, timeout, ...}；type 取值：click/long_click/wait/wait_disappear/verify_text/adb_start_app/adb_kill_app/adb_wait_toast/adb_perf_element_time/adb_if_appear/adb_if_disappear/adb_loop_n/adb_loop_elements/adb_poll_text/sleep/swipe/screenshot（Android）或 web_navigate/web_click/web_fill/web_type/web_assert/web_wait/web_screenshot（Web）",
            },
            {
                "name": "directory_id",
                "type": "integer",
                "required": False,
                "desc": "目录ID（先 list_case_directories 查询，留空为未分类）",
            },
            {
                "name": "package_name",
                "type": "string",
                "required": False,
                "desc": "被测 App 包名（UI 用例，如 com.taobao.taobao）",
            },
            {
                "name": "enabled",
                "type": "boolean",
                "required": False,
                "desc": "是否启用，默认 true（禁用的用例无法执行）",
            },
            {
                "name": "priority",
                "type": "string",
                "required": False,
                "desc": "优先级: P0/P1/P2，默认 P1",
            },
            {
                "name": "rows",
                "type": "array",
                "required": False,
                "desc": "数据行列表（仅 case_type=storage）",
            },
        ],
        "read_only": False,
    },
    {
        "name": "get_case",
        "category": "用例管理",
        "icon": "📋",
        "summary": "获取测试用例完整详情（结构化）：元信息（id/title/case_type/目录/优先级/enabled/package_name）+ steps 步骤数组（UI/Web，含 xpath/expected_text）或 config（API，四模块 JSON）或 rows（storage）",
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
    {
        "name": "list_case_directories",
        "category": "用例管理",
        "icon": "📋",
        "summary": "列出用例目录树（两级），可按用例类型过滤；拿到 directory_id 后可用 search_cases 查该目录下用例",
        "module": "cases",
        "action": "list_directories",
        "params": [
            {
                "name": "case_type",
                "type": "string",
                "required": False,
                "desc": "用例类型: ui_automation/storage/api_testing/web_automation，留空返回全部",
            },
        ],
        "read_only": True,
    },
    {
        "name": "search_cases",
        "category": "用例管理",
        "icon": "📋",
        "summary": "按标题/用例ID 搜索测试用例（跨 UI/Storage/API/Web 四类型），可叠加类型与目录过滤，返回精简列表；完整详情用 get_case",
        "module": "cases",
        "action": "search",
        "params": [
            {
                "name": "query",
                "type": "string",
                "required": False,
                "desc": "标题或用例ID 关键词，留空返回全部",
            },
            {
                "name": "case_type",
                "type": "string",
                "required": False,
                "desc": "用例类型: ui_automation/storage/api_testing/web_automation",
            },
            {
                "name": "directory_id",
                "type": "integer",
                "required": False,
                "desc": "目录ID（先 list_case_directories 查询）",
            },
            {"name": "limit", "type": "integer", "required": False, "desc": "最多返回条数，默认20"},
        ],
        "read_only": True,
    },
    # ── 测试执行 ──
    {
        "name": "run_test",
        "category": "测试执行",
        "icon": "▶️",
        "summary": "在指定设备上执行测试用例（工具会自行锁定并释放设备，无需先调用 acquire_device）。执行为异步投递：调用成功即已创建运行记录，随后用 get_run_status 查询进度（PENDING → RUNNING → completed/stopped/failed，failed 时 summary.error 为失败原因）；结果落库后用 get_run_results 取明细",
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
        "summary": "获取一次执行的完整反馈：run_status（状态/设备/计划用例/已完成结果数与汇总/起止时间）+ results 结果明细（每用例每轮的 pass/fail/时长/详情）。运行中时 results 为空但 run_status.status 为 RUNNING；run 不存在会报错",
        "module": "runner",
        "action": "get_run_results",
        "params": [
            {
                "name": "run_id",
                "type": "string",
                "required": True,
                "desc": "运行ID（run_test 创建时返回）",
            },
        ],
        "read_only": True,
    },
    {
        "name": "get_run_status",
        "category": "测试执行",
        "icon": "▶️",
        "summary": "查询一次执行运行的状态：pending（刚创建，正在连接设备）/running/completed/stopped/failed、设备、计划用例快照、已完成结果条数与汇总（通过/失败/通过率）、起止时间。执行通常需要 30-60 秒——运行中禁止连续查询，两次查询之间必须用 sleep 工具等待 10 秒。运行中时 result_count 为 0（结果在整轮结束后才落库），结束后用 get_run_results 取明细；failed 时读 summary.error 获取具体失败原因",
        "module": "runner",
        "action": "get_run_status",
        "params": [
            {
                "name": "run_id",
                "type": "string",
                "required": True,
                "desc": "运行ID（run_test 创建时返回）",
            },
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
    {
        "name": "sleep",
        "category": "测试执行",
        "icon": "⏳",
        "summary": "暂停等待指定秒数（1-30 秒）。用于等待异步任务（如用例执行）后再查询状态，避免高频轮询",
        "module": "common",
        "action": "sleep",
        "params": [
            {"name": "seconds", "type": "integer", "required": True, "desc": "等待秒数，1-30"},
        ],
        "read_only": True,
    },
    # ── 工作流 ──
    {
        "name": "list_page_flows",
        "category": "工作流",
        "icon": "🧭",
        "summary": "列出工作流工作台的页面流文档（标题/doc_id 关键词搜索，可按目录过滤），返回 doc_id、标题、目录、节点/连线数与更新时间；单个文档的语义详情用 get_page_flow",
        "module": "workflow",
        "action": "list_page_flows",
        "params": [
            {
                "name": "query",
                "type": "string",
                "required": False,
                "desc": "标题或 doc_id 关键词，留空返回全部",
            },
            {
                "name": "directory_id",
                "type": "integer",
                "required": False,
                "desc": "目录ID，留空返回全部",
            },
            {"name": "limit", "type": "integer", "required": False, "desc": "最多返回条数，默认20"},
        ],
        "read_only": True,
    },
    {
        "name": "get_page_flow",
        "category": "工作流",
        "icon": "🧭",
        "summary": "读取页面流 doc_id 的语义摘要：节点（起点/页面/弹窗/API/终点）、页面间跳转关系 links、每页 navigation_entries（可点击元素与去向，含 XPath）、elements（页面下元素，source 标注 snapshot/web_snapshot/builtin_pool/unknown）、paths（起点到终点的路径文字描述）",
        "module": "workflow",
        "action": "get_page_flow",
        "params": [
            {
                "name": "doc_id",
                "type": "string",
                "required": True,
                "desc": "页面流文档ID（WF-PF-YYYYMMDD-HHMMSS-XXXX）",
            },
        ],
        "read_only": True,
    },
    # ── 知识库 ──
    {
        "name": "search_knowledge_base",
        "category": "知识库",
        "icon": "📊",
        "summary": "检索项目文档 (PRD、架构设计、报错手册等)；智能体配置的引用范围可为目录（dir:）或单文件（doc:），目录引用动态包含其下全部文件",
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


@_register("devices", "list_all")
def _devices_list_all(user_id: str, **kwargs):
    from apps.device_pool.api import list_devices

    return list_devices(user_id=user_id)


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


@_register("devices", "action")
def _devices_action(user_id: str, serial: str = PROTECTED, action: str = PROTECTED, **kwargs):
    """控制设备执行 UI 动作（写工具），返回当前前台 package/activity。"""
    if serial is PROTECTED:
        raise ValueError("缺少必填参数: serial")
    if action is PROTECTED:
        raise ValueError("缺少必填参数: action")
    from apps.device_pool.api import device_action

    clear_first = kwargs.get("clear_first", True)
    if isinstance(clear_first, str):
        # 网关/HTTP 直调可能传字符串布尔，防 "false"→True 误判
        clear_first = clear_first.strip().lower() in ("1", "true", "yes")

    return device_action(
        serial=serial,
        action=action,
        package=kwargs.get("package", ""),
        x=kwargs.get("x"),
        y=kwargs.get("y"),
        direction=kwargs.get("direction", "up"),
        distance=kwargs.get("distance", 500),
        text=kwargs.get("text", ""),
        clear_first=bool(clear_first),
    )


@_register("devices", "list_apps")
def _devices_list_apps(user_id: str, serial: str = PROTECTED, query: str = "", **kwargs):
    """列出设备已安装包名（只读，供获取被测 App 包名）。"""
    if serial is PROTECTED:
        raise ValueError("缺少必填参数: serial")
    from apps.device_pool.api import list_apps

    return list_apps(serial=serial, query=query or "")


# ── Inspector handlers ──


@_register("inspector", "capture")
def _inspector_capture(user_id: str, serial: str = PROTECTED, method: str = "both", **kwargs):
    if serial is PROTECTED:
        raise ValueError("缺少必填参数: serial")
    from apps.device_inspector.api import capture_snapshot

    data = capture_snapshot(user_id=user_id, serial=serial, method=method)
    return _trim_capture_for_ai(data)


@_register("inspector", "save_elements")
def _inspector_save_elements(
    user_id: str,
    snapshot_id: int = PROTECTED,
    page_label: str = PROTECTED,
    folder_path: str = "",
    include_ocr: bool = True,
    **kwargs,
):
    if snapshot_id is PROTECTED:
        raise ValueError("缺少必填参数: snapshot_id")
    if page_label is PROTECTED:
        raise ValueError("缺少必填参数: page_label")
    from apps.device_inspector.api import save_snapshot_to_elements

    return save_snapshot_to_elements(
        snapshot_id=int(snapshot_id),
        page_label=page_label,
        folder_path=folder_path,
        include_ocr=bool(include_ocr),
    )


@_register("inspector", "screenshot")
def _inspector_screenshot(user_id: str, serial: str = PROTECTED, method: str = "both", **kwargs):
    """截屏返回图片 + 摘要。复用检查器 capture 落库链路，读截图文件转 base64。

    返回 `{"text": {...}, "image": {"media_type", "data"}}` 的图片标记结构，
    由 in_process_tool._format_result 识别并构造多模态 ToolChunk。
    """
    if serial is PROTECTED:
        raise ValueError("缺少必填参数: serial")
    import base64
    import io as _io

    from pathlib import Path

    from django.conf import settings
    from PIL import Image

    from apps.device_inspector.api import capture_snapshot

    data = capture_snapshot(user_id=user_id, serial=serial, method=method or "both")
    shot_rel = data.get("screenshot_path") or ""
    if not shot_rel:
        raise ValueError("截屏失败：未获取到截图路径")
    shot_file = Path(settings.MEDIA_ROOT) / shot_rel
    if not shot_file.is_file():
        raise ValueError("截屏失败：截图文件不存在")
    # 降采样 + JPEG 压缩控制体积：AgentScope 对 base64 图片按 len(data)//4 计 token，
    # 默认 tool_result_limit=50000（≈150KB）会整体卸载原图（1440x3040 PNG 约 800KB）。
    _img = Image.open(_io.BytesIO(shot_file.read_bytes()))
    _img.thumbnail((1280, 1280))
    if _img.mode not in ("RGB", "L"):
        _img = _img.convert("RGB")
    _buf = _io.BytesIO()
    _img.save(_buf, format="JPEG", quality=85)
    img_b64 = base64.b64encode(_buf.getvalue()).decode("ascii")
    return {
        "text": {
            "snapshot_id": data.get("snapshot_id"),
            "serial": data.get("serial"),
            "package": data.get("package"),
            "activity": data.get("activity"),
            "screen_w": data.get("screen_w"),
            "screen_h": data.get("screen_h"),
            "element_count": data.get("element_count"),
            "ocr_count": data.get("ocr_count"),
        },
        "image": {"media_type": "image/jpeg", "data": img_b64},
    }


def _trim_capture_for_ai(data: dict) -> dict:
    """AI 通道裁剪：actionable 子集 + texts 去缩略图（控制 token，防 4000 截断）。"""
    actionable = data.get("actionable") or []
    texts = [
        {k: v for k, v in t.items() if k in ("text", "confidence", "x", "y", "width", "height")}
        for t in (data.get("texts") or [])
    ]
    return {
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


@_register("inspector", "analyze")
def _inspector_analyze(user_id: str, serial: str = "", snapshot_id=None, **kwargs):
    """页面结构分析：纯规则分区（无 LLM）。语义命名由 Agent 经 save_semantic 提交。"""
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
    return data


@_register("inspector", "save_semantic")
def _inspector_save_semantic(
    user_id: str,
    snapshot_id=PROTECTED,
    page_summary: str = "",
    elements=None,
    cards=None,
    **kwargs,
):
    """提交页面语义命名：校验防幻觉 + 回填 func_name 到规则骨架元素。"""
    if snapshot_id is PROTECTED:
        raise ValueError("缺少必填参数: snapshot_id")
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
    return data


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

    qs = Page.objects.filter(is_folder=False).order_by("-created_at")
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


@_register("elements", "list_web_groups")
def _elements_list_web_groups(user_id: str, limit: int = 50, **kwargs):
    from apps.element_locator.models import WebGroup

    qs = WebGroup.objects.order_by("sort_order", "name")
    return list(qs[:limit])


@_register("elements", "search_web")
def _elements_search_web(user_id: str, query: str = "", limit: int = 20, **kwargs):
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
    return list(qs.order_by("name")[:limit])


@_register("elements", "list_api_groups")
def _elements_list_api_groups(user_id: str, limit: int = 50, **kwargs):
    from apps.element_locator.models import ApiGroup

    qs = ApiGroup.objects.order_by("sort_order", "name")
    return list(qs[:limit])


@_register("elements", "search_endpoints")
def _elements_search_endpoints(
    user_id: str, query: str = "", method: str = "", limit: int = 20, **kwargs
):
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
    return list(qs.order_by("name")[:limit])


# ── Case handlers ──


@_register("cases", "save_definition")
def _cases_save_definition(
    user_id: str,
    case_id: str = PROTECTED,
    title: str = "",
    case_type: str = "",
    steps=None,
    directory_id=None,
    package_name: str = "",
    enabled: bool = True,
    priority: str = "P1",
    **kwargs,
):
    if case_id is PROTECTED:
        raise ValueError("缺少必填参数: case_id")
    if not title:
        raise ValueError("缺少必填参数: title")
    from apps.case_manager.api import save_ai_definition

    if isinstance(enabled, str):
        # 网关/HTTP 直调可能传字符串布尔，防 "false"→True 误启用
        enabled = enabled.strip().lower() in ("1", "true", "yes")
    extra = {k: v for k, v in kwargs.items() if k != "user_id"}
    ok, payload = save_ai_definition(
        case_id=case_id,
        title=title,
        case_type=case_type or "ui_automation",
        steps=steps or [],
        directory_id=directory_id,
        package_name=package_name,
        enabled=bool(enabled),
        priority=priority,
        **extra,
    )
    if not ok:
        raise ValueError(payload)
    return payload


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
    from apps.case_manager.api import get_case_digest

    data = get_case_digest(case_id)
    if data is None:
        raise ValueError(f"用例不存在: {case_id}")
    return data


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


def _iso_or_empty(value) -> str:
    """datetime → ISO 字符串；其他类型原样转字符串；None → 空串。"""
    if value is None:
        return ""
    return value.isoformat() if hasattr(value, "isoformat") else str(value)


@_register("cases", "list_directories")
def _cases_list_directories(user_id: str, case_type: str = "", **kwargs):
    from apps.case_manager.models import CaseDirectory

    qs = CaseDirectory.objects.order_by("sort_order", "name")
    if case_type:
        qs = qs.filter(case_type=case_type)
    return list(qs)


@_register("cases", "search")
def _cases_search(
    user_id: str,
    query: str = "",
    case_type: str = "",
    directory_id=None,
    limit: int = 20,
    **kwargs,
):
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
                    "updated_at": _iso_or_empty(getattr(obj, "updated_at", None)),
                }
            )
    rows.sort(key=lambda r: r.get("updated_at") or "", reverse=True)
    return rows[:limit]


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
    from apps.test_runner.api import get_run_results, get_run_status

    run_status = get_run_status(run_id)
    if run_status is None:
        raise ValueError(f"run 不存在: {run_id}")
    return {"run_status": run_status, "results": get_run_results(run_id)}


@_register("runner", "get_run_status")
def _runner_get_run_status(user_id: str, run_id: str = PROTECTED, **kwargs):
    if run_id is PROTECTED:
        raise ValueError("缺少必填参数: run_id")
    from apps.test_runner.api import get_run_status

    data = get_run_status(run_id)
    if data is None:
        raise ValueError(f"run 不存在: {run_id}")
    return data


@_register("runner", "stop_run")
def _runner_stop_run(user_id: str, run_id: str = PROTECTED, **kwargs):
    if run_id is PROTECTED:
        raise ValueError("缺少必填参数: run_id")
    from apps.test_runner.api import stop_run

    return stop_run(run_id)


@_register("common", "sleep")
def _common_sleep(user_id: str, seconds: int = PROTECTED, **kwargs):
    """暂停等待（1-30 秒）——供 AI 在轮询异步任务前主动等待，降低查询频率。"""
    if seconds is PROTECTED:
        raise ValueError("缺少必填参数: seconds")
    import time

    n = max(1, min(int(seconds), 30))
    time.sleep(n)
    return {"slept_seconds": n}


# ── Workflow handlers ──


@_register("workflow", "list_page_flows")
def _workflow_list_page_flows(
    user_id: str, query: str = "", directory_id=None, limit: int = 20, **kwargs
):
    from apps.workflow.api import list_document_summaries

    return list_document_summaries(query=query, directory_id=directory_id, limit=limit)


@_register("workflow", "get_page_flow")
def _workflow_get_page_flow(user_id: str, doc_id: str = PROTECTED, **kwargs):
    if doc_id is PROTECTED:
        raise ValueError("缺少必填参数: doc_id")
    from apps.workflow.api import get_document_digest

    ok, data = get_document_digest(doc_id)
    if not ok:
        raise ValueError(data)
    return data


# ── Knowledge handlers ──


@_register("knowledge", "search")
def _knowledge_search(user_id: str, query: str = "", sources: list | None = None, **kwargs):
    from .rag_service import search as kb_search

    return kb_search(query, top_k=5, sources=sources)
