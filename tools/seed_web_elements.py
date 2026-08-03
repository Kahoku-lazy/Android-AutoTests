"""
Seed script: populate el_web_groups + el_web_elements with all platform page elements.

Idempotent — clears and re-creates on each run.
Usage: python tools/seed_web_elements.py
"""

import os
import sys

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from apps.element_locator.models import WebElement, WebGroup

# Clean slate
WebElement.objects.all().delete()
WebGroup.objects.all().delete()


def make_group(name, parent=None, is_folder=False):
    return WebGroup.objects.create(name=name, parent=parent, is_folder=is_folder)


def add_els(group, elements):
    """Batch create elements for a group. elements: list of (name, locator_type, locator_value, page_url, description)"""
    objs = []
    for name, lt, lv, url, desc in elements:
        objs.append(
            WebElement(
                group=group,
                name=name,
                locator_type=lt,
                locator_value=lv,
                page_url=url,
                description=desc,
            )
        )
    WebElement.objects.bulk_create(objs)


# ═══════════════════════════════════════════════════
# 1. Dashboard
# ═══════════════════════════════════════════════════
db_folder = make_group("仪表盘", is_folder=True)

# 1a. Stats Overview
g = make_group("统计概览", parent=db_folder)
add_els(
    g,
    [
        ("刷新按钮", "css_selector", ".wb-btn--sunset", "/dashboard", "仪表盘页面刷新按钮"),
        (
            "在线设备卡片",
            "css_selector",
            ".stats-card--green",
            "/dashboard",
            "统计卡片: 在线设备, 点击进入设备管理",
        ),
        (
            "测试用例卡片",
            "css_selector",
            ".stats-card--teal",
            "/dashboard",
            "统计卡片: 测试用例, 点击进入用例管理",
        ),
        (
            "活跃智能体卡片",
            "css_selector",
            ".stats-card--blue",
            "/dashboard",
            "统计卡片: 活跃智能体, 点击进入AI助手",
        ),
        (
            "运行中任务卡片",
            "css_selector",
            ".stats-card--pink",
            "/dashboard",
            "统计卡片: 运行中任务, 点击进入执行引擎",
        ),
        (
            "卡片进入按钮",
            "css_selector",
            ".stats-card__enter",
            "/dashboard",
            "各统计卡片上的进入按钮",
        ),
        (
            "在线设备数值",
            "css_selector",
            ".stats-card--green .stats-card__stat strong",
            "/dashboard",
            "在线设备数",
        ),
        (
            "测试用例数值",
            "css_selector",
            ".stats-card--teal .stats-card__stat strong",
            "/dashboard",
            "用例总数",
        ),
        (
            "运行中任务数值",
            "css_selector",
            ".stats-card--pink .stats-card__stat strong",
            "/dashboard",
            "活跃任务数",
        ),
    ],
)

# 1b. Trends
g = make_group("趋势图表", parent=db_folder)
add_els(
    g,
    [
        (
            "趋势柱状图",
            "css_selector",
            ".trends-chart-card",
            "/dashboard",
            "ECharts 柱状图: 成功/失败/新建 三系列",
        ),
        (
            "任务结果面板",
            "css_selector",
            ".trends-tasks-card",
            "/dashboard",
            "近期任务执行结果列表",
        ),
        ("成功摘要指标", "css_selector", ".summary-chip.is-success", "/dashboard", "成功任务计数"),
        ("失败摘要指标", "css_selector", ".summary-chip.is-failed", "/dashboard", "失败任务计数"),
        ("本周新建指标", "css_selector", ".summary-chip.is-new", "/dashboard", "本周新建用例计数"),
    ],
)

