"""Import all H717D smart ice maker test cases into the storage case table.

Reads existing 239 cases from the H717D document library HTML and 32 new
cases from dev_docs/H717D/测试用例/, then creates directories and imports
all 271 cases into cm_storage_testcases.

Usage:
    python manage.py import_h717d_cases [--dry-run] [--overwrite]

Directory structure created:
    H717D (root)
    ├── 按键功能用例设计 (42)
    ├── 指示灯功能用例设计 (51)
    ├── 出厂状态用例设计 (35)
    ├── 联网与配网用例设计 (14)
    ├── 蓝牙控制记忆时钟用例设计 (10)
    ├── 制冰轮次记录用例设计 (15)
    ├── 冰篮灯用例设计 (11)
    ├── 缺水满冰保护用例设计 (25)
    ├── 预约定时用例设计 (28)
    ├── 蓝牙连接补充 (3)
    ├── WiFi配网补充 (2)
    ├── WiFi断网重连补充 (2)
    ├── 蓝牙控制补充 (2)
    ├── 记忆功能补充 (1)
    ├── 制冰轮次补充 (1)
    ├── 时钟刷新 (3)
    ├── 分布式网关 (2)
    ├── NTC故障 (4)
    ├── 脱冰除霜 (3)
    ├── 制冰图表 (4)
    ├── 制冰日志 (3)
    └── E2E集成用例 (2)
"""

import json
import os
import re
import sys
from collections import OrderedDict
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction

from apps.case_manager.models import CaseDirectory
from apps.case_manager.models_storage import StorageTestCase

# ── Paths ─────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent.parent
DOC_LIB_HTML = Path(os.environ.get(
    "H717D_DOC_HTML",
    r"C:\Users\zhiyan\Downloads\H717D_文档库.html",
))
NEW_CASES_DIR = PROJECT_ROOT / "dev_docs" / "H717D" / "测试用例"


# ═══════════════════════════════════════════════════════════
# Part 1: Parse existing 239 cases from HTML document library
# ═══════════════════════════════════════════════════════════

def _extract_file_data(html_path: str) -> dict:
    """Extract the FILE_DATA JS object from the HTML document library.

    Uses a line-by-line state machine to handle very long content strings
    (up to 100K chars per line) that would break regex-based approaches.
    """
    with open(html_path, "r", encoding="utf-8") as f:
        lines = f.readlines()

    # Find the FILE_DATA block boundaries
    data_start = None
    data_end = None
    in_block = False
    brace_depth = 0
    for i, line in enumerate(lines):
        if "const FILE_DATA = {" in line:
            in_block = True
            brace_depth = line.count("{") - line.count("}")
            continue
        if in_block:
            brace_depth += line.count("{") - line.count("}")
            if brace_depth <= 0 and ("};" in line or (brace_depth == 0 and "}" in line.strip())):
                data_end = i
                break

    if data_end is None:
        return {}

    # Extract file entries using a line-based state machine
    # Each file entry looks like:
    #   "file_N": {
    #     "name": "...",
    #     "path": "...",
    #     "content": "...",   <-- very long single line, may span entire file
    #     "html": "...",       <-- very long single line
    #   },

    files = {}
    current_idx = None
    current_name = None
    current_path = None

    for i in range(data_start or 0, data_end + 1):
        line = lines[i]
        stripped = line.strip()

        # Match: "file_N": {
        fm = re.match(r'"file_(\d+)":\s*\{', stripped)
        if fm:
            current_idx = int(fm.group(1))
            current_name = None
            current_path = None
            continue

        if current_idx is None:
            continue

        # Match: "name": "...",
        nm = re.match(r'"name":\s*"([^"]*)",?\s*$', stripped)
        if nm:
            current_name = nm.group(1)
            continue

        # Match: "path": "...",
        pm = re.match(r'"path":\s*"([^"]*)",?\s*$', stripped)
        if pm:
            current_path = pm.group(1)
            continue

        # Match: "content": "<escaped string>",
        # The content field is very long, use a state-machine extractor
        cm = re.match(r'"content":\s*"(.*)', stripped)
        if cm:
            content = cm.group(1)
            # Check if the string ends on this line (with " or ",)
            # We need to handle the escaping: \" is an escaped quote, not the end
            if not _is_string_complete(content):
                # Multi-line content — accumulate until we find the end
                for j in range(i + 1, data_end + 1):
                    content += "\n" + lines[j].rstrip("\n")
                    if _is_string_complete(content):
                        break
            # Strip trailing "," or ", (the closing quote + comma)
            content = _strip_js_string_end(content)
            # Unescape JS
            content = _unescape_js(content)
            files[current_idx] = {
                "name": current_name or f"file_{current_idx}",
                "path": current_path or "",
                "content": content,
            }
            current_idx = None  # done with this file
            continue

    return files


def _is_string_complete(s: str) -> bool:
    r"""Check if a JS string is properly terminated (odd number of \ is escape)."""
    # Walk backwards from end, count consecutive backslashes
    i = len(s) - 1
    while i >= 0 and s[i] in ('"', ','):
        i -= 1
    # Now at the last non-quote/comma char
    # Look for the closing unescaped quote
    j = len(s) - 1
    while j >= 0:
        if s[j] == '"':
            # Check if this quote is escaped
            backslash_count = 0
            k = j - 1
            while k >= 0 and s[k] == '\\':
                backslash_count += 1
                k -= 1
            if backslash_count % 2 == 0:
                return True  # Unescaped quote found
        j -= 1
    return False


def _strip_js_string_end(s: str) -> str:
    """Remove trailing JS string terminator (",) or (")."""
    s = s.rstrip()
    # Remove trailing comma if present
    while s.endswith(",") or s.endswith('"'):
        s = s[:-1]
    return s


