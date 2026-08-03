"""API documentation — structured endpoint definitions + interactive HTML."""

import json

from django.http import HttpResponse, JsonResponse

# ═══════════════════════════════════════════════════════
# 完整接口文档数据
# ═══════════════════════════════════════════════════════

ENDPOINTS = [
    # ── element-locator (11 endpoints) ──
    {
        "module": "element-locator",
        "prefix": "/api/elements",
        "desc": "元素定位：UI dump、8种XPath策略、截图叠加层、页面跳转",
        "items": [
            {
                "method": "POST",
                "path": "/api/elements/dump",
                "desc": "Dump 当前 UI 层级并持久化到数据库",
                "body": {"action": "dump"},
                "body_desc": "空 JSON 对象即可",
                "response": {
                    "ok": "bool",
                    "page_id": "int",
                    "package": "str",
                    "activity": "str",
                    "element_count": "int",
                    "actionable_count": "int",
                    "elements": "list[dict]",
                    "actionable": "list[dict]",
                },
                "errors": [{"code": 500, "msg": "设备未连接或 uiautomator2 异常"}],
                "note": "核心操作，每次切换页面后需要调用。自动截图保存到 data/screenshots/，为每个可定位元素生成8种XPath候选",
            },
            {
                "method": "POST",
                "path": "/api/elements/action",
                "desc": "执行点击或输入操作",
                "body": {
                    "action": "click|input",
                    "x": "int",
                    "y": "int",
                    "text": "str(输入时)",
                    "clear_first": "bool",
                },
                "response": {"ok": "bool"},
                "errors": [{"code": 500, "msg": "设备未连接或操作失败"}],
                "note": "click 只需 x,y；input 需要 x,y,text,clear_first",
            },
            {
                "method": "GET",
                "path": "/api/elements/pages",
                "desc": "已 dump 的页面列表(含出入度)",
                "body": None,
                "response": {
                    "ok": "bool",
                    "pages": "list[{id,label,package,activity,element_count,created_at,flow_out,flow_in}]",
                },
                "errors": [],
                "note": "按创建时间倒序",
            },
            {
                "method": "PUT",
                "path": "/api/elements/pages/{page_id}",
                "desc": "更新页面标签",
                "body": {"label": "str"},
                "response": {"ok": "bool"},
                "errors": [],
                "note": "page_id 来自 dump 返回或页面列表",
            },
            {
                "method": "DELETE",
                "path": "/api/elements/pages/{page_id}",
                "desc": "删除页面及关联的元素和跳转",
                "body": None,
                "response": {"ok": "bool"},
                "errors": [],
                "note": "级联删除",
            },
            {
                "method": "POST",
                "path": "/api/elements/pages/clear",
                "desc": "清空全部页面/元素/跳转数据",
                "body": None,
                "response": {"ok": "bool"},
                "errors": [],
                "note": "不可逆",
            },
            {
                "method": "GET",
                "path": "/api/elements/pages/{page_id}/items",
                "desc": "页面元素列表(支持过滤)",
                "body": None,
                "response": {"ok": "bool", "elements": "list[dict]"},
                "errors": [],
                "note": "Query: ?filter=all(默认)|clickable|text|testpoint",
            },
            {
                "method": "PUT",
                "path": "/api/elements/items/{el_id}",
                "desc": "更新元素元数据",
                "body": {"alias": "str", "tags": "str", "is_test_point": "bool", "notes": "str"},
                "response": {"ok": "bool"},
                "errors": [],
                "note": "标记测试点后可在 YAML 导出中使用",
            },
            {
                "method": "GET",
                "path": "/api/elements/flows",
                "desc": "页面跳转关系列表",
                "body": None,
                "response": {
                    "ok": "bool",
                    "flows": "list[{id,from_page_id,to_page_id,from_label,to_label,trigger_text,trigger_rid}]",
                },
                "errors": [],
                "note": "LEFT JOIN 页面和元素表",
            },
            {
                "method": "POST",
                "path": "/api/elements/flows",
                "desc": "创建页面跳转记录",
                "body": {
                    "from_page_id": "int",
                    "to_page_id": "int",
                    "trigger_element_id": "int",
                    "trigger_action": "str",
                },
                "response": {"ok": "bool"},
                "errors": [],
                "note": "trigger_action 默认 click",
            },
            {
                "method": "DELETE",
                "path": "/api/elements/flows/{flow_id}",
                "desc": "删除跳转记录",
                "body": None,
                "response": {"ok": "bool"},
                "errors": [],
                "note": "",
            },
        ],
    },
    # ── device-pool (10 endpoints) ──
    {
        "module": "device-pool",
        "prefix": "/api/devices",
        "desc": "设备管理：ADB扫描、状态监控(ONLINE/BUSY/OFFLINE)、锁定释放、排队、心跳",
        "items": [
            {
                "method": "GET",
                "path": "/api/devices",
                "desc": "设备列表 + 状态 + 排队数",
                "body": None,
                "response": {
                    "ok": "bool",
                    "devices": "list[{serial,model,screen,sdk,status,locked_by,locked_at}]",
                    "current": "str",
                    "queue_length": "int",
                },
                "errors": [],
                "note": "每次调用自动触发心跳检测，同步 adb 真实状态到 DB。BUSY 设备超时自动释放",
            },
            {
                "method": "POST",
                "path": "/api/devices/scan",
                "desc": "扫描并连接设备(无线ADB或USB)",
                "body": {"address": "str (IP:port 或 USB串号)"},
                "response": {"ok": "bool", "message": "str", "serial": "str"},
                "errors": [
                    {"code": 400, "msg": "address 为空"},
                    {"code": 500, "msg": "adb 不可用"},
                ],
                "note": "包含:的地址走 adb connect；不含:的走 adb devices 查找",
            },
            {
                "method": "POST",
                "path": "/api/devices/{serial}",
                "desc": "连接设备(自动切换为当前)",
                "body": {"activate": "bool(默认true)"},
                "response": {"ok": "bool", "serial": "str", "connected": "bool"},
                "errors": [{"code": 400, "msg": "设备不可达"}],
                "note": "连接成功后自动执行 device_pool.switch_to(serial)",
            },
            {
                "method": "GET",
                "path": "/api/devices/current",
                "desc": "当前活动设备信息",
                "body": None,
                "response": {
                    "serial": "str",
                    "screen_w": "int",
                    "screen_h": "int",
                    "package": "str",
                },
                "errors": [],
                "note": "不依赖 adb，从 DevicePool 缓存读取",
            },
            {
                "method": "POST",
                "path": "/api/devices/{serial}/disconnect",
                "desc": "断开设备(同时释放锁)",
                "body": None,
                "response": {"ok": "bool"},
                "errors": [],
                "note": "无线设备执行 adb disconnect；清理 u2 连接缓存；若设备被锁则自动释放",
            },
            {
                "method": "POST",
                "path": "/api/devices/{serial}/activate",
                "desc": "切换当前活动设备",
                "body": None,
                "response": {"ok": "bool", "current": "str"},
                "errors": [],
                "note": "后续所有 dump/action 操作针对此设备",
            },
            {
                "method": "POST",
                "path": "/api/devices/{serial}/lock",
                "desc": "锁定设备(独占使用)",
                "body": {"user_id": "str", "timeout": "int(秒,默认300)"},
                "response": {"ok": "bool", "serial": "str", "locked_by": "str", "timeout": "int"},
                "errors": [{"code": 409, "msg": "设备已被其他用户锁定"}],
                "note": "锁定后设备状态变为 BUSY；超时后自动释放。同一设备重复锁定会检查超时",
            },
            {
                "method": "POST",
                "path": "/api/devices/{serial}/release",
                "desc": "释放设备锁",
                "body": None,
                "response": {"ok": "bool", "serial": "str", "status": "ONLINE"},
                "errors": [],
                "note": "状态恢复为 ONLINE；清空锁定信息；删除锁记录",
            },
            {
                "method": "GET",
                "path": "/api/devices/queue",
                "desc": "排队状态(活跃锁列表)",
                "body": None,
                "response": {
                    "ok": "bool",
                    "queue_length": "int",
                    "queue": "list[{serial,user_id,locked_at,timeout_seconds,remaining_seconds,position}]",
                },
                "errors": [],
                "note": "FIFO 排序，包含剩余超时时间",
            },
            {
                "method": "GET",
                "path": "/api/devices/heartbeat",
                "desc": "手动触发心跳检测",
                "body": None,
                "response": {
                    "ok": "bool",
                    "online": "int",
                    "busy": "int",
                    "offline": "int",
                    "total": "int",
                },
                "errors": [],
                "note": "检查所有已注册设备状态，同步 adb 真实连接，清理过期锁。前端每30秒自动调用",
            },
        ],
    },
    # ── case-manager (8 endpoints) ──
    {
        "module": "case-manager",
        "prefix": "/api/cases",
        "desc": "用例工程：用例CRUD、步骤编排(14种)、YAML导出、测试套件",
        "items": [
            {
                "method": "GET",
                "path": "/api/cases/definitions",
                "desc": "测试用例定义列表",
                "body": None,
                "response": {
                    "ok": "bool",
                    "definitions": "list[{id,title,category,description,steps,enabled,steps_data,package_name,created_at,updated_at}]",
                },
                "errors": [],
                "note": "steps_data 是 TestStep 对象数组，按 category+title 排序",
            },
            {
                "method": "POST",
                "path": "/api/cases/definitions",
                "desc": "创建或更新用例定义",
                "body": {
                    "id": "str(必填)",
                    "title": "str",
                    "category": "str",
                    "description": "str",
                    "steps_data": "list",
                    "enabled": "bool",
                    "package_name": "str",
                },
                "response": {"ok": "bool", "id": "str"},
                "errors": [{"code": 400, "msg": "id 为空"}],
                "note": "id 已存在则更新，不存在则插入。steps_data 为 TestStep JSON 数组",
            },
            {
                "method": "GET",
                "path": "/api/cases/definitions/{case_id}",
                "desc": "单个用例详情",
                "body": None,
                "response": {"ok": "bool", "definition": "dict"},
                "errors": [{"code": 404, "msg": "case_id 不存在"}],
                "note": "",
            },
            {
                "method": "DELETE",
                "path": "/api/cases/definitions/{case_id}",
                "desc": "删除用例定义",
                "body": None,
                "response": {"ok": "bool"},
                "errors": [],
                "note": "",
            },
            {
                "method": "POST",
                "path": "/api/cases/export/yaml",
                "desc": "导出测试点为 YAML 文件",
                "body": {"test_case_name": "str", "page_ids": "list[int]"},
                "response": {"ok": "bool", "filename": "str", "yaml": "str"},
                "errors": [],
                "note": "收集标记为 is_test_point 的元素，生成 YAML 格式测试用例。同时缓存在 cm_test_cases 表",
            },
            {
                "method": "GET",
                "path": "/api/cases/exports",
                "desc": "已导出的 YAML 文件列表",
                "body": None,
                "response": {"ok": "bool", "files": "list[{name,size,time}]"},
                "errors": [],
                "note": "按时间倒序",
            },
            {
                "method": "GET",
                "path": "/api/cases/exports/{filename}",
                "desc": "下载 YAML 导出文件",
                "body": None,
                "response": "FileResponse (application/x-yaml)",
                "errors": [{"code": 404, "msg": "文件不存在"}],
                "note": "不是 JSON 响应，前端需用 fetch().then(r=>r.text())",
            },
            {
                "method": "POST",
                "path": "/api/cases/suites",
                "desc": "创建测试套件 (v2)",
                "body": "待定义",
                "response": "待定义",
                "errors": [],
                "note": "⏳ v2 计划",
            },
        ],
    },
    # ── test-runner (4 endpoints) ──
    {
        "module": "test-runner",
        "prefix": "/api/runner",
        "desc": "执行引擎：异步测试执行、14种步骤类型、WebSocket 实时进度、CSV/MD报告",
        "items": [
            {
                "method": "POST",
                "path": "/api/runner/run",
                "desc": "启动测试执行(异步)",
                "body": {
                    "case_ids": "list[str]",
                    "loop_count": "int(默认10)",
                    "package_name": "str",
                },
                "response": {
                    "ok": "bool",
                    "run_id": "str",
                    "case_count": "int",
                    "loop_count": "int",
                    "ws_url": "str",
                },
                "errors": [
                    {"code": 400, "msg": "case_ids 为空"},
                    {"code": 404, "msg": "无启用的用例"},
                ],
                "note": "核心端点。后台 asyncio.create_task() 异步执行，立即返回 run_id。通过 ws_url 建立 WebSocket 接收实时进度",
            },
            {
                "method": "POST",
                "path": "/api/runner/run/{run_id}/stop",
                "desc": "停止运行中的测试",
                "body": None,
                "response": {"ok": "bool", "message": "str"},
                "errors": [{"code": 404, "msg": "run_id 不存在或已结束"}],
                "note": "优雅停止：当前步骤完成后终止",
            },
            {
                "method": "GET",
                "path": "/api/runner/run/{run_id}/status",
                "desc": "查询测试执行进度",
                "body": None,
                "response": {
                    "ok": "bool",
                    "status": "str(pending|running|stopped|completed)",
                    "is_running": "bool",
                    "selected_cases": "list",
                    "loop_count": "int",
                    "started_at": "str",
                },
                "errors": [{"code": 404, "msg": "运行记录未找到"}],
                "note": "优先查活跃运行(内存)，其次查历史 DB",
            },
            {
                "method": "GET",
                "path": "/api/runner/runs",
                "desc": "执行历史列表(最近50条)",
                "body": None,
                "response": {"ok": "bool", "runs": "list[{run_id,total,passed,failed,last_time}]"},
                "errors": [],
                "note": "从 tr_test_results 表聚合统计",
            },
        ],
    },
    # ── report-generator (2 endpoints) ──
    {
        "module": "report-generator",
        "prefix": "/api/reports",
        "desc": "报告分析：CSV/MD/JSON 报告浏览与下载",
        "items": [
            {
                "method": "GET",
                "path": "/api/reports",
                "desc": "可下载的报告文件列表",
                "body": None,
                "response": {"ok": "bool", "files": "list[{name,size,time,type}]"},
                "errors": [],
                "note": "type: csv|md|log。从 logs/ 目录扫描 result_* 前缀文件",
            },
            {
                "method": "GET",
                "path": "/api/reports/{filename}",
                "desc": "下载报告文件",
                "body": None,
                "response": "FileResponse (text/csv|text/markdown|text/plain)",
                "errors": [{"code": 404, "msg": "文件不存在"}],
                "note": "不是 JSON。前端用 fetch().then(r=>r.text())。文件名自动防目录遍历",
            },
        ],
    },
    # ── dashboard (4 endpoints) ──
    {
        "module": "dashboard",
        "prefix": "/api",
        "desc": "仪表盘：平台聚合统计、活动时间线",
        "items": [
            {
                "method": "GET",
                "path": "/api/dashboard/stats",
                "desc": "平台聚合统计数据",
                "body": None,
                "response": {
                    "ok": "bool",
                    "data": {
                        "devices": {"online": "int", "total": "int", "trend": "int"},
                        "cases": {
                            "total": "int",
                            "enabled": "int",
                            "trend": "int",
                            "breakdown": "[{type,label,total,enabled}] (Android/Web/API/功能业务)",
                        },
                        "elements": {
                            "total": "int",
                            "pages": "int",
                            "type_breakdown": "[{type,label,total}] (Android元素/Web元素/API接口)",
                        },
                        "workflow": {"total": "int", "page_flows": "int", "test_cases": "int"},
                        "runs": {"total": "int", "active": "int", "trend": "int"},
                        "agents": {"total": "int", "active": "int", "trend": "int"},
                        "reports": {"total": "int"},
                        "pass_rate": "float",
                        "charts": {
                            "execution": {
                                "labels": "[str]",
                                "success": "[int]",
                                "failed": "[int]",
                                "new_cases": "[int]",
                            }
                        },
                        "execution_summary": {
                            "passed": "int",
                            "failed": "int",
                            "new_cases_week": "int",
                        },
                        "recent_tasks": "[{id,title,status,passed,failed,total,time,cases}]",
                        "last_updated": "str",
                        "system_status": "str(normal|no_devices)",
                    },
                },
                "errors": [],
                "note": "跨 7 个模块聚合：device_pool、case_manager、element_locator、test_runner、ai_assistant、report_generator、workflow",
            },
            {
                "method": "GET",
                "path": "/api/dashboard/activities",
                "desc": "最近平台活动时间线",
                "body": None,
                "response": {"ok": "bool", "data": "[{type,action,detail,time}]"},
                "errors": [],
                "note": "最近 5 次执行 + 3 个智能体更新，按时间倒序",
            },
            {
                "method": "GET",
                "path": "/api/devices/stats",
                "desc": "设备池摘要统计",
                "body": None,
                "response": {
                    "ok": "bool",
                    "data": {
                        "online": "int",
                        "busy": "int",
                        "offline": "int",
                        "disconnected": "int",
                        "total": "int",
                    },
                },
                "errors": [],
                "note": "与仪表盘主接口的设备统计逻辑一致",
            },
            {
                "method": "GET",
                "path": "/api/cases/stats",
                "desc": "用例摘要统计",
                "body": None,
                "response": {
                    "ok": "bool",
                    "data": {"total": "int", "enabled": "int", "disabled": "int"},
                },
                "errors": [],
                "note": "涵盖全部 4 种用例类型：Android(ui_automation)、Web、API、功能业务(storage)",
            },
        ],
    },
    # ── WebSocket (2 endpoints) ──
    {
        "module": "websocket",
        "prefix": "/ws",
        "desc": "WebSocket 实时推送",
        "items": [
            {
                "method": "WS",
                "path": "/ws/screenshot",
                "desc": "实时截图流 2fps",
                "body": None,
                "response": 'S→C: {"type":"screenshot","image":"<base64 PNG>"}',
                "errors": [],
                "note": "连接后自动开始推送。无客户端时停止截图。Vite proxy 已配置",
            },
            {
                "method": "WS",
                "path": "/ws/test-run/{run_id}",
                "desc": "测试执行实时进度",
                "body": None,
                "response": "6 种消息: log|case_started|iteration_result|case_finished|run_finished|device_error",
                "errors": [],
                "note": "run_id 来自 POST /api/runner/run 返回值。断开连接后回调自动清理",
            },
        ],
    },
]