# 1c. Module Navigator
g = make_group("模块导航", parent=db_folder)
add_els(
    g,
    [
        (
            "仪表盘入口卡片",
            "css_selector",
            ".module-card--yellow",
            "/dashboard",
            "模块导航: 仪表盘快捷入口",
        ),
        (
            "设备管理入口卡片",
            "css_selector",
            ".module-card--green",
            "/dashboard",
            "模块导航: 设备管理入口",
        ),
        (
            "元素定位入口卡片",
            "css_selector",
            ".module-card--purple",
            "/dashboard",
            "模块导航: 元素定位入口",
        ),
        (
            "用例管理入口卡片",
            "css_selector",
            ".module-card--teal",
            "/dashboard",
            "模块导航: 用例管理入口",
        ),
        (
            "执行引擎入口卡片",
            "css_selector",
            ".module-card--pink",
            "/dashboard",
            "模块导航: 执行引擎入口",
        ),
        (
            "测试报告入口卡片",
            "css_selector",
            ".module-card--brown",
            "/dashboard",
            "模块导航: 测试报告入口",
        ),
        (
            "AI助手入口卡片",
            "css_selector",
            ".module-card--orange",
            "/dashboard",
            "模块导航: AI助手入口",
        ),
        (
            "工作流入口卡片",
            "css_selector",
            ".module-card--blue",
            "/dashboard",
            "模块导航: 工作流工作台入口",
        ),
    ],
)

# 1d. Activity Timeline
g = make_group("最近动态", parent=db_folder)
add_els(
    g,
    [
        ("活动时间线列表", "css_selector", ".activity-timeline", "/dashboard", "最近活动时间线"),
        (
            "时间线项-成功",
            "css_selector",
            ".timeline-item--success",
            "/dashboard",
            "活动时间线: 成功类型",
        ),
        (
            "时间线项-警告",
            "css_selector",
            ".timeline-item--warning",
            "/dashboard",
            "活动时间线: 警告类型",
        ),
        (
            "时间线项-错误",
            "css_selector",
            ".timeline-item--error",
            "/dashboard",
            "活动时间线: 错误类型",
        ),
        (
            "系统状态文本",
            "css_selector",
            ".dashboard__footer",
            "/dashboard",
            "页脚: 最近更新时间和系统状态",
        ),
    ],
)

# ═══════════════════════════════════════════════════
# 2. Device Pool
# ═══════════════════════════════════════════════════
dp_folder = make_group("设备管理", is_folder=True)

# 2a. Device Grid
g = make_group("设备网格", parent=dp_folder)
add_els(
    g,
    [
        ("局域网连接按钮", "css_selector", ".lan-btn", "/devices", "打开局域网连接弹窗"),
        ("刷新设备按钮", "css_selector", ".refresh-btn", "/devices", "刷新设备列表"),
        (
            "设备搜索框",
            "css_selector",
            '.toolbar input[placeholder*="搜索"]',
            "/devices",
            "搜索设备序列号或型号",
        ),
        ("全部设备Tab", "text", "全部设备", "/devices", "设备状态筛选Tab: 全部"),
        ("在线Tab", "text", "在线", "/devices", "设备状态筛选Tab: 在线"),
        ("使用中Tab", "text", "使用中", "/devices", "设备状态筛选Tab: 使用中"),
        ("离线Tab", "text", "离线", "/devices", "设备状态筛选Tab: 离线"),
        ("锁定按钮", "text", "锁定", "/devices", "锁定设备操作"),
        ("解除锁定按钮", "text", "解除锁定", "/devices", "解除设备锁定"),
        ("断开按钮", "text", "断开", "/devices", "断开设备连接"),
        ("设备表格", "css_selector", ".device-table", "/devices", "设备列表表格"),
        ("分页-上一页", "text", "上一页", "/devices", "设备列表分页"),
        ("分页-下一页", "text", "下一页", "/devices", "设备列表分页"),
    ],
)

# 2b. Connect Dialog
g = make_group("连接弹窗", parent=dp_folder)
add_els(
    g,
    [
        (
            "IP地址输入框",
            "css_selector",
            'input[placeholder*="IP"]',
            "/devices",
            "局域网连接: IP地址输入",
        ),
        (
            "端口输入框",
            "css_selector",
            'input[value="5555"]',
            "/devices",
            "局域网连接: 端口号, 默认5555",
        ),
        ("连接确认按钮", "text", "连接", "/devices", "局域网连接: 确认连接"),
    ],
)