def _unescape_js(s: str) -> str:
    """Unescape a JavaScript string (JSON-compatible escaping)."""
    s = s.replace("\\n", "\n").replace("\\t", "\t").replace('\\"', '"')
    s = s.replace("\\\\", "\\").replace("\\r", "\r")
    return s


def _parse_markdown_table(content: str) -> list[dict]:
    """Parse a GFM pipe table from markdown text. Returns list of row dicts."""
    lines = content.split("\n")

    # Find table header
    header_idx = None
    for i, line in enumerate(lines):
        if line.strip().startswith("|") and "用例编号" in line:
            header_idx = i
            break

    if header_idx is None:
        return []

    # Parse header
    headers = [h.strip() for h in lines[header_idx].split("|")[1:-1]]

    # Skip separator row (|:--:|:--:|...)
    sep_idx = header_idx + 1
    if sep_idx < len(lines) and "---" in lines[sep_idx]:
        pass  # skip it
    else:
        sep_idx = header_idx

    # Parse data rows
    rows = []
    for line in lines[sep_idx + 1:]:
        line = line.strip()
        if not line.startswith("|"):
            break
        cells = [c.strip() for c in line.split("|")[1:-1]]
        if len(cells) < len(headers):
            # Pad missing cells
            cells += [""] * (len(headers) - len(cells))
        cells = cells[:len(headers)]

        row = dict(zip(headers, cells))
        rows.append(row)

    return rows


def _parse_existing_cases(html_path: str) -> list[dict]:
    """Parse all existing test cases from the H717D document library HTML."""
    file_data = _extract_file_data(html_path)
    if not file_data:
        print("[WARN] Could not extract FILE_DATA from HTML document library.")
        return []

    # Module mapping: file_data index → (module_name, is_design_doc)
    # Design docs (odd indices after file_4) are skipped; test case docs (even) are parsed
    # From the HTML structure:
    #   file_4  = 冰篮灯测试用例
    #   file_5  = 冰篮灯用例设计思路  (skip - design doc)
    #   file_6  = 出厂状态测试用例
    #   file_7  = 出厂状态用例设计思路 (skip)
    #   file_8  = 制冰轮次记录测试用例
    #   file_9  = 制冰轮次记录用例设计思路 (skip)
    #   file_10 = 指示灯功能测试用例
    #   file_11 = 指示灯功能用例设计思路 (skip)
    #   file_12 = 按键功能测试用例
    #   file_13 = 按键功能用例设计思路 (skip)
    #   file_14 = 缺水满冰保护测试用例
    #   file_15 = 缺水满冰保护用例设计思路 (skip)
    #   file_16 = 联网与配网测试用例
    #   file_17 = 联网与配网用例设计思路 (skip)
    #   file_18 = 蓝牙控制记忆时钟测试用例
    #   file_19 = 蓝牙控制记忆时钟用例设计思路 (skip)
    #   file_20 = 预约定时测试用例
    #   file_21 = 预约定时用例设计思路 (skip)

    # Test case file indices: 4, 6, 8, 10, 12, 14, 16, 18, 20
    # Map each to directory name
    module_map = {
        4: "冰篮灯用例设计",
        6: "出厂状态用例设计",
        8: "制冰轮次记录用例设计",
        10: "指示灯功能用例设计",
        12: "按键功能用例设计",
        14: "缺水满冰保护用例设计",
        16: "联网与配网用例设计",
        18: "蓝牙控制记忆时钟用例设计",
        20: "预约定时用例设计",
    }

    all_cases = []
    for file_idx, module_name in module_map.items():
        entry = file_data.get(file_idx)
        if not entry:
            print(f"  [WARN] file_{file_idx} not found in FILE_DATA")
            continue

        rows = _parse_markdown_table(entry["content"])
        if not rows:
            print(f"  [WARN] No table found in {entry['name']}")
            continue

        for row in rows:
            # Skip summary/total rows
            case_id = row.get("用例编号", row.get("#", "")).strip()
            if not case_id or case_id in ("—", "**合计**", "合计"):
                continue
            if not case_id.startswith("TC-"):
                continue

            case = {
                "id": case_id,
                "title": row.get("测试标题", "").strip(),
                "module": module_name,
                "priority": row.get("优先级", "P1").strip(),
                "design_method": row.get("方法", "").strip(),
                "precondition": row.get("前置条件", "").strip(),
                "steps": row.get("测试步骤", "").strip(),
                "expected_result": row.get("预期结果", "").strip(),
                "metrics": row.get("量化指标", "—").strip(),
            }

            # Clean up
            if case["metrics"] in ("—", "-", ""):
                case["metrics"] = ""

            all_cases.append(case)

    return all_cases


# ═══════════════════════════════════════════════════════════
# Part 2: New 32 test case data
# ═══════════════════════════════════════════════════════════

