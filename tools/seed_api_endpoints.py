"""Seed ApiGroup + ApiEndpoint records from the platform's own API catalog."""

import os
import sys

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

django.setup()

from apps.element_locator.models import ApiEndpoint, ApiGroup


# ── Helper ──
def create_folder(name, parent=None, sort=0):
    g, _ = ApiGroup.objects.update_or_create(
        name=name,
        parent=parent,
        defaults={"is_folder": True, "sort_order": sort},
    )
    return g


def create_group(name, parent, sort=0):
    g, _ = ApiGroup.objects.update_or_create(
        name=name,
        parent=parent,
        defaults={"is_folder": False, "sort_order": sort},
    )
    return g


def create_endpoint(group, method, name, url, description, tags=""):
    # Use update_or_create to be idempotent
    ApiEndpoint.objects.update_or_create(
        group=group,
        method=method,
        url=url,
        defaults={
            "name": name,
            "description": description,
            "tags": tags,
            "is_test_point": False,
        },
    )


# ── Tree structure ──
print("Creating ApiGroup tree...")

ROOT = create_folder("Android-AutoTests 平台", sort=0)

# ── 0. Platform root ──
f_platform = create_folder("平台入口", parent=ROOT, sort=0)
g_root = create_group("根路径 & 文档", parent=f_platform, sort=0)
create_endpoint(
    g_root, "GET", "服务健康检查", "/", '返回 {"status":true,"service":"Android-AutoTests API"}'
)
create_endpoint(g_root, "GET", "API 文档 JSON", "/api/docs", "完整 JSON 格式的 API 文档")
create_endpoint(g_root, "GET", "API 文档 HTML", "/api/docs.html", "交互式 HTML API 文档页面")

# ── 1. Dashboard ──
f_dashboard = create_folder("仪表盘", parent=ROOT, sort=1)
g_dash = create_group("统计接口", parent=f_dashboard, sort=0)
create_endpoint(
    g_dash,
    "GET",
    "平台概览统计",
    "/api/dashboard/stats/",
    "聚合统计：设备数、用例数、执行次数、Agent 数、通过率",
)
create_endpoint(g_dash, "GET", "近期活动", "/api/dashboard/activities/", "跨模块最新事件列表")
create_endpoint(g_dash, "GET", "设备统计", "/api/devices/stats/", "设备池概览：在线/忙碌/离线/断连")
create_endpoint(
    g_dash, "GET", "用例统计", "/api/cases/stats/", "用例概览：总数/启用/禁用（跨类型）"
)

# ── 2. Device Pool ──
f_device = create_folder("设备管理", parent=ROOT, sort=2)
g_dev_list = create_group("设备列表与连接", parent=f_device, sort=0)
create_endpoint(
    g_dev_list, "GET", "设备列表", "/api/devices/", "列出所有设备及状态，含自动心跳同步"
)
create_endpoint(
    g_dev_list, "POST", "扫描注册设备", "/api/devices/scan", "扫描并注册新设备（无线 ADB 或 USB）"
)
create_endpoint(
    g_dev_list, "GET", "当前活跃设备", "/api/devices/current", "当前活跃设备信息（缓存，不走 ADB）"
)
create_endpoint(
    g_dev_list, "POST", "连接设备", "/api/devices/{serial}", "连接指定设备并自动切换为当前设备"
)
create_endpoint(
    g_dev_list,
    "POST",
    "断开设备",
    "/api/devices/{serial}/disconnect",
    "断开设备连接（若持有锁则释放）",
)
create_endpoint(
    g_dev_list,
    "POST",
    "断开观察模式",
    "/api/devices/{serial}/disconnect-observe",
    "仅断开观察连接，保留锁状态",
)
create_endpoint(
    g_dev_list,
    "POST",
    "切换活跃设备",
    "/api/devices/{serial}/activate",
    "将当前活跃设备切换为指定序列号",
)

g_dev_lock = create_group("设备锁定", parent=f_device, sort=1)
create_endpoint(
    g_dev_lock, "POST", "锁定设备", "/api/devices/{serial}/lock", "独占锁定设备（用户或进程）"
)
create_endpoint(
    g_dev_lock,
    "POST",
    "释放设备",
    "/api/devices/{serial}/release",
    "释放设备锁定状态（恢复 ONLINE）",
)
create_endpoint(
    g_dev_lock, "GET", "心跳检测", "/api/devices/heartbeat", "手动触发心跳，返回在线/忙碌/离线/总数"
)

