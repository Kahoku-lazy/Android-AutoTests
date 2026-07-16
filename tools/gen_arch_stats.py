#!/usr/bin/env python3
"""
Architecture stats generator — 扫描代码库，输出当前架构的可度量事实。

用途:
  - architect agent 被调用时自动运行，对比 项目架构.md 的 auto 区域
  - 发现 drift 后自动更新文档的事实部分
  - 也支持 --json 输出，供 CI/hook 消费

用法:
  python tools/gen_arch_stats.py              # 输出 Markdown 片段
  python tools/gen_arch_stats.py --json        # 输出 JSON
  python tools/gen_arch_stats.py --check-md    # 对比 项目架构.md，输出 drift 报告
"""

import json
import os
import re
import sys
from collections import defaultdict
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent


# ── 1. Django App 扫描 ──

def scan_django_apps():
    """扫描 apps/ 下所有 Django App，返回结构化数据。"""
    apps_dir = PROJECT_ROOT / "apps"
    apps = []
    for d in sorted(apps_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
            continue
        if not (d / "__init__.py").exists() and not (d / "models.py").exists():
            continue

        app = {"name": d.name, "has_models": (d / "models.py").exists(),
               "has_views": (d / "views.py").exists() or (d / "views").is_dir(),
               "has_api": (d / "api.py").exists(),
               "has_urls": (d / "urls.py").exists()}

        # 统计表数量
        app["table_count"] = 0
        app["tables"] = []
        if app["has_models"]:
            models_path = d / "models.py"
            content = models_path.read_text(encoding="utf-8")
            app["table_count"] = len(re.findall(r"db_table\s*=\s*['\"](\w+)['\"]", content))
            app["tables"] = re.findall(r"db_table\s*=\s*['\"](\w+)['\"]", content)

        # 统计端点数量
        app["endpoint_count"] = 0
        if app["has_urls"]:
            urls_path = d / "urls.py"
            urls_content = urls_path.read_text(encoding="utf-8")
            app["endpoint_count"] = len(re.findall(r"^\s*path\([\"']", urls_content, re.MULTILINE))

        # 统计代码行数
        app["total_lines"] = 0
        for py_file in d.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue
            try:
                app["total_lines"] += len(py_file.read_text(encoding="utf-8").splitlines())
            except Exception:
                pass

        apps.append(app)
    return apps


# ── 2. AgentScope Tool 扫描 ──

def scan_tools():
    """扫描 agentscope_service/tools/ 下所有 Tool。"""
    tools_dir = PROJECT_ROOT / "agentscope_service" / "tools"
    tools = []
    for py_file in sorted(tools_dir.glob("*.py")):
        if py_file.name.startswith("_"):
            continue
        content = py_file.read_text(encoding="utf-8")
        tool_classes = re.findall(r"class\s+(\w+)\s*\(\s*ToolBase\s*\)", content)
        for cls_name in tool_classes:
            # 提取 description
            desc_match = re.search(
                rf"class\s+{cls_name}\s*\(.*?\).*?\n\s+name\s*=\s*['\"]([^'\"]+)['\"]",
                content, re.DOTALL
            )
            tool_name = desc_match.group(1) if desc_match else cls_name
            # 提取 is_read_only
            readonly = "is_read_only = True" in content.split(f"class {cls_name}")[1].split("class")[0] if f"class {cls_name}" in content else False
            tools.append({
                "name": tool_name,
                "class": cls_name,
                "file": py_file.name,
                "is_read_only": readonly,
            })
    return tools


# ── 3. 前端模块扫描 ──

def scan_frontend_modules():
    """扫描 frontend/src/modules/ 下所有模块。"""
    mods_dir = PROJECT_ROOT / "frontend" / "src" / "modules"
    if not mods_dir.exists():
        return []
    modules = []
    for d in sorted(mods_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("."):
            continue
        mod = {"name": d.name}
        mod["has_index"] = (d / "index.vue").exists()
        mod["has_api"] = (d / "api.js").exists()
        mod["has_routes"] = (d / "routes.js").exists()
        mod["has_store"] = (d / "store.js").exists() or (d / "store.ts").exists()
        mod["has_composables"] = (d / "composables").is_dir()
        mod["has_components"] = (d / "components").is_dir()
        # 统计 Vue 文件总行数
        mod["vue_lines"] = 0
        for vue_file in d.rglob("*.vue"):
            try:
                mod["vue_lines"] += len(vue_file.read_text(encoding="utf-8").splitlines())
            except Exception:
                pass
        modules.append(mod)
    return modules


# ── 4. 文件体积违规扫描 ──

def scan_file_size_violations(py_limit=400, vue_limit=500):
    """扫描超标文件。"""
    violations = []

    # Python 文件
    apps_dir = PROJECT_ROOT / "apps"
    for py_file in apps_dir.rglob("*.py"):
        if "migrations" in str(py_file) or "__pycache__" in str(py_file):
            continue
        lines = len(py_file.read_text(encoding="utf-8").splitlines())
        if lines > py_limit:
            violations.append({
                "file": str(py_file.relative_to(PROJECT_ROOT)),
                "lines": lines,
                "limit": py_limit,
                "excess": lines - py_limit,
                "type": "python",
            })

    # AgentScope tools
    tools_dir = PROJECT_ROOT / "agentscope_service"
    for py_file in tools_dir.rglob("*.py"):
        if "__pycache__" in str(py_file):
            continue
        lines = len(py_file.read_text(encoding="utf-8").splitlines())
        if lines > py_limit:
            violations.append({
                "file": str(py_file.relative_to(PROJECT_ROOT)),
                "lines": lines,
                "limit": py_limit,
                "excess": lines - py_limit,
                "type": "python",
            })

    # Vue 文件
    frontend_dir = PROJECT_ROOT / "frontend" / "src"
    for vue_file in frontend_dir.rglob("*.vue"):
        lines = len(vue_file.read_text(encoding="utf-8").splitlines())
        if lines > vue_limit:
            violations.append({
                "file": str(vue_file.relative_to(PROJECT_ROOT)),
                "lines": lines,
                "limit": vue_limit,
                "excess": lines - vue_limit,
                "type": "vue",
            })

    violations.sort(key=lambda v: -v["excess"])
    return violations


# ── 5. 跨模块依赖扫描 ──

def scan_cross_app_imports():
    """扫描跨 App import 关系。"""
    apps_dir = PROJECT_ROOT / "apps"
    agentscope_dir = PROJECT_ROOT / "agentscope_service"
    gateway_dir = PROJECT_ROOT / "gateway"

    # 从 INSTALLED_APPS 获取 App 列表
    settings_path = PROJECT_ROOT / "config" / "settings.py"
    settings_content = settings_path.read_text(encoding="utf-8")
    app_names = re.findall(r"'apps\.(\w+)'", settings_content)

    # 按目标 App 分组
    targets = defaultdict(set)  # {target_app: {source_file1, source_file2, ...}}

    for scan_dir in [apps_dir, agentscope_dir, gateway_dir]:
        for py_file in scan_dir.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue
            content = py_file.read_text(encoding="utf-8")
            for app_name in app_names:
                pattern = rf"from apps\.{app_name}\."
                if re.search(pattern, content):
                    # 排除同 App 内的 import
                    rel_path = str(py_file.relative_to(PROJECT_ROOT))
                    if f"apps/{app_name}/" not in rel_path:
                        targets[app_name].add(rel_path)

    return {app: sorted(sources) for app, sources in sorted(targets.items())}


# ── 5b. 跨模块 ORM 写违规扫描（防火墙 #2）──

# 已知违规白名单加载
def _load_boundary_whitelist():
    """Load known-violation whitelist from .claude/boundary-whitelist.json."""
    whitelist_path = PROJECT_ROOT / ".claude" / "boundary-whitelist.json"
    if not whitelist_path.exists():
        return []
    try:
        data = json.loads(whitelist_path.read_text(encoding="utf-8"))
        return data.get("whitelist", [])
    except Exception:
        return []


def scan_orm_write_violations():
    """Detect cross-module direct ORM write violations.

    Firewall #2 rule: cross-app writes MUST go through api.py.
    This scans for files that import a Model from another app
    and then call .objects.create / .objects.update / .objects.filter(...).update
    / .objects.filter(...).delete on it, bypassing api.py.

    Returns (new_violations, known_violations) — new violations not yet whitelisted
    should fail CI.
    """
    apps_dir = PROJECT_ROOT / "apps"
    agentscope_dir = PROJECT_ROOT / "agentscope_service"
    whitelist = _load_boundary_whitelist()

    # Build a mapping: model_class_name → app_name
    model_to_app = {}  # {"Device": "device_pool", ...}
    for d in sorted(apps_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
            continue
        models_path = d / "models.py"
        if not models_path.exists():
            continue
        content = models_path.read_text(encoding="utf-8")
        for m in re.findall(r"class\s+(\w+)\s*\(\s*models\.Model\s*\)", content):
            model_to_app[m] = d.name

    # Write patterns to detect
    # Pattern 1: ModelName.objects.create(   — direct INSERT
    # Pattern 2: ModelName.objects.update(   — direct bulk UPDATE
    # Pattern 3: ModelName.objects.filter(...).update( — queryset UPDATE
    # Pattern 4: ModelName.objects.filter(...).delete( — queryset DELETE
    WRITE_PATTERNS = [
        (r'\b({model})\s*\.\s*objects\s*\.\s*create\s*\(', 'objects.create()'),
        (r'\b({model})\s*\.\s*objects\s*\.\s*update\s*\(', 'objects.update()'),
        (r'\b({model})\s*\.\s*objects\s*\.\s*filter\s*\([^)]*\)\s*\.\s*update\s*\(', 'filter().update()'),
        (r'\b({model})\s*\.\s*objects\s*\.\s*filter\s*\([^)]*\)\s*\.\s*delete\s*\(', 'filter().delete()'),
    ]

    # Scan all source files
    scan_dirs = [apps_dir, agentscope_dir]
    violations = []

    for scan_dir in scan_dirs:
        for py_file in scan_dir.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue
            if py_file.name == "__init__.py" and py_file.stat().st_size < 100:
                continue

            rel_path = str(py_file.relative_to(PROJECT_ROOT))
            try:
                content = py_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # Find which models this file imports from OTHER apps
            imported_models = {}  # {ModelName: source_app}
            for m in re.finditer(
                r'from\s+apps\.(\w+)\s*\.\s*models\s+import\s+([^#\n]+)',
                content,
            ):
                source_app = m.group(1)
                imported_str = m.group(2)
                # Extract individual model names from the import
                names = re.findall(r'\b(\w+)\b', imported_str.split('#')[0])
                for name in names:
                    if name in model_to_app and model_to_app[name] == source_app:
                        imported_models[name] = source_app

            if not imported_models:
                continue

            # Determine the "owning" app of this file
            file_app = None
            if f"apps/" in rel_path:
                file_app = rel_path.split("apps/")[1].split("/")[0]

            # For each imported model, check for write patterns
            for model_name, source_app in imported_models.items():
                # Skip if this file IS the source app's api.py (allowed)
                if file_app == source_app and py_file.name == "api.py":
                    continue

                for pattern, pattern_label in WRITE_PATTERNS:
                    compiled = re.compile(pattern.format(model=model_name))
                    matches = list(compiled.finditer(content))
                    for match in matches:
                        line_no = content[:match.start()].count("\n") + 1
                        violations.append({
                            "file": rel_path,
                            "line": line_no,
                            "model": model_name,
                            "source_app": source_app,
                            "pattern": pattern_label,
                            "snippet": content.split("\n")[line_no - 1].strip()[:120],
                        })

    # Match against whitelist
    def _whitelist_key(v):
        return f"{v['file']}:{v['line']}:{v['model']}:{v['pattern']}"

    known = []
    new = []
    whitelist_keys = set()
    for w in whitelist:
        whitelist_keys.add(f"{w.get('file', '')}:{w.get('line', 0)}:{w.get('model', '')}:{w.get('pattern', '')}")

    for v in violations:
        if _whitelist_key(v) in whitelist_keys:
            known.append(v)
        else:
            new.append(v)

    return new, known


def scan_cross_app_internal_imports():
    """Detect cross-app imports of internal implementation (firewall #1).

    Firewall #1 rule: service.py 互不 import.
    Extends to: no importing from other apps' non-api internals
    (e.g. runner.py internals, views.py private symbols like _active_runs).
    """
    apps_dir = PROJECT_ROOT / "apps"
    agentscope_dir = PROJECT_ROOT / "agentscope_service"

    # Apps that have these internal modules
    INTERNAL_MODULES = ["service", "runner", "consumer", "callbacks", "state_machine"]

    whitelist = _load_boundary_whitelist()
    violations = []

    for scan_dir in [apps_dir, agentscope_dir]:
        for py_file in scan_dir.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue

            rel_path = str(py_file.relative_to(PROJECT_ROOT))
            try:
                content = py_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # Detect: from apps.X.{internal} import ...
            for mod in INTERNAL_MODULES:
                for m in re.finditer(
                    rf'from\s+apps\.(\w+)\.{mod}\s+import\s+([^#\n]+)',
                    content,
                ):
                    source_app = m.group(1)
                    imported_names = m.group(2).strip()
                    # Skip if same app
                    if f"apps/{source_app}/" in rel_path:
                        continue
                    line_no = content[:m.start()].count("\n") + 1
                    violations.append({
                        "file": rel_path,
                        "line": line_no,
                        "source_app": source_app,
                        "module": mod,
                        "imports": imported_names[:100],
                        "snippet": content.split("\n")[line_no - 1].strip()[:120],
                    })

    # Match against whitelist
    def _key(v):
        return f"{v['file']}:{v['line']}:internal:{v['source_app']}.{v['module']}"

    known = []
    new = []
    whitelist_keys = set()
    for w in whitelist:
        whitelist_keys.add(
            f"{w.get('file', '')}:{w.get('line', 0)}:internal:{w.get('source_app', '')}.{w.get('module', '')}"
        )

    for v in violations:
        if _key(v) in whitelist_keys:
            known.append(v)
        else:
            new.append(v)

    return new, known


# ── 6. 步骤类型与设备状态 ──

def scan_step_types():
    """从 models/step_types.py 的 StepType 枚举中提取步骤类型。"""
    step_types_path = PROJECT_ROOT / "models" / "step_types.py"
    if not step_types_path.exists():
        return {"count": 0, "types": [], "labels": {}}

    content = step_types_path.read_text(encoding="utf-8")
    types = []
    for m in re.finditer(r'(\w+)\s*=\s*"(\w+)"', content):
        name, value = m.group(1), m.group(2)
        if name.isupper() and not name.startswith('_'):
            types.append({"name": name, "value": value})

    labels = {}
    for m in re.finditer(r'StepType\.(\w+):\s*"([^"]+)"', content):
        labels[m.group(1)] = m.group(2)

    return {"count": len(types), "types": types, "labels": labels}


def scan_device_statuses():
    """从 device_pool/models.py 提取设备状态定义。"""
    models_path = PROJECT_ROOT / "apps" / "device_pool" / "models.py"
    if not models_path.exists():
        return {"count": 0, "statuses": []}

    content = models_path.read_text(encoding="utf-8")
    # Pattern 1: comment-based # ONLINE | BUSY | OFFLINE
    for m in re.finditer(r'#\s*((?:ONLINE|BUSY|OFFLINE|DISCONNECTED)(?:\s*\|\s*(?:ONLINE|BUSY|OFFLINE|DISCONNECTED))*)', content):
        statuses = [s.strip() for s in m.group(1).split("|")]
        return {"count": len(statuses), "statuses": sorted(statuses)}
    return {"count": 0, "statuses": []}


# ── 7. 汇总 → Markdown ──

def generate_markdown():
    """生成可插入 项目架构.md 的 Markdown 片段。"""
    apps = scan_django_apps()
    tools = scan_tools()
    modules = scan_frontend_modules()
    violations = scan_file_size_violations()
    cross_imports = scan_cross_app_imports()

    total_tables = sum(a["table_count"] for a in apps)
    total_endpoints = sum(a["endpoint_count"] for a in apps)
    total_violations = len(violations)
    top_violations = violations[:10]

    lines = []
    lines.append(f"<!-- ARCH_STATS — 由 tools/gen_arch_stats.py 自动生成，请勿手动编辑 -->")
    lines.append(f"<!-- 最后更新: 见 git log -- -->")
    lines.append("")

    # App 总览
    lines.append("### Django App 清单")
    lines.append("")
    lines.append(f"| App | 表 | 端点 | 代码行数 | models | views | api | urls |")
    lines.append(f"|-----|:--:|:--:|:--:|:--:|:--:|:--:|:--:|")
    for a in apps:
        lines.append(
            f"| `{a['name']}` | {a['table_count']} | {a['endpoint_count']} | {a['total_lines']} | "
            f"{'✅' if a['has_models'] else '❌'} | "
            f"{'✅' if a['has_views'] else '❌'} | "
            f"{'✅' if a['has_api'] else '❌'} | "
            f"{'✅' if a['has_urls'] else '❌'} |"
        )
    lines.append(f"| **合计** | **{total_tables}** | **{total_endpoints}** | — | — | — | — | — |")
    lines.append("")

    # 数据库表
    lines.append("### 数据库表清单")
    lines.append("")
    lines.append(f"| 前缀 | App | 表名 |")
    lines.append(f"|------|-----|------|")
    for a in apps:
        prefix_map = {
            "device_pool": "dp_", "element_locator": "el_", "case_manager": "cm_",
            "test_runner": "tr_", "report_generator": "rg_", "ai_assistant": "ai_",
            "workflow": "wf_", "dashboard": "—",
        }
        prefix = prefix_map.get(a["name"], "??")
        for t in a["tables"]:
            lines.append(f"| `{prefix}` | `{a['name']}` | `{t}` |")
    lines.append("")

    # AgentScope Tool
    lines.append("### AgentScope Tool 清单")
    lines.append("")
    lines.append(f"| Tool 名称 | 类名 | 文件 | 只读 |")
    lines.append(f"|-----------|------|------|:--:|")
    for t in tools:
        lines.append(f"| `{t['name']}` | `{t['class']}` | `{t['file']}` | {'✅' if t['is_read_only'] else '❌'} |")
    lines.append(f"| **合计 {len(tools)} 个** | | | |")
    lines.append("")

    # 前端模块
    lines.append("### 前端模块清单")
    lines.append("")
    lines.append(f"| 模块 | index.vue | api.js | routes.js | Vue 行数 |")
    lines.append(f"|------|:--:|:--:|:--:|:--:|")
    for m in modules:
        lines.append(
            f"| `{m['name']}` | {'✅' if m['has_index'] else '❌'} | "
            f"{'✅' if m['has_api'] else '❌'} | "
            f"{'✅' if m['has_routes'] else '❌'} | "
            f"{m['vue_lines']} |"
        )
    lines.append("")

    # 跨模块依赖
    lines.append("### 跨模块 import 关系")
    lines.append("")
    lines.append("（被依赖的 App → 依赖来源文件）")
    lines.append("")
    for app_name, sources in cross_imports.items():
        lines.append(f"**`{app_name}`** ← {len(sources)} 个外部文件")
        for s in sources[:5]:
            lines.append(f"  - `{s}`")
        if len(sources) > 5:
            lines.append(f"  - ... 还有 {len(sources) - 5} 个")
        lines.append("")

    # 文件体积违规
    lines.append("### 文件体积违规 TOP 10")
    lines.append("")
    if top_violations:
        lines.append(f"| 文件 | 行数 | 上限 | 超出 | 类型 |")
        lines.append(f"|------|:--:|:--:|:--:|------|")
        for v in top_violations:
            lines.append(f"| `{v['file']}` | {v['lines']} | {v['limit']} | +{v['excess']} | {v['type']} |")
    else:
        lines.append("✅ 无超标文件")
    lines.append("")

    lines.append(f"<!-- ARCH_STATS_END -->")

    # ── 步骤类型 ──
    steps = scan_step_types()
    lines.append("")
    lines.append("### 步骤类型定义（来自 StepType 枚举）")
    lines.append("")
    lines.append(f"**{steps['count']} 种步骤类型**：")
    lines.append("")
    cat_order = [
        ("点击类", ["CLICK", "LONG_CLICK", "CLICK_INDEXED", "RETRY_CLICK"]),
        ("手势类", ["SWIPE", "DRAG"]),
        ("等待类", ["WAIT", "WAIT_DISAPPEAR", "WAIT_ANY", "WAIT_TOAST"]),
        ("验证类", ["VERIFY_TEXT", "POLL_TEXT"]),
        ("控制类", ["START_APP", "KILL_APP", "RESTART_APP"]),
        ("工具类", ["SLEEP", "LOG"]),
    ]
    for cat_name, cat_keys in cat_order:
        items = []
        for key in cat_keys:
            label = steps["labels"].get(key, "")
            items.append(f"`{key}` ({label})" if label else f"`{key}`")
        if items:
            lines.append(f"| {cat_name} | {' · '.join(items)} |")
    lines.append("")

    # ── 设备状态 ──
    dev_status = scan_device_statuses()
    lines.append("### 设备状态定义")
    lines.append("")
    lines.append(f"**{dev_status['count']} 种状态**: " + " · ".join(f"`{s}`" for s in dev_status['statuses']))
    lines.append("")

    return "\n".join(lines)


def generate_json():
    """输出 JSON 格式（供 CI/hook 消费）。"""
    new_violations, known_violations = scan_orm_write_violations()
    return json.dumps({
        "django_apps": scan_django_apps(),
        "tools": scan_tools(),
        "frontend_modules": scan_frontend_modules(),
        "file_size_violations": scan_file_size_violations(),
        "cross_app_imports": scan_cross_app_imports(),
        "orm_write_violations": {
            "new": new_violations,
            "known": known_violations,
        },
        "summary": {
            "app_count": len(scan_django_apps()),
            "table_count": sum(a["table_count"] for a in scan_django_apps()),
            "endpoint_count": sum(a["endpoint_count"] for a in scan_django_apps()),
            "tool_count": len(scan_tools()),
            "frontend_module_count": len(scan_frontend_modules()),
            "file_size_violation_count": len(scan_file_size_violations()),
            "orm_write_violation_new": len(new_violations),
            "orm_write_violation_known": len(known_violations),
        }
    }, indent=2, ensure_ascii=False)


def check_drift():
    """对比 项目架构.md 中的 auto 区域，检测 drift。"""
    doc_path = PROJECT_ROOT / "dev_docs" / "03-设计与架构" / "项目架构.md"
    if not doc_path.exists():
        return {"status": "no_doc", "message": "项目架构.md 不存在"}

    doc_content = doc_path.read_text(encoding="utf-8")
    current = generate_markdown()

    # 提取文档中的 auto 区域
    match = re.search(r"<!-- ARCH_STATS.*?-->.*?<!-- ARCH_STATS_END -->", doc_content, re.DOTALL)
    if not match:
        return {"status": "no_auto_section", "message": "项目架构.md 中无 ARCH_STATS 区域，需要初始化"}

    existing = match.group(0)

    # 简单对比: 提取关键数字
    def extract_numbers(text):
        nums = {}
        # App 数量
        m = re.search(r"\|\s*\*+\s*合计\s*\*+\s*\|\s*\*+(\d+)\*+\s*\|\s*\*+(\d+)\*+", text)
        if m:
            nums["tables"] = int(m.group(1))
            nums["endpoints"] = int(m.group(2))
        # Tool 数量
        m = re.search(r"\*\*合计\s*(\d+)\s*个\*\*", text)
        if m:
            nums["tools"] = int(m.group(1))
        # 违规数量 (从 TOP 10 表行数判断)
        nums["violations"] = len(re.findall(r"^\| `", text, re.MULTILINE))  # 粗略估计
        return nums

    current_nums = extract_numbers(current)
    existing_nums = extract_numbers(existing)

    drift_items = []
    for key in ["tables", "endpoints", "tools"]:
        if current_nums.get(key) != existing_nums.get(key):
            drift_items.append(f"{key}: 文档 {existing_nums.get(key)} → 实际 {current_nums.get(key)}")

    if drift_items:
        return {"status": "drift", "items": drift_items, "current_stats": current_nums}
    return {"status": "ok", "current_stats": current_nums}


# ── 7. AGENTS.md 自动更新 ──

def generate_agents_md_sections():
    """Generate auto-updatable sections for AGENTS.md.

    Returns a dict: {section_name: markdown_content}
    Sections are designed to be placed between <!-- AUTO_STATS: {name} --> markers.
    """
    apps = scan_django_apps()
    tools = scan_tools()
    modules = scan_frontend_modules()

    total_tables = sum(a["table_count"] for a in apps)
    total_endpoints = sum(a["endpoint_count"] for a in apps)

    sections = {}

    # ── Summary line ──
    sections["summary"] = (
        f"{len(apps)} App · {total_tables} 表 · {total_endpoints} 端点 · "
        f"{len(tools)} Tool · {len(modules)} 前端模块"
    )

    # ── Django App table ──
    lines = []
    lines.append(f"| App | 表 | 端点 | 代码行数 | models | views | api | urls |")
    lines.append(f"|-----|:--:|:--:|:--:|:--:|:--:|:--:|:--:|")
    for a in apps:
        lines.append(
            f"| `{a['name']}` | {a['table_count']} | {a['endpoint_count']} | {a['total_lines']} | "
            f"{'✅' if a['has_models'] else '❌'} | "
            f"{'✅' if a['has_views'] else '❌'} | "
            f"{'✅' if a['has_api'] else '❌'} | "
            f"{'✅' if a['has_urls'] else '❌'} |"
        )
    lines.append(f"| **合计** | **{total_tables}** | **{total_endpoints}** | — | — | — | — | — |")
    sections["app-table"] = "\n".join(lines)

    # ── DB table list ──
    prefix_map = {
        "device_pool": "dp_", "element_locator": "el_", "case_manager": "cm_",
        "test_runner": "tr_", "report_generator": "rg_", "ai_assistant": "ai_",
        "workflow": "wf_", "dashboard": "—",
    }
    lines = []
    lines.append(f"| 前缀 | App | 表名 |")
    lines.append(f"|------|-----|------|")
    for a in apps:
        prefix = prefix_map.get(a["name"], "??")
        for t in a["tables"]:
            lines.append(f"| `{prefix}` | `{a['name']}` | `{t}` |")
    lines.append(f"| **合计** | **{len(apps)} App** | **{total_tables} 张表** |")
    sections["db-tables"] = "\n".join(lines)

    # ── Tool list ──
    lines = []
    lines.append(f"| Tool 名称 | 文件 | 只读 |")
    lines.append(f"|-----------|------|:--:|")
    for t in tools:
        lines.append(f"| `{t['name']}` | `{t['file']}` | {'✅' if t['is_read_only'] else '❌'} |")
    lines.append(f"| **合计 {len(tools)} 个** | | |")
    sections["tool-list"] = "\n".join(lines)

    # ── Frontend module list ──
    lines = []
    lines.append(f"| 模块 | index.vue | api.js | routes.js | store | composables | components | Vue 行数 |")
    lines.append(f"|------|:--:|:--:|:--:|:--:|:--:|:--:|:--:|")
    for m in modules:
        lines.append(
            f"| `{m['name']}` | {'✅' if m['has_index'] else '❌'} | "
            f"{'✅' if m['has_api'] else '❌'} | "
            f"{'✅' if m['has_routes'] else '❌'} | "
            f"{'✅' if m['has_store'] else '❌'} | "
            f"{'✅' if m['has_composables'] else '❌'} | "
            f"{'✅' if m['has_components'] else '❌'} | "
            f"{m['vue_lines']} |"
        )
    total_vue = sum(m["vue_lines"] for m in modules)
    lines.append(f"| **合计 {len(modules)} 个** | — | — | — | — | — | — | **{total_vue}** |")
    sections["frontend-modules"] = "\n".join(lines)

    return sections


def update_agents_md():
    """Read AGENTS.md, replace AUTO_STATS sections with current data, write back."""
    agents_md_path = PROJECT_ROOT / "AGENTS.md"
    if not agents_md_path.exists():
        print("❌ AGENTS.md 不存在")
        return 1

    content = agents_md_path.read_text(encoding="utf-8")
    sections = generate_agents_md_sections()

    updated = content
    changes = 0

    for section_name, new_content in sections.items():
        marker_start = f"<!-- AUTO_STATS: {section_name} -->"
        marker_end = f"<!-- AUTO_STATS_END: {section_name} -->"

        # Build the replacement block
        replacement = f"{marker_start}\n{new_content}\n{marker_end}"

        # Find existing block
        pattern = re.compile(
            rf"{re.escape(marker_start)}.*?{re.escape(marker_end)}",
            re.DOTALL,
        )
        if pattern.search(updated):
            updated = pattern.sub(replacement.replace("\\", "\\\\"), updated)
            changes += 1
        else:
            print(f"⚠️  未找到标记 {marker_start}，跳过 {section_name}")

    if changes > 0:
        agents_md_path.write_text(updated, encoding="utf-8")
        print(f"✅ AGENTS.md 已更新 — {changes} 个自动区块同步完成")
        print(f"   {sections['summary']}")
    else:
        print("⚠️  没有找到任何 AUTO_STATS 标记，未做修改")
        print("   请在 AGENTS.md 中添加 <!-- AUTO_STATS: {name} -->...<!-- AUTO_STATS_END: {name} --> 标记")

    return 0


# ── CLI ──

if __name__ == "__main__":
    if "--json" in sys.argv:
        print(generate_json())
    elif "--check-boundaries" in sys.argv:
        exit_code = 0

        # Firewall #2: ORM write violations
        orm_new, orm_known = scan_orm_write_violations()
        # Firewall #1: Internal import violations
        imp_new, imp_known = scan_cross_app_internal_imports()

        total_new = len(orm_new) + len(imp_new)
        total_known = len(orm_known) + len(imp_known)

        if total_new > 0:
            print(f"╔══════════════════════════════════════════╗")
            print(f"║  🔴 模块边界违规 — {total_new} 个新违规（已知 {total_known} 条技术债）║")
            print(f"╚══════════════════════════════════════════╝")
            print()

            if orm_new:
                print(f"── 防火墙 #2: 跨模块 ORM 写入 ──")
                for v in orm_new:
                    print(f"  {v['file']}:{v['line']}  {v['model']}.{v['pattern']}")
                    print(f"    → {v['snippet']}")
                print(f"  修复: 跨 App 写操作必须走目标 App 的 api.py")
                print()

            if imp_new:
                print(f"── 防火墙 #1: 跨模块内部实现 import ──")
                for v in imp_new:
                    print(f"  {v['file']}:{v['line']}  from apps.{v['source_app']}.{v['module']} import {v['imports']}")
                    print(f"    → {v['snippet']}")
                print(f"  修复: 跨 App 只能 import api.py 或 models，禁止 import 内部实现")
                print()

            print(f"  如果是有意豁免，请添加到 .claude/boundary-whitelist.json")
            exit_code = 1
        else:
            if total_known:
                print(f"✅ 模块边界检查通过（已知 {total_known} 条技术债已登记）")
            else:
                print(f"✅ 模块边界检查通过 — 零违规")
            exit_code = 0

        sys.exit(exit_code)
    elif "--check-frontend" in sys.argv:
        violations = scan_file_size_violations()
        vue_violations = [v for v in violations if v['type'] == 'vue']
        if not vue_violations:
            print("✅ 前端文件体积检查通过 ─ 所有 .vue 文件 < 500 行")
            sys.exit(0)

        # Load frontend whitelist
        fwl_path = PROJECT_ROOT / ".claude" / "frontend-whitelist.json"
        whitelist = set()
        if fwl_path.exists():
            try:
                data = json.loads(fwl_path.read_text(encoding="utf-8"))
                for w in data.get("whitelist", []):
                    whitelist.add(w.get("file", ""))
            except Exception:
                pass

        new_violations = [v for v in vue_violations if v['file'] not in whitelist]

        if new_violations:
            print(f"🔴 前端文件体积超标 ─ {len(new_violations)} 个新增超标文件:\n")
            for v in new_violations[:10]:
                print(f"  {v['file']}: {v['lines']}行 (+{v['excess']})")
            print(f"\n  修复: CSS外置 / composable提取 / 常量外提 / 子组件拆分")
            print(f"  如需豁免: 添加到 .claude/frontend-whitelist.json")
            sys.exit(1)
        else:
            known = len(vue_violations)
            print(f"✅ 无新增前端文件超标（已知 {known} 个文件在白名单中）")
            sys.exit(0)
    elif "--check-md" in sys.argv:
        result = check_drift()
        if result["status"] == "drift":
            print(f"🔴 架构文档落后于代码: {', '.join(result['items'])}")
            sys.exit(1)
        elif result["status"] == "no_auto_section":
            print("💡 项目架构.md 需要初始化 ARCH_STATS 区域")
            sys.exit(0)
        elif result["status"] == "no_doc":
            print("💡 项目架构.md 不存在")
            sys.exit(0)
        else:
            print("✅ 架构文档与实际代码一致")
            sys.exit(0)
    elif "--update-agents-md" in sys.argv:
        sys.exit(update_agents_md())
    else:
        print(generate_markdown())