def _get_new_cases_data() -> list[dict]:
    """Return the 32 new test cases as structured data."""
    cases = []

    # ── 蓝牙连接补充 (3) ──
    cases.extend([
        {
            "id": "TC-H717D-BLE-V2-001",
            "title": "蓝牙广播 19min50s 边界值",
            "module": "蓝牙连接补充",
            "priority": "P1",
            "design_method": "边界值+场景流",
            "precondition": "设备首次上电未配网",
            "steps": "1. 上电启动秒表\n2. 19min49s 确认 WiFi 慢闪\n3. 19min50s 观察 WiFi\n4. 确认进入普通待机",
            "expected_result": "19min49s: WiFi 白色慢闪中；19min50s(±5s): WiFi 熄灭；设备进入普通待机",
            "metrics": "超时=19min50s±5s",
            "req_id": "REQ-FW-009a",
            "complexity": "L2",
            "check_point": "确认不是 19min 或 20min",
        },
        {
            "id": "TC-H717D-BLE-V2-002",
            "title": "A/B 手机蓝牙抢占",
            "module": "蓝牙连接补充",
            "priority": "P1",
            "design_method": "协议测试+场景流",
            "precondition": "A手机已蓝牙连接设备",
            "steps": "1. B手机 APP 搜索设备\n2. B手机尝试连接\n3. 观察 A手机连接状态\n4. 观察设备指示灯",
            "expected_result": "B手机无法连接（A已独占）；A手机连接不受影响；设备蓝牙状态不变",
            "metrics": "—",
            "req_id": "REQ-FW-012a",
            "complexity": "L2",
            "check_point": "排他锁生效，不被 B 抢走",
        },
        {
            "id": "TC-H717D-BLE-V2-003",
            "title": "配网按键验证 30s 超时",
            "module": "蓝牙连接补充",
            "priority": "P1",
            "design_method": "边界值+错误推测",
            "precondition": "APP 发起蓝牙配对，进入按键验证流程",
            "steps": "1. APP 发起配对→提示按 POWER\n2. 不按键，等待 30s\n3. 观察 WiFi 灯+APP 状态\n4. 再按 POWER→确认按键功能恢复",
            "expected_result": "30s 内未按键: WiFi 停止快闪(0.5s)，APP 退出配对页；按键恢复正常功能(非配网验证态)",
            "metrics": "超时=30s±2s",
            "req_id": "REQ-FW-009c",
            "complexity": "L2",
            "check_point": "超时后按键功能恢复验证关键",
        },
    ])

    # ── WiFi配网补充 (2) ──
    cases.extend([
        {
            "id": "TC-H717D-WiFi-V2-001",
            "title": "WiFi 配网密码错误→回连前 WiFi",
            "module": "WiFi配网补充",
            "priority": "P1",
            "design_method": "协议测试+错误推测",
            "precondition": "设备已连接 WiFi-A（密码正确）",
            "steps": "1. APP 发送 WiFi-B + 错误密码\n2. 等待配网超时 60s\n3. 观察 WiFi 指示灯\n4. APP 查看设备在线状态",
            "expected_result": "配网失败→WiFi 指示灯熄灭→设备回连 WiFi-A→APP 显示设备在线(WiFi-A)",
            "metrics": "回连 WiFi-A ≤60s",
            "req_id": "REQ-FW-010f",
            "complexity": "L2",
            "check_point": "验证不回连错误密码而是回连前 WiFi",
        },
        {
            "id": "TC-H717D-WiFi-V2-002",
            "title": "WiFi 配网 60s 超时",
            "module": "WiFi配网补充",
            "priority": "P1",
            "design_method": "边界值+协议测试",
            "precondition": "设备蓝牙已连接，WiFi信息正确但路由器不响应",
            "steps": "1. APP 发送 WiFi 信息\n2. 故意让路由器不响应(关路由器)\n3. 秒表计时 60s\n4. 观察 WiFi 指示灯+APP 提示",
            "expected_result": "60s(±5s) 后: WiFi 指示灯熄灭；APP 提示\"配网超时\"+失败原因",
            "metrics": "超时=60s±5s",
            "req_id": "REQ-FW-010a",
            "complexity": "L2",
            "check_point": "超时后设备状态(是否回到蓝牙广播)",
        },
    ])

    # ── WiFi断网重连补充 (2) ──
    cases.extend([
        {
            "id": "TC-H717D-WiFi-V2-003",
            "title": "断网重连：指示灯不闪烁",
            "module": "WiFi断网重连补充",
            "priority": "P1",
            "design_method": "协议测试+场景流",
            "precondition": "设备已连接 WiFi，制冰运行中",
            "steps": "1. 关闭路由器(模拟断网)\n2. 观察 WiFi 指示灯 5 分钟\n3. 确认指示灯不闪烁\n4. APP 查看状态",
            "expected_result": "断网后 WiFi 指示灯不闪烁（直接显示离线）；APP 显示设备离线",
            "metrics": "5min 内指示灯无闪烁行为",
            "req_id": "REQ-FW-011b",
            "complexity": "L2",
            "check_point": "规格明确\"重连期间指示灯不闪烁\"",
        },
        {
            "id": "TC-H717D-WiFi-V2-004",
            "title": "断网重连成功→指示灯恢复长亮",
            "module": "WiFi断网重连补充",
            "priority": "P1",
            "design_method": "协议测试+边界值",
            "precondition": "设备已连接 WiFi，路由器关闭≥60s后重新开启",
            "steps": "1. 关闭路由器 60s\n2. 重新开启路由器\n3. 观察 WiFi 指示灯\n4. 计时直到指示灯恢复",
            "expected_result": "路由器恢复后: 设备在 60s 重连周期内自动重连；重连成功后 WiFi 指示灯白光长亮",
            "metrics": "重连成功≤60s",
            "req_id": "REQ-FW-011a",
            "complexity": "L2",
            "check_point": "重连周期 60s 验证",
        },
    ])

    # ── 蓝牙控制补充 (2) ──
    cases.extend([
        {
            "id": "TC-H717D-BLE-V2-004",
            "title": "APP 首页\"仅控制时连接\"策略",
            "module": "蓝牙控制补充",
            "priority": "P1",
            "design_method": "协议测试+场景流",
            "precondition": "手机在蓝牙范围内，APP 处于首页",
            "steps": "1. APP 首页→执行控制指令(开/关机)\n2. 观察蓝牙连接建立→指令执行→断开\n3. 等待 10s 无操作\n4. 确认蓝牙已断开",
            "expected_result": "发送控制指令时蓝牙连接建立→指令执行完毕→蓝牙断开；非控制期间蓝牙不保持连接",
            "metrics": "指令执行后≤5s断开",
            "req_id": "REQ-FW-012d",
            "complexity": "L2",
            "check_point": "区分\"首页控制时连接\"vs\"详情页保持连接\"",
        },
        {
            "id": "TC-H717D-BLE-V2-005",
            "title": "蓝牙断连→立即广播",
            "module": "蓝牙控制补充",
            "priority": "P1",
            "design_method": "协议测试+错误推测",
            "precondition": "手机与设备蓝牙已连接",
            "steps": "1. 手机关闭蓝牙\n2. 用另一台手机扫描蓝牙设备\n3. 确认设备名称出现在扫描列表",
            "expected_result": "手机蓝牙关闭后，设备立即进入蓝牙广播状态；另一手机可扫描到设备",
            "metrics": "断连→广播≤3s",
            "req_id": "REQ-FW-012a",
            "complexity": "L2",
            "check_point": "断连后是否立即可被其他手机发现",
        },
    ])

    # ── 记忆功能补充 (1) ──
    cases.append({
        "id": "TC-H717D-MEM-V2-001",
        "title": "MCU 三项记忆同时验证",
        "module": "记忆功能补充",
        "priority": "P1",
        "design_method": "CRUD+场景流",
        "precondition": "设备已配网，模式 Medium，灯红色/80%",
        "steps": "1. 记录: 模式=Medium, WiFi=SSID-A, 灯=红/80%\n2. 断电 30s→上电\n3. 检查三项恢复情况",
        "expected_result": "断电后三项全部恢复：①模式=Medium ②WiFi自动连接SSID-A ③灯色=红/80%",
        "metrics": "断电→开机显示Medium；WiFi重连≤60s；灯光恢复≤3s",
        "req_id": "REQ-FW-013a,b,c",
        "complexity": "L2",
        "check_point": "三项同时验证，确认无遗漏",
    })

    # ── 制冰轮次补充 (1) ──
    cases.append({
        "id": "TC-H717D-RCD-V2-001",
        "title": "满冰后继续制冰→轮次继续累计",
        "module": "制冰轮次补充",
        "priority": "P1",
        "design_method": "边界值+场景流",
        "precondition": "制冰运行中，满冰触发后取冰继续",
        "steps": "1. 制冰→满冰(第3轮)\n2. 取走冰块(满冰解除)\n3. 设备自动继续制冰(第4轮)\n4. APP 查看累计轮次",
        "expected_result": "满冰状态停止期间不计时；满冰解除后自动恢复制冰；累计轮次=3+后续完成轮次(继续累计)",
        "metrics": "满冰→恢复≤30s",
        "req_id": "REQ-FW-018e",
        "complexity": "L2",
        "check_point": "满冰不重置轮次计数器",
    })

    # ── 时钟刷新 (3) ──
    cases.extend([
        {
            "id": "TC-H717D-CLK-V1-001",
            "title": "蓝牙连接→获取手机时间",
            "module": "时钟刷新",
            "priority": "P1",
            "design_method": "协议测试+场景流",
            "precondition": "设备未连接蓝牙/WiFi",
            "steps": "1. 手机蓝牙连接设备\n2. APP 查看设备日志时间戳\n3. 对比手机时间",
            "expected_result": "设备日志/预约时间与手机时间一致",
            "metrics": "时间同步≤2s",
            "req_id": "REQ-FW-014a",
            "complexity": "L2",
            "check_point": "首次蓝牙连接后时间是否自动同步",
        },
        {
            "id": "TC-H717D-CLK-V1-002",
            "title": "WiFi连接→获取服务器时间",
            "module": "时钟刷新",
            "priority": "P1",
            "design_method": "协议测试+场景流",
            "precondition": "设备仅蓝牙连接，手机时间故意设错1h",
            "steps": "1. 手机设错误时间\n2. WiFi 连接互联网\n3. 查看设备时间是否校正",
            "expected_result": "WiFi 连接成功后设备时间=服务器时间，覆盖蓝牙同步的错误时间",
            "metrics": "WiFi时间同步≤5s",
            "req_id": "REQ-FW-014b",
            "complexity": "L2",
            "check_point": "WiFi服务器时间优先级>蓝牙手机时间",
        },
        {
            "id": "TC-H717D-CLK-V1-003",
            "title": "WiFi 24h 周期时间同步",
            "module": "时钟刷新",
            "priority": "P2",
            "design_method": "边界值+CRUD",
            "precondition": "设备已连接 WiFi 超过 24h",
            "steps": "1. 记录当前设备时间\n2. 等待 24h(或模拟时钟跨越)\n3. 对比服务器时间",
            "expected_result": "每24h自动从服务器同步一次；时间精度与服务器一致",
            "metrics": "24h±1h内触发同步",
            "req_id": "REQ-FW-014c",
            "complexity": "L2",
            "check_point": "长周期测试，可用模拟时钟加速",
        },
    ])

    # ── 分布式网关 (2) ──
    cases.extend([
        {
            "id": "TC-H717D-GW-V1-001",
            "title": "分布式网关：设备作为网关节点注册",
            "module": "分布式网关",
            "priority": "P2",
            "design_method": "协议测试+场景流",
            "precondition": "设备 WiFi 已连接，同一网络有其他 Govee 设备",
            "steps": "1. WiFi连接→APP查看网络拓扑\n2. 确认设备出现在网关节点列表\n3. 其他设备通过本设备中转通信",
            "expected_result": "设备注册为分布式网关节点；APP可见网关拓扑；子设备可通过网关通信",
            "metrics": "网关注册≤30s",
            "req_id": "REQ-FW-015a",
            "complexity": "L2",
            "check_point": "分布式网关功能标志位确认；中继通信延迟",
        },
        {
            "id": "TC-H717D-GW-V1-002",
            "title": "分布式网关：网关断网→子设备切换",
            "module": "分布式网关",
            "priority": "P2",
            "design_method": "错误推测+协议测试",
            "precondition": "设备作为网关，有子设备通过其通信",
            "steps": "1. 关闭本设备 WiFi\n2. 观察子设备通信状态\n3. 确认子设备是否切换网关",
            "expected_result": "本设备断网→子设备自动切换到其他可用网关；APP显示网关切换通知",
            "metrics": "切换≤30s",
            "req_id": "REQ-FW-015a",
            "complexity": "L2",
            "check_point": "网关故障转移机制；子设备不丢消息",
        },
    ])

    # ── NTC故障 (4) ──
    cases.extend([
        {
            "id": "TC-H717D-NTC-V1-001",
            "title": "上电检测 NTC 开路→L/M/S 三灯同时闪烁",
            "module": "NTC故障",
            "priority": "P0",
            "design_method": "场景流+硬件注入",
            "precondition": "通过硬件注入模拟 NTC 开路",
            "steps": "1. NTC 开路注入\n2. 设备上电\n3. 观察指示灯",
            "expected_result": "L、M、S 三种制冰档位灯同时持续闪烁（非交替闪烁，三灯同闪）",
            "metrics": "三灯同时闪烁",
            "req_id": "REQ-FW-016a",
            "complexity": "L2",
            "check_point": "三灯闪烁=故障警告；区分正常模式选择闪烁(单灯闪3s)",
        },
        {
            "id": "TC-H717D-NTC-V1-002",
            "title": "NTC 故障→APP 报故障码 E1",
            "module": "NTC故障",
            "priority": "P0",
            "design_method": "场景流+硬件注入",
            "precondition": "NTC 开路/短路注入，APP已连接",
            "steps": "1. NTC 故障注入\n2. APP 查看设备状态\n3. 确认故障码",
            "expected_result": "APP 显示设备异常；故障代码=E1；故障描述: NTC 异常",
            "metrics": "故障码出现≤5s",
            "req_id": "REQ-FW-016d",
            "complexity": "L2",
            "check_point": "E1 故障码正确；不是其他错误码",
        },
        {
            "id": "TC-H717D-NTC-V1-003",
            "title": "NTC 故障→制冰功能保留",
            "module": "NTC故障",
            "priority": "P0",
            "design_method": "场景流+判定表+硬件注入",
            "precondition": "NTC 开路注入，设备开机",
            "steps": "1. NTC 故障灯效已触发\n2. 按 POWER 启动制冰\n3. 确认制冰是否正常运行\n4. 确认有功率输出",
            "expected_result": "NTC 报异常状态但制冰功能保留；设备仍可正常制冰；同时 L/M/S 故障灯持续闪烁",
            "metrics": "制冰启动≤3s",
            "req_id": "REQ-FW-016e",
            "complexity": "L2",
            "check_point": "有故障但制冰不阻塞(部分用户可能忽略故障灯)",
        },
        {
            "id": "TC-H717D-NTC-V1-004",
            "title": "NTC 故障灯→关机消除→再开机复现",
            "module": "NTC故障",
            "priority": "P1",
            "design_method": "错误推测+场景流",
            "precondition": "NTC 开路，L/M/S 三灯闪烁中",
            "steps": "1. 按 POWER 进入待机(故障灯熄灭)\n2. 再按 POWER 开机\n3. 观察指示灯",
            "expected_result": "关机→故障灯灭；再开机→重新检测NTC→仍异常→L/M/S三灯再次持续闪烁",
            "metrics": "再检测≤1s",
            "req_id": "REQ-FW-016c",
            "complexity": "L2",
            "check_point": "关机消除灯效但故障仍存在→再开机应重新报告",
        },
    ])

    # ── 脱冰除霜 (3) ──
    cases.extend([
        {
            "id": "TC-H717D-DFS-V1-001",
            "title": "脱冰触发→制冰轮次+1",
            "module": "脱冰除霜",
            "priority": "P1",
            "design_method": "场景流+CRUD",
            "precondition": "设备制冰运行中，一轮制冰完成",
            "steps": "1. APP 记录当前制冰轮次\n2. 等待一轮制冰完成(电磁阀脱冰)\n3. APP 刷新查看轮次",
            "expected_result": "电磁阀触发脱冰 → APP 制冰轮次+1；APP 显示\"已制作 X 轮冰块(一轮=9颗)\"",
            "metrics": "轮次更新≤5s",
            "req_id": "REQ-FW-017a",
            "complexity": "L2",
            "check_point": "脱冰=1轮的触发信号确认",
        },
        {
            "id": "TC-H717D-DFS-V1-002",
            "title": "除霜模式→不触发清洁预约",
            "module": "脱冰除霜",
            "priority": "P1",
            "design_method": "判定表+错误推测",
            "precondition": "设备进入除霜模式，APP设置了清洁预约",
            "steps": "1. 触发除霜(模拟)\n2. 清洁预约时间到达\n3. 观察设备是否启动清洁",
            "expected_result": "除霜模式运行中；清洁预约不触发；待除霜完成后才处理下一个模式",
            "metrics": "—",
            "req_id": "REQ-FW-017c",
            "complexity": "L2",
            "check_point": "除霜期间预约互斥规则；除霜后是否自动启动清洁",
        },
        {
            "id": "TC-H717D-DFS-V1-003",
            "title": "脱冰+制冰轮次记录完整性",
            "module": "脱冰除霜",
            "priority": "P2",
            "design_method": "CRUD+边界值",
            "precondition": "设备连续制冰 10 轮",
            "steps": "1. 连续制冰 10 轮\n2. 每轮确认 APP 轮次递增\n3. 第 5 轮中途断电→上电\n4. 确认第 5 轮不计入累计",
            "expected_result": "完整完成的轮次: 全部计入；中途取消/断电的轮次: 不计入；轮次累计正确: 9/10(第5轮不计)",
            "metrics": "—",
            "req_id": "REQ-FW-017a",
            "complexity": "L2",
            "check_point": "取消的轮次不污染累计值",
        },
    ])

    # ── 制冰图表 (4) ──
    cases.extend([
        {
            "id": "TC-H717D-CHT-V1-001",
            "title": "制冰图表:当天 Day 视图",
            "module": "制冰图表",
            "priority": "P1",
            "design_method": "CRUD+边界值",
            "precondition": "当天有制冰记录(≥3次)",
            "steps": "1. APP 打开制冰图表\n2. 切换到\"当天 Day\"视图\n3. 检查每次制冰的时间点",
            "expected_result": "图表显示当天每次制冰的开始时间+累计时长；X轴=时间(h), Y轴=制冰时长(min)；满冰停止时间不计入累计时长",
            "metrics": "数据点与实际制冰次数一致",
            "req_id": "REQ-FW-019a",
            "complexity": "L2",
            "check_point": "满冰停止时间是否被正确排除",
        },
        {
            "id": "TC-H717D-CHT-V1-002",
            "title": "制冰图表:近30天(天颗粒度)",
            "module": "制冰图表",
            "priority": "P1",
            "design_method": "CRUD+边界值",
            "precondition": "设备使用≥30天，有历史数据",
            "steps": "1. APP 图表切换\"近30天\"\n2. 确认颗粒度为\"天\"\n3. 抽查第1天和第30天数据",
            "expected_result": "X轴=日期(30个点)；Y轴=每天累计制冰时长；滑动的30天窗口",
            "metrics": "30天数据点完整无缺失",
            "req_id": "REQ-FW-019c",
            "complexity": "L2",
            "check_point": "颗粒度切换时数据连续性",
        },
        {
            "id": "TC-H717D-CHT-V1-003",
            "title": "制冰图表:近一年(月颗粒度)",
            "module": "制冰图表",
            "priority": "P2",
            "design_method": "CRUD+边界值",
            "precondition": "设备使用≥2个月，有跨月数据",
            "steps": "1. APP 图表切换\"近一年\"\n2. 确认颗粒度为\"月\"\n3. 检查数据聚合",
            "expected_result": "X轴=月份(12个点)；Y轴=每月累计制冰时长；数据按自然月聚合",
            "metrics": "12个月数据点完整",
            "req_id": "REQ-FW-019c",
            "complexity": "L2",
            "check_point": "跨月聚合正确；月初/月末边界",
        },
        {
            "id": "TC-H717D-CHT-V1-004",
            "title": "冰块预估重量 + kg/lb 单位切换",
            "module": "制冰图表",
            "priority": "P1",
            "design_method": "CRUD+等价类",
            "precondition": "当天有制冰记录",
            "steps": "1. APP 查看预估重量(默认kg)\n2. 切换单位为 lb\n3. 验证: 1kg≈2.205lb",
            "expected_result": "默认单位kg，显示制冰预估重量；切换lb后数值正确换算；9颗冰×N轮×单颗重量(约10g)=预估重量",
            "metrics": "kg↔lb换算误差≤5%",
            "req_id": "REQ-FW-019b",
            "complexity": "L2",
            "check_point": "重量=9×轮次×单颗重量",
        },
    ])

    # ── 制冰日志 (3) ──
    cases.extend([
        {
            "id": "TC-H717D-LOG-V1-001",
            "title": "制冰日志:事件类型+时间戳",
            "module": "制冰日志",
            "priority": "P1",
            "design_method": "CRUD+场景流",
            "precondition": "设备已运行，执行各种操作",
            "steps": "1. 分别触发: 制冰开始/清洁/缺水/除霜\n2. APP 查看制冰日志",
            "expected_result": "日志显示每条事件的日期+时间+事件名称；格式: \"2026-07-23 14:30:15 开始制作冰块\"",
            "metrics": "事件时间戳精度=秒",
            "req_id": "REQ-FW-020a",
            "complexity": "L2",
            "check_point": "记录事件不记录时长",
        },
        {
            "id": "TC-H717D-LOG-V1-002",
            "title": "离线日志:最多存10条(FIFO)",
            "module": "制冰日志",
            "priority": "P1",
            "design_method": "边界值+CRUD",
            "precondition": "设备离线(WiFi+蓝牙均断开)，触发12个事件",
            "steps": "1. 断开所有网络\n2. 触发 12 个不同事件\n3. 恢复联网→APP 同步日志\n4. 查看日志条数",
            "expected_result": "离线期间只保留最近10条日志；最早触发的2条被FIFO淘汰；联网后10条日志同步到APP",
            "metrics": "离线存储上限=10条",
            "req_id": "REQ-FW-020c",
            "complexity": "L2",
            "check_point": "FIFO淘汰机制；联网后补推完整性",
        },
        {
            "id": "TC-H717D-LOG-V1-003",
            "title": "联网后日志同步补推",
            "module": "制冰日志",
            "priority": "P1",
            "design_method": "协议测试+CRUD",
            "precondition": "设备离线期间有5条日志",
            "steps": "1. 离线触发5个事件\n2. 恢复 WiFi 连接\n3. APP 查看日志",
            "expected_result": "恢复联网后5条离线日志自动同步到APP；时间戳为实际发生时间(非同步时间)；APP日志列表完整显示",
            "metrics": "同步≤30s",
            "req_id": "REQ-FW-020c",
            "complexity": "L2",
            "check_point": "同步后日志时间戳正确",
        },
    ])

    # ── E2E集成用例 (2) ──
    cases.extend([
        {
            "id": "TC-H717D-E2E-V1-003",
            "title": "E2E: 制冰→脱冰→日志→图表全链路",
            "module": "E2E集成用例",
            "priority": "P1",
            "design_method": "场景流",
            "precondition": "设备正常，APP已连接",
            "steps": "1. 启动制冰→记录开始时间\n2. 等待3轮脱冰→APP确认轮次=3\n3. 制冰日志确认3条\"开始制冰\"\n4. 图表确认当天有制冰数据\n5. 确认预估重量=3轮×9颗×10g≈270g",
            "expected_result": "全链路: 制冰→脱冰→轮次→日志→图表→重量；数据一致性: 轮次=日志条数=图表数据点数；重量=轮次×9×10g(±10%)",
            "metrics": "轮次=日志条数=图表点",
            "req_id": "REQ-FW-017~020",
            "complexity": "L2",
            "check_point": "跨模块数据一致性",
        },
        {
            "id": "TC-H717D-E2E-V1-004",
            "title": "E2E: 蓝牙配网→WiFi→时钟同步→预约制冰",
            "module": "E2E集成用例",
            "priority": "P1",
            "design_method": "场景流",
            "precondition": "设备首次上电未配网",
            "steps": "1. 蓝牙配网→WiFi连接\n2. 确认时钟同步(服务器时间)\n3. APP设置预约明天8:00\n4. 确认预约指示灯亮\n5. 等到8:00→确认自动启动",
            "expected_result": "配网→时钟同步→预约→到点自动启动；全部按预期执行",
            "metrics": "蓝牙配网≤30s,WiFi≤60s,预约±1min",
            "req_id": "REQ-FW-009~014",
            "complexity": "L2",
            "check_point": "通信栈+时钟+预约跨模块联动",
        },
    ])

    return cases