g_dev_queue = create_group("设备队列", parent=f_device, sort=2)
create_endpoint(
    g_dev_queue, "GET", "队列状态", "/api/devices/queue", "当前排队状态（活跃锁列表，FIFO 排序）"
)
create_endpoint(
    g_dev_queue, "POST", "加入等待队列", "/api/devices/{serial}/queue", "加入设备使用等待队列"
)
create_endpoint(
    g_dev_queue, "POST", "离开等待队列", "/api/devices/{serial}/queue/leave", "离开设备使用等待队列"
)

# ── 3. Element Locator ──
f_element = create_folder("元素定位", parent=ROOT, sort=3)

g_el_device = create_group("设备交互", parent=f_element, sort=0)
create_endpoint(
    g_el_device,
    "POST",
    "Dump UI 层级",
    "/api/elements/dump",
    "从连接设备实时获取 UI 层级结构（不持久化）",
)
create_endpoint(
    g_el_device,
    "POST",
    "执行设备操作",
    "/api/elements/action",
    "在设备上执行 click / input / swipe / drag",
)
create_endpoint(
    g_el_device,
    "GET",
    "设备信息",
    "/api/elements/device-info",
    "当前设备信息：型号、分辨率、包名、占用状态",
)
create_endpoint(
    g_el_device, "GET", "快速截图", "/api/elements/screenshot", "单帧 JPEG 截图，用于首屏快速渲染"
)

g_el_page = create_group("页面管理", parent=f_element, sort=1)
create_endpoint(
    g_el_page,
    "GET",
    "页面列表",
    "/api/elements/pages",
    "列出所有已记录页面（含 parent_id、跳转流计数）",
)
create_endpoint(
    g_el_page, "POST", "创建页面/目录", "/api/elements/pages/create", "手动创建页面或目录节点"
)
create_endpoint(
    g_el_page,
    "POST",
    "清空所有页面",
    "/api/elements/pages/clear",
    "删除所有页面、元素和跳转流（不可逆）",
)
create_endpoint(
    g_el_page,
    "POST",
    "批量移动页面",
    "/api/elements/pages/batch-move",
    "批量移动页面/目录到目标父节点",
)
create_endpoint(
    g_el_page, "PUT", "更新页面名称", "/api/elements/pages/{page_id}", "更新页面标签名称"
)
create_endpoint(
    g_el_page, "DELETE", "删除页面", "/api/elements/pages/{page_id}", "删除页面及关联的元素和跳转流"
)

g_el_elem = create_group("页面元素", parent=f_element, sort=2)
create_endpoint(
    g_el_elem,
    "GET",
    "页面元素列表",
    "/api/elements/pages/{page_id}/items",
    "获取页面下元素列表（支持筛选：all/clickable/text/testpoint）",
)
create_endpoint(
    g_el_elem,
    "POST",
    "添加页面元素",
    "/api/elements/pages/{page_id}/elements",
    "向页面添加单个元素",
)
create_endpoint(
    g_el_elem,
    "POST",
    "批量添加元素",
    "/api/elements/pages/{page_id}/elements/batch",
    "向页面批量添加多个元素",
)
create_endpoint(
    g_el_elem,
    "PUT",
    "更新元素信息",
    "/api/elements/items/{el_id}",
    "更新元素元数据：别名、标签、备注、测试点",
)

g_el_flow = create_group("页面跳转流", parent=f_element, sort=3)
create_endpoint(g_el_flow, "GET", "跳转流列表", "/api/elements/flows", "列出所有页面跳转流关系")
create_endpoint(g_el_flow, "POST", "创建跳转流", "/api/elements/flows", "创建页面跳转关系")
create_endpoint(
    g_el_flow, "DELETE", "删除跳转流", "/api/elements/flows/{flow_id}", "删除一条跳转流记录"
)

g_web_el = create_group("Web 元素管理", parent=f_element, sort=4)
create_endpoint(
    g_web_el,
    "GET",
    "Web 元素列表",
    "/api/elements/web",
    "列出 Web 元素（支持搜索，按类型/URL/分组筛选）",
)
create_endpoint(
    g_web_el,
    "POST",
    "创建 Web 元素",
    "/api/elements/web/create",
    "创建 Web 页面元素（支持 12 种定位方式）",
)
create_endpoint(
    g_web_el, "POST", "批量导入 Web 元素", "/api/elements/web/batch", "JSON 批量导入 Web 元素"
)
create_endpoint(g_web_el, "PUT", "更新 Web 元素", "/api/elements/web/{el_id}", "更新 Web 元素信息")
create_endpoint(g_web_el, "DELETE", "删除 Web 元素", "/api/elements/web/{el_id}", "删除 Web 元素")