# 2c. Queue Panel
g = make_group("排队面板", parent=dp_folder)
add_els(
    g,
    [
        ("排队徽章", "css_selector", ".queue-badge", "/devices", "设备排队: 显示排队数量"),
        ("排队取消按钮", "text", "取消", "/devices", "设备排队: 取消排队"),
    ],
)

# ═══════════════════════════════════════════════════
# 3. Case Manager
# ═══════════════════════════════════════════════════
cm_folder = make_group("用例管理", is_folder=True)

# 3a. UI Automation
ui_folder = make_group("UI自动化", parent=cm_folder, is_folder=True)
g = make_group("用例列表", parent=ui_folder)
add_els(
    g,
    [
        ("新建用例按钮", "text", "新建用例", "/cases", "打开用例编辑器"),
        ("导出YAML按钮", "text", "导出 YAML", "/cases", "导出用例为YAML"),
        ("卡片视图切换", "text", "▦", "/cases", "切换到卡片视图"),
        ("列表视图切换", "text", "☰", "/cases", "切换到列表视图"),
        ("搜索用例输入框", "css_selector", ".case-toolbar input", "/cases", "搜索用例标题或ID"),
        ("目录树根节点", "css_selector", ".el-tree", "/cases", "用例目录树"),
        ("选择模式按钮", "text", "选择", "/cases", "进入批量选择模式"),
        ("面包屑-全部用例", "css_selector", ".crumb--root", "/cases", "面包屑导航: 返回根目录"),
    ],
)
g = make_group("用例编辑", parent=ui_folder)
add_els(
    g,
    [
        (
            "用例标题输入",
            "css_selector",
            'input[placeholder*="用例标题"]',
            "/cases/new",
            "新建/编辑用例: 标题",
        ),
        (
            "用例ID输入",
            "css_selector",
            'input[placeholder*="留空则自动生成"]',
            "/cases/new",
            "新建用例: 自动或手动ID",
        ),
        (
            "优先级选择",
            "css_selector",
            'input[placeholder*="P0"]',
            "/cases/new",
            "用例优先级: P0/P1/P2",
        ),
        ("包名输入", "css_selector", 'input[placeholder*="com.example"]', "/cases/new", "用例包名"),
        ("启用开关", "css_selector", ".case-editor .el-switch", "/cases/new", "启用/禁用用例"),
        ("保存按钮", "text", "保存", "/cases/new", "保存用例"),
        ("退出按钮", "text", "退出", "/cases/new", "退出编辑器"),
        ("步骤编辑器面板", "css_selector", ".step-editor", "/cases/new", "步骤编排区域"),
        ("添加步骤按钮", "text", "添加步骤", "/cases/new", "添加新测试步骤"),
        (
            "元素库搜索",
            "css_selector",
            ".xpath-picker input",
            "/cases/new",
            "搜索已保存的Android元素",
        ),
        ("弹窗监视器面板", "css_selector", ".watcher-panel", "/cases/new", "全局弹窗监视器配置"),
    ],
)

# 3b. Storage / 3c. API / 3d. Web
for cat_key, cat_name, cols in [
    (
        "storage",
        "存储业务",
        ["测试用例编号", "用例标题", "优先级", "前置条件", "用例步骤", "预期结果"],
    ),
    (
        "api",
        "API接口",
        ["测试用例编号", "用例标题", "优先级", "前置条件", "请求头", "请求体", "预期响应文本"],
    ),
    (
        "web",
        "Web自动化",
        ["测试用例编号", "用例标题", "优先级", "前置条件", "目标URL", "操作步骤", "预期结果"],
    ),
]:
    sub = make_group(cat_name, parent=cm_folder, is_folder=True)
    g = make_group(cat_name + "列表", parent=sub)
    add_els(
        g,
        [
            (f"{cat_name}Tab切换", "text", cat_name, "/cases", f"切换到{cat_name}用例列表"),
            ("新建用例按钮", "text", "新建", f"/cases/{cat_key}/new", f"新建{cat_name}用例"),
            ("搜索输入框", "css_selector", ".case-toolbar input", f"/cases", f"搜索{cat_name}用例"),
        ],
    )
    g = make_group(cat_name + "编辑", parent=sub)
    add_els(
        g,
        [
            (
                f"{cat_name}添加行按钮",
                "text",
                "添加行",
                f"/cases/{cat_key}/new",
                f"{cat_name}编辑: 添加数据行",
            ),
            (
                f"{cat_name}添加列按钮",
                "text",
                "添加列",
                f"/cases/{cat_key}/new",
                f"{cat_name}编辑: 添加自定义列",
            ),
            (
                f"{cat_name}保存按钮",
                "text",
                "保存",
                f"/cases/{cat_key}/new",
                f"{cat_name}编辑: 保存",
            ),
        ]
        + [
            (
                f"{cat_name}列-{c}",
                "css_selector",
                f".cell-input",
                f"/cases/{cat_key}/new",
                f"{cat_name}编辑: {c}列",
            )
            for c in cols
        ],
    )