# ═══════════════════════════════════════════════════════════
# Part 3: All directories (22 sub-directories under H717D root)
# ═══════════════════════════════════════════════════════════

# Directory name → sort_order
ALL_DIRECTORIES = OrderedDict([
    # Existing modules (9)
    ("按键功能用例设计", 1),
    ("指示灯功能用例设计", 2),
    ("出厂状态用例设计", 3),
    ("联网与配网用例设计", 4),
    ("蓝牙控制记忆时钟用例设计", 5),
    ("制冰轮次记录用例设计", 6),
    ("冰篮灯用例设计", 7),
    ("缺水满冰保护用例设计", 8),
    ("预约定时用例设计", 9),
    # Supplement modules (6)
    ("蓝牙连接补充", 10),
    ("WiFi配网补充", 11),
    ("WiFi断网重连补充", 12),
    ("蓝牙控制补充", 13),
    ("记忆功能补充", 14),
    ("制冰轮次补充", 15),
    # New modules (7)
    ("时钟刷新", 16),
    ("分布式网关", 17),
    ("NTC故障", 18),
    ("脱冰除霜", 19),
    ("制冰图表", 20),
    ("制冰日志", 21),
    ("E2E集成用例", 22),
])

ROOT_DIR_NAME = "H717D"
CASE_TYPE = "storage"