g_web_grp = create_group("Web 分组管理", parent=f_element, sort=5)
create_endpoint(
    g_web_grp, "GET", "Web 分组列表", "/api/elements/web-groups", "列出所有 Web 分组（含元素数量）"
)
create_endpoint(
    g_web_grp, "POST", "创建 Web 分组", "/api/elements/web-groups/create", "创建 Web 分组或目录"
)
create_endpoint(
    g_web_grp,
    "POST",
    "批量移动分组",
    "/api/elements/web-groups/batch-move",
    "批量移动 Web 分组到目标父级",
)
create_endpoint(
    g_web_grp, "PUT", "更新 Web 分组", "/api/elements/web-groups/{group_id}", "更新 Web 分组名称"
)
create_endpoint(
    g_web_grp,
    "DELETE",
    "删除 Web 分组",
    "/api/elements/web-groups/{group_id}",
    "删除 Web 分组（元素变为未分类）",
)

g_web_flow = create_group("Web 页面跳转", parent=f_element, sort=6)
create_endpoint(
    g_web_flow, "GET", "Web 跳转流列表", "/api/elements/web-flows", "列出所有 Web 页面跳转流"
)
create_endpoint(
    g_web_flow, "POST", "创建 Web 跳转流", "/api/elements/web-flows", "创建 Web 页面跳转关系"
)
create_endpoint(
    g_web_flow,
    "DELETE",
    "删除 Web 跳转流",
    "/api/elements/web-flows/{flow_id}",
    "删除一条 Web 跳转流记录",
)

g_api_grp = create_group("API 分组管理", parent=f_element, sort=7)
create_endpoint(
    g_api_grp, "GET", "API 分组列表", "/api/elements/api-groups", "列出所有 API 分组（含接口数量）"
)
create_endpoint(
    g_api_grp, "POST", "创建 API 分组", "/api/elements/api-groups/create", "创建 API 分组或目录"
)
create_endpoint(
    g_api_grp,
    "POST",
    "批量移动 API 分组",
    "/api/elements/api-groups/batch-move",
    "批量移动 API 分组到目标父级",
)
create_endpoint(
    g_api_grp, "PUT", "更新 API 分组", "/api/elements/api-groups/{group_id}", "更新 API 分组名称"
)
create_endpoint(
    g_api_grp,
    "DELETE",
    "删除 API 分组",
    "/api/elements/api-groups/{group_id}",
    "删除 API 分组（接口变为未分类）",
)

g_api_ep = create_group("API 接口管理", parent=f_element, sort=8)
create_endpoint(
    g_api_ep,
    "GET",
    "API 接口列表",
    "/api/elements/api-endpoints",
    "列出所有 API 接口定义（支持搜索）",
)
create_endpoint(
    g_api_ep, "POST", "创建 API 接口", "/api/elements/api-endpoints/create", "创建 API 接口定义"
)
create_endpoint(
    g_api_ep, "PUT", "更新 API 接口", "/api/elements/api-endpoints/{el_id}", "更新 API 接口定义"
)
create_endpoint(
    g_api_ep, "DELETE", "删除 API 接口", "/api/elements/api-endpoints/{el_id}", "删除 API 接口定义"
)

# ── 4. Case Manager ──
f_case = create_folder("用例管理", parent=ROOT, sort=4)

g_case_dir = create_group("目录管理", parent=f_case, sort=0)
create_endpoint(
    g_case_dir, "GET", "用例目录列表", "/api/cases/directories", "完整目录树（可按 case_type 筛选）"
)
create_endpoint(g_case_dir, "POST", "创建目录", "/api/cases/directories/create", "创建用例目录")
create_endpoint(
    g_case_dir, "POST", "更新/删除目录", "/api/cases/directories/{dir_id}", "更新目录信息或删除目录"
)
create_endpoint(
    g_case_dir, "POST", "批量移动目录", "/api/cases/directories/batch-move", "批量移动目录及内容"
)
create_endpoint(
    g_case_dir,
    "POST",
    "设置目录权限",
    "/api/cases/directories/{dir_id}/permission",
    "设置目录访问权限",
)