# ═══════════════════════════════════════════════════
# 4. Test Runner
# ═══════════════════════════════════════════════════
tr_folder = make_group("执行引擎", is_folder=True)

g = make_group("执行面板", parent=tr_folder)
add_els(
    g,
    [
        ("新建任务按钮", "text", "新建任务", "/runner", "打开新建任务弹窗"),
        ("全部Tab", "text", "全部", "/runner", "任务列表筛选: 全部"),
        ("执行中Tab", "text", "执行中", "/runner", "任务列表筛选: 执行中"),
        ("已完成Tab", "text", "已完成", "/runner", "任务列表筛选: 已完成"),
        (
            "任务名称输入",
            "css_selector",
            'input[placeholder*="任务名称"]',
            "/runner",
            "新建任务: 任务名称",
        ),
        (
            "设备选择",
            "css_selector",
            'input[placeholder*="选择在线设备"]',
            "/runner",
            "新建任务: 选择设备",
        ),
        (
            "用例选择",
            "css_selector",
            'input[placeholder*="选择用例"]',
            "/runner",
            "新建任务: 选择用例",
        ),
        ("循环次数输入", "css_selector", ".el-input-number", "/runner", "新建任务: 循环次数"),
        ("立即执行Radio", "text", "立即执行", "/runner", "执行方式: 立即"),
        ("定时执行Radio", "text", "定时执行", "/runner", "执行方式: 定时"),
        ("创建并执行按钮", "text", "创建并执行", "/runner", "新建任务: 提交创建"),
        ("停止按钮", "text", "停止", "/runner", "停止正在执行的任务"),
        ("重新执行按钮", "text", "重新执行", "/runner", "重新执行已完成的任务"),
        ("查看报告按钮", "text", "查看报告", "/runner", "跳转到任务报告"),
        ("删除按钮", "text", "删除", "/runner", "删除任务"),
    ],
)

g = make_group("任务详情", parent=tr_folder)
add_els(
    g,
    [
        ("返回列表按钮", "text", "返回列表", "/runner/task/:id", "返回任务列表"),
        ("日志面板", "css_selector", ".log-panel", "/runner/task/:id", "实时WebSocket日志"),
        ("清空日志按钮", "text", "清空", "/runner/task/:id", "清空日志面板"),
        (
            "用例执行卡片",
            "css_selector",
            ".case-execution-card",
            "/runner/task/:id",
            "单个用例的执行结果",
        ),
        ("BUG卡片", "css_selector", ".bug-card", "/runner/task/:id", "执行失败BUG记录"),
    ],
)

# ═══════════════════════════════════════════════════
# 5. Report Generator
# ═══════════════════════════════════════════════════
rg_folder = make_group("测试报告", is_folder=True)