def api_docs_json(request):
    """GET /api/docs — JSON 格式完整接口文档."""
    return JsonResponse(
        {
            "ok": True,
            "service": "Android-AutoTests API",
            "version": "v2.0",
            "base_url": "http://localhost:8765",
            "modules": 6,
            "endpoints": 39,
            "websockets": 2,
            "conventions": {
                "wrapper": '{"ok": true/false, ...}',
                "field_style": "snake_case",
                "content_type": "application/json",
                "error_format": '{"ok": false, "error": "描述"}',
            },
            "modules_detail": ENDPOINTS,
        },
        json_dumps_params={"ensure_ascii": False, "indent": 2},
    )


def api_docs_html(request):
    """GET /api/docs.html — 可点击展开的交互式接口文档."""
    docs_json = json.dumps(ENDPOINTS, ensure_ascii=False)
    docs_json = json.dumps(ENDPOINTS, ensure_ascii=False)
    html = """<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>API Docs · Android-AutoTests</title>
<style>
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Quicksand:wght@500;600;700&display=swap');
  :root{{--bg:linear-gradient(45deg,#ffc8dd,#bde0fe,#a2d2ff);--glass:rgba(255,255,255,0.45);--border:rgba(255,255,255,0.6);--text:#4a4e69;--sub:#9a8c98;--font-sans:"Inter","Microsoft YaHei","Noto Sans SC","DengXian",-apple-system,"Segoe UI",Roboto,"Quicksand",sans-serif;--font-display:"Quicksand","Inter","Microsoft YaHei","Noto Sans SC",-apple-system,sans-serif;--font-mono:"Consolas","Source Code Pro","Courier New","Microsoft YaHei",monospace}}
  *{{margin:0;padding:0;box-sizing:border-box}}
  body{{font-family:var(--font-sans);min-height:100vh;background:var(--bg);background-size:200% 200%;animation:gradientBG 15s ease infinite;padding:40px 20px;-webkit-font-smoothing:antialiased}}
  @keyframes gradientBG{{0%{{background-position:0% 50%}}50%{{background-position:100% 50%}}100%{{background-position:0% 50%}}}}
  .container{{max-width:1150px;margin:0 auto}}
  .header{{background:var(--glass);backdrop-filter:blur(20px);border-radius:24px;border:1px solid var(--border);padding:28px 32px;margin-bottom:20px;box-shadow:0 8px 32px rgba(31,38,135,0.07)}}
  .header h1{{font-size:24px;font-weight:700;color:var(--text);font-family:var(--font-display)}}
  .header .sub{{font-size:13px;color:var(--sub);margin-top:4px}}
  .toolbar{{display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap}}
  .toolbar button{{padding:8px 18px;border-radius:50px;border:1px solid var(--border);background:var(--glass);backdrop-filter:blur(12px);cursor:pointer;font-size:12px;font-weight:600;font-family:var(--font-sans);color:var(--text);transition:all .2s}}
  .toolbar button:hover{{background:rgba(255,255,255,0.7);transform:translateY(-1px)}}
  .toolbar button.active{{background:var(--text);color:#fff;border-color:var(--text)}}
  .module{{margin-bottom:14px;border-radius:16px;overflow:hidden}}
  .module-header{{background:rgba(74,78,105,0.85);backdrop-filter:blur(16px);color:#fff;padding:14px 20px;cursor:pointer;display:flex;justify-content:space-between;align-items:center;font-size:14px;font-weight:600;font-family:var(--font-display);user-select:none;transition:all .2s}}
  .module-header:hover{{background:rgba(74,78,105,0.95)}}
  .module-header .arrow{{transition:transform .3s;font-size:11px}}
  .module-header.open .arrow{{transform:rotate(90deg)}}
  .module-desc{{font-size:11px;opacity:.7;margin-top:4px;font-weight:400;font-family:var(--font-sans)}}
  .ep-list{{display:none}}
  .ep-list.open{{display:block}}
  .ep{{background:var(--glass);backdrop-filter:blur(12px);border-bottom:1px solid rgba(255,255,255,0.25);cursor:pointer;transition:all .2s}}
  .ep:hover{{background:rgba(255,255,255,0.6)}}
  .ep:last-child{{border-radius:0 0 16px 16px}}
  .ep-row{{display:flex;align-items:center;gap:12px;padding:12px 20px}}
  .method{{min-width:52px;padding:4px 8px;border-radius:8px;text-align:center;font-size:11px;font-weight:700;font-family:var(--font-sans)}}
  .m-GET{{background:rgba(184,232,198,0.6);color:#1a5c2a}}
  .m-POST{{background:rgba(162,210,255,0.6);color:#1c4a7a}}
  .m-PUT{{background:rgba(255,218,185,0.6);color:#7a4c1c}}
  .m-DELETE{{background:rgba(255,192,203,0.6);color:#7a1c2b}}
  .m-WS{{background:rgba(200,180,255,0.6);color:#3a1c7a}}
  .path{{font-family:var(--font-mono);color:var(--text);font-weight:500;flex:1;font-size:13px}}
  .ep-desc{{color:var(--sub);font-size:12px;font-family:var(--font-sans)}}
  .ep-detail{{display:none;padding:0 20px 16px 84px;font-size:12px}}
  .ep-detail.open{{display:block}}
  .detail-section{{margin-top:10px}}
  .detail-label{{font-weight:600;color:var(--text);font-size:11px;margin-bottom:4px;font-family:var(--font-sans)}}
  .detail-json{{background:rgba(30,30,40,0.9);color:#a2d2ff;border-radius:10px;padding:10px 14px;font-family:var(--font-mono);font-size:12px;overflow-x:auto;white-space:pre}}
  .detail-table{{width:100%;border-collapse:collapse;font-size:11px}}
  .detail-table th{{text-align:left;padding:4px 8px;color:var(--sub);font-weight:500;border-bottom:1px solid rgba(0,0,0,0.06)}}
  .detail-table td{{padding:4px 8px;color:var(--text);font-family:var(--font-mono)}}
  .error-code{{display:inline-block;background:rgba(255,192,203,0.4);color:#7a1c2b;padding:1px 6px;border-radius:4px;font-size:10px;font-weight:700;margin-right:6px}}
  .note-box{{background:rgba(162,210,255,0.2);border-left:3px solid var(--accent-blue);border-radius:0 8px 8px 0;padding:8px 12px;color:var(--text);font-size:11px;line-height:1.5}}
  .curl-box{{background:rgba(30,30,40,0.95);color:#bde0fe;border-radius:10px;padding:10px 14px;font-family:var(--font-mono);font-size:11px;overflow-x:auto;white-space:pre;margin-top:8px}}
  .footer{{text-align:center;margin-top:32px;font-size:11px;color:var(--sub);font-family:var(--font-sans)}}
  .footer a{{color:var(--sub);text-decoration:underline}}
</style></head>
<body>
<div class="container">
  <div class="header">
    <h1>Android-AutoTests API</h1>
    <p class="sub">v2.0 · 6 个模块 · 39 个 REST 端点 + 2 个 WebSocket · 所有响应: {"ok": true/false, ...}</p>
  </div>
  <div class="toolbar">
    <button class="active" onclick="expandAll()">展开全部</button>
    <button onclick="collapseAll()">折叠全部</button>
    <button onclick="filterMethod('')">全部方法</button>
    <button onclick="filterMethod('GET')">GET</button>
    <button onclick="filterMethod('POST')">POST</button>
    <button onclick="filterMethod('PUT')">PUT</button>
    <button onclick="filterMethod('DELETE')">DELETE</button>
    <button onclick="filterMethod('WS')">WebSocket</button>
  </div>
  <div id="modules"></div>
  <div class="footer">Android-AutoTests v2.0 · <a href="/api/docs">JSON Docs</a> · <a href="/admin/">Django Admin</a> · VUE_API_CONTRACT.md</div>
</div>
<script>
const DATA = __DOCS_JSON__;

function esc(s){{return String(s).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;')}}

function formatJSON(obj){{
  if(!obj) return '';
  if(typeof obj==='string') return obj;
  return JSON.stringify(obj,null,2);
}}

function curlCmd(method,path,body){{
  var base='http://localhost:8765';
  var cmd='curl -X '+method+' '+base+path;
  if(method==='POST'||method==='PUT') cmd+=" -H 'Content-Type: application/json'";
  if(body) cmd+=" -d '"+JSON.stringify(body)+"'";
  else if(method==='POST'||method==='PUT') cmd+=" -d '{{}}'";
  return cmd;
}}

function renderFieldTable(fields){{
  if(!fields||typeof fields!=='object') return '';
  var rows=Object.entries(fields).map(function(e){{return '<tr><td>'+esc(e[0])+'</td><td>'+esc(String(e[1]))+'</td></tr>'}}).join('');
  return '<table class="detail-table"><tr><th>字段</th><th>类型/说明</th></tr>'+rows+'</table>';
}}

function renderErrors(errs){{
  if(!errs||!errs.length) return '<span style="color:var(--sub)">无特定错误码</span>';
  return errs.map(function(e){{return '<span class="error-code">'+e.code+'</span> '+esc(e.msg)}}).join('<br>');
}}

function buildModules(){{
  var html='';
  DATA.forEach(function(mod){{
    html+='<div class="module">';
    html+='<div class="module-header" onclick="this.classList.toggle(\'open\');this.nextElementSibling.classList.toggle(\'open\')">';
    html+='<div><span class="arrow">▶</span> '+esc(mod.module)+' <span style="font-size:12px;opacity:.7;font-weight:400">'+esc(mod.prefix)+'</span><div class="module-desc">'+esc(mod.desc||'')+'</div></div>';
    html+='<span style="font-size:12px;opacity:.7">'+mod.items.length+' 端点</span></div>';
    html+='<div class="ep-list">';
    mod.items.forEach(function(ep,i){{
      var id=mod.module.replace(/[^a-z]/g,'')+i;
      html+='<div class="ep" data-method="'+ep.method+'">';
      html+='<div class="ep-row" onclick="this.parentElement.querySelector(\'.ep-detail\').classList.toggle(\'open\')">';
      html+='<span class="method m-'+ep.method+'">'+ep.method+'</span>';
      html+='<span class="path">'+esc(ep.path)+'</span>';
      html+='<span class="ep-desc">'+esc(ep.desc)+'</span>';
      html+='<span style="font-size:18px;color:var(--sub);transition:transform .2s">▾</span></div>';
      html+='<div class="ep-detail">';

      if(ep.note) html+='<div class="note-box">📝 '+esc(ep.note)+'</div>';

      html+='<div class="detail-section"><div class="detail-label">cURL 命令</div>';
      html+='<div class="curl-box">'+esc(curlCmd(ep.method,ep.path,ep.body))+'</div></div>';

      html+='<div class="detail-section"><div class="detail-label">请求体 '+(ep.body?'(application/json)':'(无)')+'</div>';
      if(ep.body){{html+='<div class="detail-json">'+esc(formatJSON(ep.body))+'</div>';
        if(ep.body_desc) html+='<div style="color:var(--sub);margin-top:4px">'+esc(ep.body_desc)+'</div>';
      }}else{{html+='<div style="color:var(--sub)">此端点无请求体</div>';}}
      html+='</div>';

      html+='<div class="detail-section"><div class="detail-label">响应字段</div>';
      html+=renderFieldTable(ep.response);
      html+='</div>';

      html+='<div class="detail-section"><div class="detail-label">错误码</div>';
      html+=renderErrors(ep.errors);
      html+='</div>';

      html+='</div></div>';
    }});
    html+='</div></div>';
  }});
  document.getElementById('modules').innerHTML=html;
}}

function expandAll(){{document.querySelectorAll('.module-header').forEach(function(h){{h.classList.add('open')}});document.querySelectorAll('.ep-list').forEach(function(l){{l.classList.add('open')}});document.querySelectorAll('.ep-detail').forEach(function(d){{d.classList.add('open')}})}}
function collapseAll(){{document.querySelectorAll('.module-header').forEach(function(h){{h.classList.remove('open')}});document.querySelectorAll('.ep-list').forEach(function(l){{l.classList.remove('open')}});document.querySelectorAll('.ep-detail').forEach(function(d){{d.classList.remove('open')}})}}
function filterMethod(m){{document.querySelectorAll('.toolbar button').forEach(function(b){{b.classList.remove('active')}});event.target.classList.add('active');document.querySelectorAll('.ep').forEach(function(e){{e.style.display=m&&e.dataset.method!==m?'none':''}})}};

buildModules();
</script>
</body></html>"""
    html = html.replace("__DOCS_JSON__", docs_json)
    return HttpResponse(html, content_type="text/html; charset=utf-8")