g_case_ui = create_group("UI 测试用例", parent=f_case, sort=1)
create_endpoint(
    g_case_ui,
    "GET",
    "UI 用例列表",
    "/api/cases/definitions",
    "列出 UI 自动化测试用例（含可见性过滤）",
)
create_endpoint(
    g_case_ui, "POST", "创建/更新 UI 用例", "/api/cases/definitions", "创建或更新 UI 自动化测试用例"
)
create_endpoint(
    g_case_ui,
    "POST",
    "批量保存 UI 用例",
    "/api/cases/definitions/batch",
    "批量保存 UI 自动化测试用例",
)
create_endpoint(
    g_case_ui, "GET", "UI 用例详情", "/api/cases/definitions/{case_id}", "获取单个 UI 用例详情"
)
create_endpoint(
    g_case_ui, "PUT", "更新单个 UI 用例", "/api/cases/definitions/{case_id}", "更新单个 UI 测试用例"
)
create_endpoint(
    g_case_ui, "DELETE", "删除 UI 用例", "/api/cases/definitions/{case_id}", "删除单个 UI 测试用例"
)

g_case_storage = create_group("存储测试用例", parent=f_case, sort=2)
create_endpoint(
    g_case_storage,
    "GET",
    "存储用例列表",
    "/api/cases/storage/definitions",
    "列出存储/业务功能测试用例",
)
create_endpoint(
    g_case_storage,
    "POST",
    "创建/更新存储用例",
    "/api/cases/storage/definitions",
    "创建或更新存储测试用例",
)
create_endpoint(
    g_case_storage,
    "POST",
    "批量保存存储用例",
    "/api/cases/storage/definitions/batch",
    "批量保存存储测试用例",
)
create_endpoint(
    g_case_storage,
    "GET",
    "存储用例详情",
    "/api/cases/storage/definitions/{case_id}",
    "获取单个存储用例详情",
)
create_endpoint(
    g_case_storage,
    "PUT",
    "更新单个存储用例",
    "/api/cases/storage/definitions/{case_id}",
    "更新单个存储测试用例",
)
create_endpoint(
    g_case_storage,
    "DELETE",
    "删除存储用例",
    "/api/cases/storage/definitions/{case_id}",
    "删除单个存储测试用例",
)

g_case_api = create_group("API 测试用例", parent=f_case, sort=3)
create_endpoint(
    g_case_api,
    "GET",
    "API 测试用例列表",
    "/api/cases/api-testing/definitions",
    "列出 API 接口测试用例",
)
create_endpoint(
    g_case_api,
    "POST",
    "创建/更新 API 测试用例",
    "/api/cases/api-testing/definitions",
    "创建或更新 API 测试用例",
)
create_endpoint(
    g_case_api,
    "POST",
    "批量保存 API 测试用例",
    "/api/cases/api-testing/definitions/batch",
    "批量保存 API 测试用例",
)
create_endpoint(
    g_case_api,
    "GET",
    "API 测试用例详情",
    "/api/cases/api-testing/definitions/{case_id}",
    "获取单个 API 测试用例详情",
)
create_endpoint(
    g_case_api,
    "PUT",
    "更新单个 API 测试用例",
    "/api/cases/api-testing/definitions/{case_id}",
    "更新单个 API 测试用例",
)
create_endpoint(
    g_case_api,
    "DELETE",
    "删除 API 测试用例",
    "/api/cases/api-testing/definitions/{case_id}",
    "删除单个 API 测试用例",
)

g_case_web = create_group("Web 测试用例", parent=f_case, sort=4)
create_endpoint(
    g_case_web, "GET", "Web 测试用例列表", "/api/cases/web/definitions", "列出 Web 自动化测试用例"
)
create_endpoint(
    g_case_web,
    "POST",
    "创建/更新 Web 测试用例",
    "/api/cases/web/definitions",
    "创建或更新 Web 自动化测试用例",
)
create_endpoint(
    g_case_web,
    "POST",
    "批量保存 Web 测试用例",
    "/api/cases/web/definitions/batch",
    "批量保存 Web 自动化测试用例",
)
create_endpoint(
    g_case_web,
    "GET",
    "Web 测试用例详情",
    "/api/cases/web/definitions/{case_id}",
    "获取单个 Web 测试用例详情",
)
create_endpoint(
    g_case_web,
    "PUT",
    "更新单个 Web 测试用例",
    "/api/cases/web/definitions/{case_id}",
    "更新单个 Web 测试用例",
)
create_endpoint(
    g_case_web,
    "DELETE",
    "删除 Web 测试用例",
    "/api/cases/web/definitions/{case_id}",
    "删除单个 Web 测试用例",
)