g = make_group("报告网格", parent=rg_folder)
add_els(
    g,
    [
        ("日期范围选择", "css_selector", ".el-date-editor", "/reports", "筛选日期范围"),
        ("RunID搜索", "css_selector", 'input[placeholder*="Run ID"]', "/reports", "按Run ID搜索"),
        (
            "任务名称搜索",
            "css_selector",
            'input[placeholder*="任务名称"]',
            "/reports",
            "按任务名称搜索",
        ),
        ("设备搜索", "css_selector", 'input[placeholder*="设备"]', "/reports", "按设备搜索"),
        ("创建人搜索", "css_selector", 'input[placeholder*="创建人"]', "/reports", "按创建人搜索"),
        ("清空条件按钮", "text", "清空条件", "/reports", "清空所有筛选条件"),
        ("通过KPI卡片", "css_selector", ".kpi-card.green", "/reports", "点击查看通过的用例"),
        ("失败KPI卡片", "css_selector", ".kpi-card.red", "/reports", "点击查看失败的用例"),
        ("通过率趋势图", "css_selector", ".pass-rate-chart", "/reports", "通过率趋势折线图"),
        ("每日通过失败图", "css_selector", ".daily-chart", "/reports", "每日通过/失败柱状图"),
        ("图表范围按钮7天", "text", "7天", "/reports", "图表时间范围: 7天"),
        ("图表范围按钮30天", "text", "30天", "/reports", "图表时间范围: 30天"),
        ("图表范围按钮60天", "text", "60天", "/reports", "图表时间范围: 60天"),
        ("图表范围按钮90天", "text", "90天", "/reports", "图表时间范围: 90天"),
        ("报告表格", "css_selector", ".report-table", "/reports", "执行报告列表表格"),
    ],
)

g = make_group("报告详情", parent=rg_folder)
add_els(
    g,
    [
        ("用例执行明细Tab", "text", "用例执行明细", "/reports/:runId", "查看用例执行详情"),
        ("失败分析Tab", "text", "失败分析", "/reports/:runId", "查看失败分析"),
        ("展开步骤按钮", "css_selector", ".expand-row", "/reports/:runId", "展开用例步骤详情"),
    ],
)

g = make_group("用例细分", parent=rg_folder)
add_els(
    g,
    [
        ("BUG问题汇总Tab", "text", "BUG问题汇总", "/reports/cases/:type", "按BUG类型汇总"),
        ("失败明细Tab", "text", "失败明细", "/reports/cases/fail", "失败用例详细列表"),
    ],
)

# ═══════════════════════════════════════════════════
# 6. AI Assistant
# ═══════════════════════════════════════════════════
ai_folder = make_group("AI助手", is_folder=True)

g = make_group("智能体列表", parent=ai_folder)
add_els(
    g,
    [
        ("新建智能体按钮", "text", "新建智能体", "/ai-assistant", "创建新的AI智能体"),
        ("智能体看板Tab", "text", "智能体看板", "/ai-assistant", "切换到智能体看板"),
        ("知识库Tab", "text", "知识库", "/ai-assistant", "切换到知识库管理"),
        ("评测中心Tab", "text", "评测中心", "/ai-assistant", "切换到评测中心"),
        (
            "智能体便签卡片",
            "css_selector",
            ".sticky-note",
            "/ai-assistant",
            "智能体便签: 名称/模型/状态",
        ),
        ("智能体聊天按钮", "text", "聊天", "/ai-assistant", "点击进入AI对话"),
        ("智能体编辑按钮", "text", "编辑", "/ai-assistant", "编辑智能体配置"),
        ("智能体删除按钮", "text", "删除", "/ai-assistant", "删除智能体"),
        ("任务便签卡片", "css_selector", ".task-sticky-note", "/ai-assistant", "任务看板便签"),
        ("任务筛选Tab-全部", "text", "全部", "/ai-assistant", "任务筛选: 全部"),
        ("任务筛选Tab-待执行", "text", "待执行", "/ai-assistant", "任务筛选: 待执行"),
    ],
)