# ═══════════════════════════════════════════════════════════
# Part 4: Django Management Command
# ═══════════════════════════════════════════════════════════

class Command(BaseCommand):
    help = __doc__

    def add_arguments(self, parser):
        parser.add_argument(
            "--dry-run", action="store_true",
            help="Preview without writing to the database.",
        )
        parser.add_argument(
            "--overwrite", action="store_true",
            help="Overwrite existing cases (default: skip if exists).",
        )
        parser.add_argument(
            "--skip-existing", action="store_true",
            help="Skip parsing the HTML document library (only import new 32 cases).",
        )

    def handle(self, **options):
        dry_run = options["dry_run"]
        overwrite = options["overwrite"]
        skip_existing = options["skip_existing"]

        self.stdout.write(self.style.NOTICE("=" * 60))
        self.stdout.write(self.style.NOTICE("H717D Test Case Import"))
        self.stdout.write(self.style.NOTICE("=" * 60))

        if dry_run:
            self.stdout.write(self.style.WARNING("[DRY RUN] No changes will be written."))

        # ── Collect all test cases ──
        all_cases = []

        if not skip_existing:
            self.stdout.write("\n[1/4] Parsing existing 239 cases from HTML document library...")
            html_path = str(DOC_LIB_HTML)
            if not os.path.exists(html_path):
                self.stdout.write(self.style.WARNING(
                    f"  HTML document library not found at: {html_path}\n"
                    f"  Set H717D_DOC_HTML env var or use --skip-existing to skip."
                ))
                existing = []
            else:
                existing = _parse_existing_cases(html_path)
                self.stdout.write(f"  Found {len(existing)} existing test cases in 9 modules.")
                all_cases.extend(existing)
        else:
            self.stdout.write("\n[1/4] Skipping existing cases (--skip-existing).")

        # ── Add new 32 cases ──
        self.stdout.write("\n[2/4] Loading new 32 test cases...")
        new_cases = _get_new_cases_data()
        self.stdout.write(f"  Loaded {len(new_cases)} new test cases in 13 modules.")
        all_cases.extend(new_cases)

        self.stdout.write(f"\n  Total cases to import: {len(all_cases)}")

        # ── Validate ──
        for c in all_cases:
            if c["module"] not in ALL_DIRECTORIES:
                self.stdout.write(self.style.ERROR(
                    f"  ERROR: Unknown module '{c['module']}' for case {c['id']}"
                ))
                return

        # ── Statistics ──
        p0 = sum(1 for c in all_cases if c.get("priority") == "P0")
        p1 = sum(1 for c in all_cases if c.get("priority") == "P1")
        p2 = sum(1 for c in all_cases if c.get("priority") == "P2")
        self.stdout.write(f"  P0: {p0} | P1: {p1} | P2: {p2}")

        # ── Create directories and import cases ──
        self.stdout.write("\n[3/4] Creating directory structure...")
        dirs_created = 0
        dirs_existing = 0

        if dry_run:
            self.stdout.write(f"  [DRY RUN] Would create root: {ROOT_DIR_NAME}")
            for dir_name, sort_order in ALL_DIRECTORIES.items():
                dirs_created += 1
                self.stdout.write(f"  [DRY RUN] Would create: {dir_name}")
            self.stdout.write(self.style.WARNING(
                f"\n[DRY RUN] Would import {len(all_cases)} test cases "
                f"(P0:{p0} P1:{p1} P2:{p2})."
            ))
            self.stdout.write(self.style.WARNING("[DRY RUN] No changes written."))
            return

        with transaction.atomic():
            # Root directory
            root_dir, created = CaseDirectory.objects.get_or_create(
                name=ROOT_DIR_NAME,
                parent=None,
                case_type=CASE_TYPE,
                defaults={"sort_order": 0},
            )
            if created:
                dirs_created += 1
                self.stdout.write(f"  + Created root: {ROOT_DIR_NAME}")
            else:
                dirs_existing += 1
                self.stdout.write(f"  = Exists root: {ROOT_DIR_NAME}")

            # Sub-directories
            dir_map = {}  # name → CaseDirectory instance
            dir_map[ROOT_DIR_NAME] = root_dir

            for dir_name, sort_order in ALL_DIRECTORIES.items():
                sub_dir, created = CaseDirectory.objects.get_or_create(
                    name=dir_name,
                    parent=root_dir,
                    case_type=CASE_TYPE,
                    defaults={"sort_order": sort_order},
                )
                dir_map[dir_name] = sub_dir
                if created:
                    dirs_created += 1
                    self.stdout.write(f"  + Created: {dir_name}")
                else:
                    dirs_existing += 1
                    self.stdout.write(f"  = Exists: {dir_name}")

            # ── Group cases by module ──
            self.stdout.write(f"\n[4/4] Building {len(all_cases)} cases into {len(ALL_DIRECTORIES)} module tables...")
            module_cases = {}  # module_name → list of case dicts
            for case in all_cases:
                module_name = case["module"]
                if module_name not in module_cases:
                    module_cases[module_name] = []
                module_cases[module_name].append(case)

            # ── Define extra columns shared across all modules ──
            extra_columns = [
                {"key": "case_no", "label": "用例编号", "width": 240, "editable": False},
                {"key": "design_method", "label": "设计方法", "width": 180, "editable": True},
                {"key": "metrics", "label": "量化指标", "width": 200, "editable": True},
                {"key": "req_id", "label": "追溯需求ID", "width": 160, "editable": True},
                {"key": "complexity", "label": "复杂度", "width": 80, "editable": True},
                {"key": "check_point", "label": "校验要点", "width": 250, "editable": True},
                {"key": "status", "label": "执行状态", "width": 100, "editable": True},
            ]

            imported = 0
            skipped = 0
            failed = 0

            for module_name, cases in module_cases.items():
                directory = dir_map.get(module_name)
                if directory is None:
                    self.stdout.write(self.style.ERROR(
                        f"  FAIL: module '{module_name}' — directory not found"
                    ))
                    failed += 1
                    continue

                # Table ID: H717D-{module}
                table_id = f"H717D-{module_name}"

                # Check existence
                if not overwrite and StorageTestCase.objects.filter(id=table_id).exists():
                    skipped += 1
                    continue

                # Build rows: one row per test case
                rows = []
                for i, case in enumerate(cases):
                    row = {
                        "id": i + 1,
                        "title": case["title"],
                        "priority": case.get("priority", "P1"),
                        "precondition": case.get("precondition", ""),
                        "steps": case.get("steps", ""),
                        "expected_result": case.get("expected_result", ""),
                        # Extra columns
                        "case_no": case["id"],
                        "design_method": case.get("design_method", ""),
                        "metrics": case.get("metrics", ""),
                        "req_id": case.get("req_id", ""),
                        "complexity": case.get("complexity", ""),
                        "check_point": case.get("check_point", ""),
                        "status": "NOT_RUN",
                    }
                    rows.append(row)

                defaults = {
                    "title": module_name,
                    "case_type": CASE_TYPE,
                    "priority": "P1",
                    "precondition": "",
                    "steps": "",
                    "expected_result": "",
                    "design_method": "",
                    "metrics": "",
                    "custom_columns": extra_columns,
                    "rows": rows,
                    "directory": directory,
                    "enabled": True,
                    "visibility": "public",
                    "permission": "edit",
                    "created_by": "import_h717d",
                    "updated_by": "import_h717d",
                }

                try:
                    obj, created = StorageTestCase.objects.update_or_create(
                        id=table_id,
                        defaults=defaults,
                    )
                    imported += 1
                    self.stdout.write(f"  + {module_name}: {len(rows)} rows")
                except Exception as e:
                    self.stdout.write(self.style.ERROR(
                        f"  FAIL: {module_name} — {e}"
                    ))
                    failed += 1

        # ── Summary ──
        self.stdout.write("\n" + self.style.SUCCESS("=" * 60))
        self.stdout.write(self.style.SUCCESS("Import Complete"))
        self.stdout.write(self.style.SUCCESS("=" * 60))
        self.stdout.write(f"  Directories: {dirs_created} created, {dirs_existing} existing")
        self.stdout.write(f"  Module tables: {imported} imported, {skipped} skipped, {failed} failed")
        self.stdout.write(f"  Total rows: {len(all_cases)} (P0:{p0} P1:{p1} P2:{p2})")
        self.stdout.write(f"\n  Frontend: 用例管理 → 业务功能用例 → H717D (22 个模块表格，{len(all_cases)} 行)")