g_case_lock = create_group("编辑锁与权限", parent=f_case, sort=5)
create_endpoint(
    g_case_lock,
    "POST",
    "获取编辑锁",
    "/api/cases/definitions/{case_id}/lock",
    "获取用例编辑锁（30 分钟超时）",
)
create_endpoint(
    g_case_lock, "POST", "释放编辑锁", "/api/cases/definitions/{case_id}/unlock", "释放用例编辑锁"
)
create_endpoint(
    g_case_lock,
    "POST",
    "锁定用例",
    "/api/cases/definitions/{case_id}/case-lock",
    "锁定用例（备用锁机制）",
)
create_endpoint(
    g_case_lock,
    "POST",
    "解锁用例",
    "/api/cases/definitions/{case_id}/case-unlock",
    "解锁用例（备用解锁机制）",
)
create_endpoint(
    g_case_lock,
    "POST",
    "设置可见性",
    "/api/cases/definitions/{case_id}/visibility",
    "设置用例可见性（public/private/restricted）",
)

g_case_export = create_group("YAML 导出", parent=f_case, sort=6)
create_endpoint(
    g_case_export, "POST", "导出 YAML", "/api/cases/export/yaml", "导出测试点到 YAML 文件"
)
create_endpoint(g_case_export, "GET", "导出列表", "/api/cases/exports", "列出已导出 YAML 文件")
create_endpoint(
    g_case_export, "GET", "下载导出文件", "/api/cases/exports/{filename}", "下载 YAML 导出文件"
)

# ── 5. Workflow ──
f_workflow = create_folder("工作流", parent=ROOT, sort=5)

g_wf_dir = create_group("目录管理", parent=f_workflow, sort=0)
create_endpoint(
    g_wf_dir, "GET", "工作流目录列表", "/api/workflow/directories", "列出工作流目录（平铺 + 树形）"
)
create_endpoint(
    g_wf_dir, "POST", "创建工作流目录", "/api/workflow/directories/create", "创建工作流目录"
)
create_endpoint(
    g_wf_dir,
    "POST",
    "更新/删除目录",
    "/api/workflow/directories/{dir_id}",
    "更新目录信息或删除目录",
)
create_endpoint(
    g_wf_dir, "POST", "移动目录", "/api/workflow/directories/{dir_id}/move", "移动目录到新的父节点"
)

g_wf_doc = create_group("文档管理", parent=f_workflow, sort=1)
create_endpoint(
    g_wf_doc, "GET", "文档列表", "/api/workflow/documents", "列出工作流文档（可按目录和类型筛选）"
)
create_endpoint(
    g_wf_doc, "POST", "创建/更新文档", "/api/workflow/documents/create", "创建或更新工作流文档"
)
create_endpoint(
    g_wf_doc,
    "POST",
    "导入文档",
    "/api/workflow/documents/import",
    "从 JSON envelope 导入工作流文档",
)
create_endpoint(
    g_wf_doc, "GET", "文档详情", "/api/workflow/documents/{doc_id}", "获取单个工作流文档"
)
create_endpoint(
    g_wf_doc, "PUT", "更新文档", "/api/workflow/documents/{doc_id}", "更新单个工作流文档"
)
create_endpoint(
    g_wf_doc, "DELETE", "删除文档", "/api/workflow/documents/{doc_id}", "删除单个工作流文档"
)
create_endpoint(
    g_wf_doc,
    "GET",
    "导出文档",
    "/api/workflow/documents/{doc_id}/export",
    "导出文档为 JSON envelope",
)
create_endpoint(
    g_wf_doc, "POST", "移动文档", "/api/workflow/documents/{doc_id}/move", "移动文档到新目录"
)

# ── 6. Test Runner ──
f_runner = create_folder("执行引擎", parent=ROOT, sort=6)