g = make_group("智能体详情", parent=ai_folder)
add_els(
    g,
    [
        (
            "名称输入",
            "css_selector",
            'input[placeholder*="名称"]',
            "/ai-assistant/agent/:id",
            "智能体配置: 名称",
        ),
        (
            "模型提供商选择",
            "css_selector",
            'input[placeholder*="模型提供商"]',
            "/ai-assistant/agent/:id",
            "智能体配置: 模型提供商",
        ),
        (
            "APIKey输入",
            "css_selector",
            'input[type="password"]',
            "/ai-assistant/agent/:id",
            "智能体配置: API Key",
        ),
        (
            "系统提示词输入",
            "css_selector",
            'textarea[placeholder*="提示词"]',
            "/ai-assistant/agent/:id",
            "智能体配置: 系统提示词",
        ),
        ("保存配置按钮", "text", "保存", "/ai-assistant/agent/:id", "保存智能体配置"),
        (
            "阶段1工具配置",
            "text",
            "阶段 1",
            "/ai-assistant/agent/:id",
            "SOP阶段1: 需求分析与用例设计",
        ),
        ("阶段2工具配置", "text", "阶段 2", "/ai-assistant/agent/:id", "SOP阶段2: 元素准备"),
        ("阶段3工具配置", "text", "阶段 3", "/ai-assistant/agent/:id", "SOP阶段3: 用例创建与调试"),
        ("阶段4工具配置", "text", "阶段 4", "/ai-assistant/agent/:id", "SOP阶段4: 任务执行"),
    ],
)

g = make_group("AI对话", parent=ai_folder)
add_els(
    g,
    [
        (
            "对话消息输入框",
            "css_selector",
            ".chat-input textarea",
            "/ai-assistant/chat/:id",
            "AI对话: 消息输入",
        ),
        (
            "发送按钮",
            "css_selector",
            ".chat-input button",
            "/ai-assistant/chat/:id",
            "AI对话: 发送消息",
        ),
        (
            "对话列表",
            "css_selector",
            ".conversation-list",
            "/ai-assistant/chat/:id",
            "AI对话: 历史对话列表",
        ),
        (
            "消息气泡",
            "css_selector",
            ".message-bubble",
            "/ai-assistant/chat/:id",
            "AI对话: 消息气泡",
        ),
        (
            "思考块",
            "css_selector",
            ".thinking-block",
            "/ai-assistant/chat/:id",
            "AI对话: 思考过程展示",
        ),
        (
            "工具调用卡片",
            "css_selector",
            ".tool-call-card",
            "/ai-assistant/chat/:id",
            "AI对话: 工具调用结果",
        ),
    ],
)

# ═══════════════════════════════════════════════════
# 7. Workflow
# ═══════════════════════════════════════════════════
wf_folder = make_group("工作流工作台", is_folder=True)

g = make_group("画布区", parent=wf_folder)
add_els(
    g,
    [
        ("导入JSON按钮", "text", "导入 JSON", "/workflow", "导入工作流JSON文件"),
        ("同ID覆盖复选框", "text", "同 ID 覆盖", "/workflow", "导入时覆盖同ID文件"),
        ("导出JSON按钮", "text", "导出 JSON", "/workflow", "导出当前工作流"),
        ("保存按钮", "text", "保存", "/workflow", "保存工作流"),
        ("关闭编辑按钮", "text", "关闭编辑", "/workflow", "关闭当前编辑的文件"),
        ("侧边栏折叠按钮", "css_selector", ".sidebar-toggle", "/workflow", "折叠/展开资源树"),
        ("新建根目录按钮", "text", "根目录", "/workflow", "创建根级目录"),
        ("新建页面流按钮", "text", "页面流", "/workflow", "创建页面流文件"),
        ("新建用例按钮", "text", "用例", "/workflow", "创建工作流用例"),
        ("导入用例按钮", "text", "导入用例", "/workflow", "从用例库导入"),
        ("文件卡片-全部", "text", "全部", "/workflow", "文件列表: 全部"),
        ("文件卡片-页面流", "text", "页面流", "/workflow", "文件筛选: 页面流"),
        ("文件卡片-测试用例", "text", "测试用例", "/workflow", "文件筛选: 测试用例"),
        (
            "目录名称输入",
            "css_selector",
            'input[maxlength="80"]',
            "/workflow",
            "新建目录: 名称输入",
        ),
    ],
)

g = make_group("积木编辑器", parent=wf_folder)
add_els(
    g,
    [
        ("Blockly画布", "css_selector", ".blockly-container", "/workflow", "Blockly积木编辑区域"),
        ("积木工具栏", "css_selector", ".blocklyToolboxDiv", "/workflow", "Blockly积木分类面板"),
    ],
)