g_run_mgmt = create_group("运行管理", parent=f_runner, sort=0)
create_endpoint(
    g_run_mgmt,
    "POST",
    "启动测试执行",
    "/api/runner/run",
    "启动异步测试执行（返回 run_id + ws_url）",
)
create_endpoint(g_run_mgmt, "GET", "活跃运行列表", "/api/runner/active", "当前活跃的测试运行列表")
create_endpoint(
    g_run_mgmt, "POST", "取消排队任务", "/api/runner/queue/cancel", "移除设备队列中的排队任务"
)
create_endpoint(
    g_run_mgmt, "POST", "停止运行", "/api/runner/run/{run_id}/stop", "优雅停止正在运行的测试"
)
create_endpoint(
    g_run_mgmt, "GET", "运行状态", "/api/runner/run/{run_id}/status", "查询测试执行进度"
)
create_endpoint(
    g_run_mgmt, "GET", "运行历史", "/api/runner/runs", "执行历史列表（最近 50 条，可分页）"
)
create_endpoint(
    g_run_mgmt, "POST", "运行单个步骤", "/api/runner/run-step", "在当前设备上执行单个步骤（调试用）"
)

g_task = create_group("任务卡片", parent=f_runner, sort=1)
create_endpoint(g_task, "GET", "任务卡片列表", "/api/runner/tasks", "列出所有任务卡片")
create_endpoint(g_task, "POST", "保存任务卡片", "/api/runner/tasks/save", "创建或更新任务卡片")
create_endpoint(g_task, "DELETE", "删除任务卡片", "/api/runner/tasks/{task_id}", "删除任务卡片")

g_monitor = create_group("监控与快照", parent=f_runner, sort=2)
create_endpoint(
    g_monitor, "GET", "运行监控", "/api/runner/monitor/{run_id}", "运行监控流（TREP Phase 0）"
)
create_endpoint(
    g_monitor, "GET", "运行快照", "/api/runner/run/{run_id}/snapshot", "获取指定运行的详细快照"
)

# ── 7. Report Generator ──
f_report = create_folder("报告生成", parent=ROOT, sort=7)

g_rpt = create_group("报告管理", parent=f_report, sort=0)
create_endpoint(g_rpt, "GET", "报告列表", "/api/reports/", "执行运行列表（含 KPI 摘要、每日趋势）")
create_endpoint(g_rpt, "GET", "用例分解", "/api/reports/cases", "按通过/失败分类的层级用例分解")
create_endpoint(g_rpt, "GET", "单次运行报告", "/api/reports/run/{run_id}", "单次运行的完整聚合报告")
create_endpoint(
    g_rpt, "GET", "任务报告", "/api/reports/task/{task_id}", "基于 TaskCard 视角的综合报告"
)
create_endpoint(
    g_rpt,
    "GET",
    "查看报告内容",
    "/api/reports/{filename}/content",
    "在线查看报告文件（CSV 解析行）",
)
create_endpoint(
    g_rpt, "GET", "下载报告文件", "/api/reports/{filename}", "下载报告文件（CSV/MD/LOG）"
)

# ── 8. AI Assistant ──
f_ai = create_folder("AI 助手", parent=ROOT, sort=8)

g_auth = create_group("认证", parent=f_ai, sort=0)
create_endpoint(g_auth, "POST", "用户登录", "/api/ai/auth/login", "用户登录获取 JWT")
create_endpoint(g_auth, "POST", "用户注册", "/api/ai/auth/register", "新用户注册")
create_endpoint(g_auth, "POST", "刷新 Token", "/api/ai/auth/refresh", "刷新 JWT Token")
create_endpoint(g_auth, "POST", "用户登出", "/api/ai/auth/logout", "用户登出（Token 加入黑名单）")
create_endpoint(g_auth, "GET", "当前用户信息", "/api/ai/auth/me", "获取当前登录用户信息")

g_agent = create_group("Agent 管理", parent=f_ai, sort=1)
create_endpoint(g_agent, "GET", "Agent 列表", "/api/ai/agents", "列出所有 AI Agent")
create_endpoint(g_agent, "POST", "创建 Agent", "/api/ai/agents/create", "创建新的 AI Agent")
create_endpoint(g_agent, "GET", "Agent 详情", "/api/ai/agents/{agent_id}", "获取 Agent 详细信息")
create_endpoint(
    g_agent, "POST", "更新 Agent", "/api/ai/agents/{agent_id}/update", "更新 Agent 配置"
)
create_endpoint(g_agent, "DELETE", "删除 Agent", "/api/ai/agents/{agent_id}/delete", "删除 Agent")
create_endpoint(
    g_agent, "GET", "查看 API Key", "/api/ai/agents/{agent_id}/reveal-key", "查看解密后的 API Key"
)
create_endpoint(
    g_agent, "POST", "测试连接", "/api/ai/agents/{agent_id}/test", "测试 Agent 模型连通性"
)
create_endpoint(
    g_agent, "GET", "可用模型列表", "/api/ai/agents/{agent_id}/models", "获取 Agent 可用模型列表"
)
create_endpoint(
    g_agent,
    "POST",
    "注册到 AgentScope",
    "/api/ai/agents/{agent_id}/register-scope",
    "在 AgentScope 框架中注册 Agent",
)
create_endpoint(g_agent, "GET", "健康检查", "/api/ai/agents/health", "所有 Agent 健康检查")

g_conv = create_group("会话管理", parent=f_ai, sort=2)
create_endpoint(
    g_conv, "GET", "会话列表", "/api/ai/agents/{agent_id}/conversations", "列出 Agent 的对话列表"
)
create_endpoint(
    g_conv, "POST", "创建会话", "/api/ai/agents/{agent_id}/conversations/create", "创建新的对话"
)
create_endpoint(
    g_conv, "GET", "消息列表", "/api/ai/conversations/{conv_id}/messages", "列出对话中的消息"
)
create_endpoint(
    g_conv, "POST", "发送消息", "/api/ai/conversations/{conv_id}/send", "向 Agent 发送消息"
)
create_endpoint(
    g_conv,
    "POST",
    "保存消息",
    "/api/ai/conversations/{conv_id}/save-message",
    "持久化保存消息到 DB",
)
create_endpoint(
    g_conv, "GET", "SSE 流式对话", "/api/ai/conversations/{conv_id}/stream", "SSE 流式聊天端点"
)
create_endpoint(
    g_conv,
    "POST",
    "HITL 确认结果",
    "/api/ai/conversations/{conv_id}/confirm-result",
    "提交人工确认结果",
)
create_endpoint(
    g_conv,
    "POST",
    "创建 Scope 会话",
    "/api/ai/conversations/{conv_id}/create-scope-session",
    "创建 AgentScope SSE 会话",
)
create_endpoint(
    g_conv, "POST", "重命名会话", "/api/ai/conversations/{conv_id}/rename", "重命名一个对话"
)
create_endpoint(
    g_conv, "DELETE", "删除会话", "/api/ai/conversations/{conv_id}/delete", "删除一个对话"
)

g_model = create_group("模型与平台工具", parent=f_ai, sort=3)
create_endpoint(g_model, "GET", "探测模型列表", "/api/ai/models/detect", "探测并列出可用 LLM 模型")
create_endpoint(
    g_model, "GET", "默认系统提示词", "/api/ai/default-system-prompt", "获取默认系统提示词模板"
)
create_endpoint(g_model, "GET", "可用平台工具", "/api/ai/available-tools", "列出可用平台工具")
create_endpoint(
    g_model, "GET", "可用技能列表", "/api/ai/available-skills", "列出所有可用 Agent 技能"
)

g_mcp = create_group("工具副本管理", parent=f_ai, sort=4)
create_endpoint(
    g_mcp, "GET", "Agent 工具列表", "/api/ai/agents/{agent_id}/tools", "列出 Agent 已导入的工具副本"
)
create_endpoint(
    g_mcp, "POST", "开关工具", "/api/ai/agents/{agent_id}/tools/{tool_id}/toggle", "启用或禁用工具"
)
create_endpoint(
    g_mcp,
    "DELETE",
    "删除工具",
    "/api/ai/agents/{agent_id}/tools/{tool_id}/delete",
    "从 Agent 删除工具",
)

g_conv_task = create_group("对话任务", parent=f_ai, sort=5)
create_endpoint(
    g_conv_task,
    "GET",
    "会话任务列表",
    "/api/ai/conversations/{conv_id}/tasks",
    "列出对话关联的任务",
)
create_endpoint(
    g_conv_task,
    "GET",
    "会话任务详情",
    "/api/ai/conversations/{conv_id}/tasks/{run_id}",
    "获取指定对话任务详情",
)
create_endpoint(
    g_conv_task, "GET", "AI 任务看板", "/api/ai/tasks", "工作台任务看板（全部 AI 任务列表）"
)