# ═══════════════════════════════════════════════════
# 8. Element Locator (already seeded partially via web-manager)
# ═══════════════════════════════════════════════════
el_folder = make_group("元素定位", is_folder=True)
g = make_group("设备发现", parent=el_folder)
add_els(
    g,
    [
        ("设备选择器", "css_selector", ".device-selector", "/elements", "选择/连接Android设备"),
        ("刷新屏幕按钮", "text", "刷新屏幕", "/elements", "刷新设备截图"),
        ("DumpUI按钮", "text", "Dump UI", "/elements", "Dump设备UI层级"),
        ("筛选Radio-全部", "text", "全部", "/elements", "元素筛选: 全部"),
        ("筛选Radio-可点击", "text", "可点击", "/elements", "元素筛选: 可点击"),
        ("筛选Radio-有文本", "text", "有文本", "/elements", "元素筛选: 有文本"),
        ("筛选Radio-有ResourceID", "text", "有 Resource ID", "/elements", "元素筛选: Resource ID"),
        (
            "元素搜索框",
            "css_selector",
            'input[placeholder*="搜索"]',
            "/elements",
            "搜索text/resource-id/class",
        ),
        ("截图Canvas", "css_selector", "canvas", "/elements", "设备截图渲染Canvas"),
        ("XPath候选面板", "css_selector", ".col-xpath", "/elements", "XPath候选列表"),
        ("混入用例按钮", "css_selector", ".add-step-btn", "/elements", "将XPath添加到用例步骤"),
    ],
)

g = make_group("Android元素管理", parent=el_folder)
add_els(
    g,
    [
        ("页面树面板", "css_selector", ".page-tree-panel", "/elements", "Android页面/文件夹树"),
        ("新建目录按钮", "text", "目录", "/elements", "创建元素目录"),
        ("新建页面按钮", "text", "页面", "/elements", "创建Android页面"),
        ("选择模式按钮", "text", "选择", "/elements", "进入批量选择"),
        ("清空按钮", "text", "清空", "/elements", "清空所有页面"),
        ("添加元素按钮", "text", "添加元素", "/elements", "手动添加Android元素"),
        ("元素筛选Tab-全部", "text", "全部", "/elements", "元素筛选: 全部"),
        ("元素筛选Tab-测试点", "text", "测试点", "/elements", "元素筛选: 测试点"),
    ],
)

g = make_group("Web端元素管理", parent=el_folder)
add_els(
    g,
    [
        (
            "项目分组树",
            "css_selector",
            ".web-element-manager .tree-panel",
            "/elements",
            "Web元素分组织树",
        ),
        ("新建项目按钮", "text", "项目", "/elements", "创建Web项目目录"),
        ("新建模块按钮", "text", "模块", "/elements", "创建Web模块"),
        ("添加Web元素按钮", "text", "添加元素", "/elements", "手动添加Web元素"),
        ("批量导入按钮", "text", "批量导入", "/elements", "JSON批量导入Web元素"),
        ("未分类节点", "text", "未分类", "/elements", "显示未分类的Web元素"),
    ],
)

# ═══════════════════════════════════════════════════
# Summary
# ═══════════════════════════════════════════════════
total_groups = WebGroup.objects.count()
total_elements = WebElement.objects.count()
print(f"[OK] Seeded {total_groups} groups, {total_elements} elements")
print(f"  Dashboard:  {WebGroup.objects.filter(name='仪表盘').count()} groups")
print(f"  Device:     {WebGroup.objects.filter(name='设备管理').count()} groups")
print(f"  Case Mgr:   {WebGroup.objects.filter(name='用例管理').count()} groups")
print(f"  Test Runner:{WebGroup.objects.filter(name='执行引擎').count()} groups")
print(f"  Reports:    {WebGroup.objects.filter(name='测试报告').count()} groups")
print(f"  AI:         {WebGroup.objects.filter(name='AI助手').count()} groups")
print(f"  Workflow:   {WebGroup.objects.filter(name='工作流工作台').count()} groups")
print(f"  Elements:   {WebGroup.objects.filter(name='元素定位').count()} groups")