g_kb = create_group("知识库", parent=f_ai, sort=6)
create_endpoint(g_kb, "GET", "知识库状态", "/api/ai/knowledge/status", "查询知识库状态")
create_endpoint(g_kb, "GET", "文档列表", "/api/ai/knowledge/documents", "列出知识库文档")
create_endpoint(g_kb, "GET", "文档预览", "/api/ai/knowledge/documents/preview", "预览知识库文档")
create_endpoint(g_kb, "POST", "重建索引", "/api/ai/knowledge/reindex", "重建知识库索引")
create_endpoint(g_kb, "POST", "添加文档", "/api/ai/knowledge/documents/add", "添加文档到知识库")

g_file = create_group("文件与健康检查", parent=f_ai, sort=7)
create_endpoint(g_file, "POST", "上传头像", "/api/ai/upload-avatar", "上传用户头像")
create_endpoint(g_file, "GET", "获取头像", "/api/ai/avatars/{filename}", "获取已上传头像文件")
create_endpoint(g_file, "POST", "上传解析文件", "/api/ai/upload-file", "上传并解析文件")
create_endpoint(g_file, "GET", "健康检查", "/api/ai/health", "AI 模块健康检查")

# ── 9. Evaluator ──
f_eval = create_folder("评估器", parent=ROOT, sort=9)

g_eval_bank = create_group("题库管理", parent=f_eval, sort=0)
create_endpoint(g_eval_bank, "GET", "题库列表", "/api/evaluator/banks", "列出所有题库")
create_endpoint(g_eval_bank, "POST", "创建题库", "/api/evaluator/banks/create", "创建新题库")
create_endpoint(
    g_eval_bank, "POST", "初始化默认题库", "/api/evaluator/banks/seed", "创建默认 30 题题库"
)
create_endpoint(
    g_eval_bank, "GET", "题库详情", "/api/evaluator/banks/{bank_id}", "获取题库详情及所有题目"
)
create_endpoint(
    g_eval_bank, "POST", "更新题库", "/api/evaluator/banks/{bank_id}/update", "更新题库（全量替换）"
)
create_endpoint(
    g_eval_bank, "DELETE", "删除题库", "/api/evaluator/banks/{bank_id}/delete", "删除题库"
)

g_eval_run = create_group("评估运行", parent=f_eval, sort=1)
create_endpoint(g_eval_run, "GET", "运行列表", "/api/evaluator/runs", "列出评估运行（最近 50 次）")
create_endpoint(
    g_eval_run, "POST", "启动评估", "/api/evaluator/runs/start", "启动新的评估运行（后台执行）"
)
create_endpoint(
    g_eval_run, "GET", "运行详情", "/api/evaluator/runs/{run_id}", "获取评估运行详情及结果"
)
create_endpoint(
    g_eval_run, "DELETE", "删除运行", "/api/evaluator/runs/{run_id}/delete", "删除评估运行"
)

g_eval_score = create_group("人工评分", parent=f_eval, sort=2)
create_endpoint(
    g_eval_score,
    "POST",
    "提交人工评分",
    "/api/evaluator/results/{result_id}/score",
    "提交人工维度评分",
)

g_eval_fw = create_group("框架与知识库搜索", parent=f_eval, sort=3)
create_endpoint(g_eval_fw, "GET", "框架列表", "/api/evaluator/frameworks", "列出可用评估框架")
create_endpoint(g_eval_fw, "POST", "知识库搜索", "/api/evaluator/kb-search", "交互式知识库搜索")
create_endpoint(
    g_eval_fw, "POST", "知识库自测", "/api/evaluator/kb-self-test", "测试知识库检索质量"
)

# ── 10. WebSocket ──
f_ws = create_folder("WebSocket", parent=ROOT, sort=10)
g_ws = create_group("实时通信", parent=f_ws, sort=0)
create_endpoint(g_ws, "WS", "截图流推送", "/ws/screenshot", "实时截图流，~2fps Base64 PNG 帧推送")
create_endpoint(
    g_ws,
    "WS",
    "测试执行进度",
    "/ws/test-run/{run_id}/",
    "实时测试执行进度：log/case_started/iteration_result/case_finished/run_finished/device_error",
)

# ── Stats ──
total_groups = ApiGroup.objects.count()
total_endpoints = ApiEndpoint.objects.count()
print(
    f"\nDone! Created {total_groups} groups (folders + modules) and {total_endpoints} endpoint records."
)
