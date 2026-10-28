#!/usr/bin/env python3
"""
Architecture stats generator — 扫描代码库，输出当前架构的可度量事实。

用途:
  - architect agent 被调用时自动运行，对比指定架构文档的 auto 区域
  - 发现 drift 后自动更新文档的事实部分
  - 也支持 --json 输出，供 CI/hook 消费

用法:
  python utils/gen_arch_stats.py                              # 输出 Markdown 片段
  python utils/gen_arch_stats.py --json                       # 输出 JSON（供 CI/hook 消费）
  python utils/gen_arch_stats.py --check-md --doc <文档路径>    # 对比架构文档，输出 drift 报告
  python utils/gen_arch_stats.py --check-boundaries [--verbose] # 模块边界检查（CI Job 4）
  python utils/gen_arch_stats.py --check-frontend             # 前端文件体积检查（CI Job 5）
  python utils/gen_arch_stats.py --update-agents-md           # 同步 AGENTS.md 的 AUTO_STATS 区块
"""

import ast
import json
import logging
import re
import sys

from collections import defaultdict
from pathlib import Path

# 控制台输出统一 UTF-8：本脚本会打印 emoji（📝 / ✅ / 🔴/❌）。
# Windows 中文环境下 stdout 默认是 GBK，被管道/重定向捕获时 print 会抛
# UnicodeEncodeError 并以退出码 1 结束——与「发现边界违规」无法区分，会让
# CI 与 dsh-plugins/arch-gate（execFile 捕获 + passMarker "零违规"）误判失败。
# 修复放在脚本内而非要求调用方设 PYTHONIOENCODING：单点覆盖所有输出路径。
# 被 pytest 等捕获时 stdout 可能不是 TextIOWrapper，故用 hasattr 守卫。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# ── 仓库布局常量 ──
# 源码位于 `backend/` 下，跨 App import 统一写作 `backend.apps.<app>`。
# 早期版本的脚本按「根目录即 Django 项目、import 写作 apps.<app>」写死了路径与正则，
# 迁目录后所有扫描都会静默返回空结果——集中在这里，改目录只改这一处。
BACKEND_DIR = PROJECT_ROOT / "backend"
APPS_DIR = BACKEND_DIR / "apps"
GATEWAY_DIR = BACKEND_DIR / "gateway"
SETTINGS_PATH = BACKEND_DIR / "config" / "settings.py"
# 供 re 使用的「跨 App import」前缀（不含结尾点，调用方自行拼接）
APP_IMPORT_PREFIX = r"backend\.apps"
# 表前缀归属：App 名 → 表名前缀。新增 App 时在此登记，未登记会显示 "??"。
TABLE_PREFIX = {
    "device_pool": "dp_",
    "case_manager": "cm_",
    "task_list": "task_",
    "bug_manager": "bug_",
    "ai_assistant": "ai_",
    "report_generator": "rg_",
    "workflow": "wf_",
    "serial_log": "sl_",
    "accounts": "auth_",
    "dashboard": "—",
}


# ── 1. Django App 扫描 ──


def _viewset_actions(app_dir: Path, class_name: str):
    """找出 ViewSet 类上的 `@action` 装饰器。

    Args:
        app_dir: App 目录。
        class_name: ViewSet 类名。

    Returns:
        [(detail, url_path), ...]；detail 为 True 表示挂在详情路由下。
        找不到类时返回空表。
    """
    for view_file in sorted(app_dir.glob("views*.py")):
        try:
            tree = ast.parse(view_file.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not (isinstance(node, ast.ClassDef) and node.name == class_name):
                continue
            actions = []
            for member in node.body:
                if not isinstance(member, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    continue
                for dec in member.decorator_list:
                    if not (isinstance(dec, ast.Call) and getattr(dec.func, "id", "") == "action"):
                        continue
                    detail = False
                    url_path = member.name.replace("_", "-")
                    for kw in dec.keywords:
                        if kw.arg == "detail":
                            detail = isinstance(kw.value, ast.Constant) and kw.value.value is True
                        elif kw.arg == "url_path" and isinstance(kw.value, ast.Constant):
                            url_path = kw.value.value
                    actions.append((detail, url_path))
            return actions
    return []


def count_app_endpoints(app_dir: Path):
    """统计一个 App 的端点数量。

    口径：唯一 URL 路径，同一路径多方法计 1。字面 `path()` / `re_path()` 各计 1；
    `router.register()` 按其 ViewSet 展开为「集合路由 + 详情路由 + 每个 @action」，
    与 DefaultRouter 实际生成的路径一致。

    Args:
        app_dir: App 目录。

    Returns:
        端点条数。
    """
    urls_path = app_dir / "urls.py"
    if not urls_path.exists():
        return 0
    content = urls_path.read_text(encoding="utf-8")

    count = len(re.findall(r"^\s*(?:path|re_path)\(", content, re.MULTILINE))
    for match in re.finditer(r"router\.register\(\s*r?[\"']([^\"']+)[\"']\s*,\s*(\w+)", content):
        prefix, viewset = match.group(1), match.group(2)
        count += 2  # 集合路由 `{prefix}/` + 详情路由 `{prefix}/{lookup}/`
        count += len(_viewset_actions(app_dir, viewset))
    return count


def scan_django_apps():
    """扫描 backend/apps/ 下所有 Django App，返回结构化数据。"""
    apps_dir = APPS_DIR
    apps = []
    for d in sorted(apps_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
            continue
        if not (d / "__init__.py").exists() and not (d / "models.py").exists():
            continue

        app = {
            "name": d.name,
            "has_models": (d / "models.py").exists(),
            # 视图可拆成多片（views_pages.py / views_drf.py ...），故按前缀识别
            "has_views": (d / "views.py").exists()
            or any(d.glob("views*.py"))
            or (d / "views").is_dir(),
            "has_api": (d / "api.py").exists(),
            "has_urls": (d / "urls.py").exists(),
        }

        # 统计表数量（含 models_*.py 分表，如 case_manager 的 models_web/models_storage/models_api）
        app["table_count"] = 0
        app["tables"] = []
        model_files = sorted(d.glob("models*.py"))
        for models_path in model_files:
            content = models_path.read_text(encoding="utf-8")
            app["table_count"] += len(re.findall(r"db_table\s*=\s*['\"](\w+)['\"]", content))
            app["tables"].extend(re.findall(r"db_table\s*=\s*['\"](\w+)['\"]", content))

        # 统计端点数量（字面 path() + DRF Router 生成的路由）
        app["endpoint_count"] = count_app_endpoints(d)

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


# ── 2. Agent 工具扫描 ──

TOOLS_CONFIG_PATH = PROJECT_ROOT / "engines" / "agents" / "tools_config.py"
TOOLS_DIR = PROJECT_ROOT / "engines" / "agents" / "tools"


def _literal_str_tuple(node):
    """把 ast.Tuple / ast.List 里的字符串常量取成 list；非字面量返回空表。"""
    if not isinstance(node, (ast.Tuple, ast.List)):
        return []
    return [e.value for e in node.elts if isinstance(e, ast.Constant) and isinstance(e.value, str)]


def _tool_source_index():
    """建立 工具名 → 定义文件（相对仓库根）的索引。

    Returns:
        dict[str, str]：函数名映射到 `engines/agents/tools/tool_*.py` 的相对路径。
    """
    index = {}
    if not TOOLS_DIR.exists():
        return index
    for path in sorted(TOOLS_DIR.glob("tool_*.py")):
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError:
            continue
        rel = path.relative_to(PROJECT_ROOT).as_posix()
        # 先收模块级函数，再补 build_*_tools() 内部的闭包工具（如 screenshot_page）
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                index.setdefault(node.name, rel)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                index.setdefault(node.name, rel)
    return index


def scan_tools():
    """扫描工具注册表 `engines/agents/tools_config.py`，返回已装配给角色的工具。

    常驻工具来自 `EXECUTOR_BASIC_TOOL_NAMES` / `VERIFIER_BASIC_TOOL_NAMES`，
    可开关工具来自 `EXECUTOR_TOOL_GROUPS` 里每个 `ToolGroupSpec` 的 `tool_names`。
    同一工具只登记一次，角色列累计所有引用它的角色。

    Returns:
        工具列表，元素含 name / group / roles / file。
    """
    if not TOOLS_CONFIG_PATH.exists():
        return []
    try:
        tree = ast.parse(TOOLS_CONFIG_PATH.read_text(encoding="utf-8"))
    except SyntaxError:
        return []

    files = _tool_source_index()
    tools = {}  # name → 记录；dict 保序，保证输出稳定

    def add(name, group, role):
        """登记一个工具；重复出现时只补角色，不覆盖首次出现的位置。"""
        item = tools.setdefault(
            name,
            {"name": name, "group": group, "roles": [], "file": files.get(name, "")},
        )
        if role not in item["roles"]:
            item["roles"].append(role)

    for node in tree.body:
        is_assign = isinstance(node, ast.Assign)
        if not is_assign and not isinstance(node, ast.AnnAssign):
            continue
        target = node.targets[0] if is_assign else node.target
        if not isinstance(target, ast.Name) or node.value is None:
            continue

        if target.id == "EXECUTOR_BASIC_TOOL_NAMES":
            for name in _literal_str_tuple(node.value):
                add(name, "basic", "executor")
        elif target.id == "VERIFIER_BASIC_TOOL_NAMES":
            for name in _literal_str_tuple(node.value):
                add(name, "basic", "verifier")
        elif target.id == "EXECUTOR_TOOL_GROUPS" and isinstance(node.value, ast.Tuple):
            for call in node.value.elts:
                if not isinstance(call, ast.Call):
                    continue
                group_name, names = "", []
                for kw in call.keywords:
                    if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                        group_name = kw.value.value
                    elif kw.arg == "tool_names":
                        names = _literal_str_tuple(kw.value)
                for name in names:
                    add(name, group_name, "executor")

    return list(tools.values())


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
    apps_dir = APPS_DIR
    for py_file in apps_dir.rglob("*.py"):
        if "migrations" in str(py_file) or "__pycache__" in str(py_file):
            continue
        lines = len(py_file.read_text(encoding="utf-8").splitlines())
        if lines > py_limit:
            violations.append(
                {
                    "file": py_file.relative_to(PROJECT_ROOT).as_posix(),
                    "lines": lines,
                    "limit": py_limit,
                    "excess": lines - py_limit,
                    "type": "python",
                }
            )

    # Vue 文件
    frontend_dir = PROJECT_ROOT / "frontend" / "src"
    for vue_file in frontend_dir.rglob("*.vue"):
        lines = len(vue_file.read_text(encoding="utf-8").splitlines())
        if lines > vue_limit:
            violations.append(
                {
                    "file": vue_file.relative_to(PROJECT_ROOT).as_posix(),
                    "lines": lines,
                    "limit": vue_limit,
                    "excess": lines - vue_limit,
                    "type": "vue",
                }
            )

    violations.sort(key=lambda v: -v["excess"])
    return violations


# ── 5. 跨模块依赖扫描 ──


def scan_cross_app_imports():
    """扫描跨 App import 关系（被依赖 App → 依赖来源文件）。"""
    # 从 INSTALLED_APPS 获取 App 列表（条目形如 "backend.apps.device_pool"）
    app_names = list(
        dict.fromkeys(
            re.findall(
                rf"['\"]{APP_IMPORT_PREFIX}\.(\w+)['\"]",
                SETTINGS_PATH.read_text(encoding="utf-8"),
            )
        )
    )  # 去重：settings 里另有菜单图标字典会重复出现 App 名

    # 按目标 App 分组
    targets = defaultdict(set)  # {target_app: {source_file1, source_file2, ...}}

    for scan_dir in [APPS_DIR, GATEWAY_DIR]:
        for py_file in scan_dir.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue
            content = py_file.read_text(encoding="utf-8")
            for app_name in app_names:
                pattern = rf"from\s+{APP_IMPORT_PREFIX}\.{app_name}\."
                if re.search(pattern, content):
                    # 排除同 App 内的 import
                    rel_path = py_file.relative_to(PROJECT_ROOT).as_posix()
                    if f"apps/{app_name}/" not in rel_path:
                        targets[app_name].add(rel_path)

    return {app: sorted(sources) for app, sources in sorted(targets.items())}


# ── 5b. 跨模块 ORM 写违规扫描（防火墙 #2）──


# 已知违规白名单加载
def _load_boundary_whitelist():
    """Load known-violation whitelist from utils/boundary-whitelist.json."""
    whitelist_path = PROJECT_ROOT / "utils" / "boundary-whitelist.json"
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
    apps_dir = APPS_DIR
    whitelist = _load_boundary_whitelist()

    # Build a mapping: model_class_name → app_name
    model_to_app = {}  # {"Device": "device_pool", ...}
    for d in sorted(apps_dir.iterdir()):
        if not d.is_dir() or d.name.startswith("_") or d.name.startswith("."):
            continue
        for models_path in sorted(d.glob("models*.py")):
            content = models_path.read_text(encoding="utf-8")
            for m in re.findall(r"class\s+(\w+)\s*\(\s*models\.Model\s*\)", content):
                model_to_app[m] = d.name

    # Write patterns to detect
    # Pattern 1: ModelName.objects.create(   — direct INSERT
    # Pattern 2: ModelName.objects.update(   — direct bulk UPDATE
    # Pattern 3: ModelName.objects.filter(...).update( — queryset UPDATE
    # Pattern 4: ModelName.objects.filter(...).delete( — queryset DELETE
    WRITE_PATTERNS = [
        (r"\b({model})\s*\.\s*objects\s*\.\s*create\s*\(", "objects.create()"),
        (r"\b({model})\s*\.\s*objects\s*\.\s*update\s*\(", "objects.update()"),
        (
            r"\b({model})\s*\.\s*objects\s*\.\s*filter\s*\([^)]*\)\s*\.\s*update\s*\(",
            "filter().update()",
        ),
        (
            r"\b({model})\s*\.\s*objects\s*\.\s*filter\s*\([^)]*\)\s*\.\s*delete\s*\(",
            "filter().delete()",
        ),
    ]

    # Scan all source files
    scan_dirs = [apps_dir]
    violations = []

    for scan_dir in scan_dirs:
        for py_file in scan_dir.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue
            if py_file.name == "__init__.py" and py_file.stat().st_size < 100:
                continue

            rel_path = str(py_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
            try:
                content = py_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # Find which models this file imports from OTHER apps
            imported_models = {}  # {ModelName: source_app}
            for m in re.finditer(
                rf"from\s+{APP_IMPORT_PREFIX}\.(\w+)\s*\.\s*models\s+import\s+([^#\n]+)",
                content,
            ):
                source_app = m.group(1)
                imported_str = m.group(2)
                # Extract individual model names from the import
                names = re.findall(r"\b(\w+)\b", imported_str.split("#")[0])
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
                        line_no = content[: match.start()].count("\n") + 1
                        violations.append(
                            {
                                "file": rel_path,
                                "line": line_no,
                                "model": model_name,
                                "source_app": source_app,
                                "pattern": pattern_label,
                                "snippet": content.split("\n")[line_no - 1].strip()[:120],
                            }
                        )

    # Match against whitelist
    def _whitelist_key(v):
        return f"{v['file']}:{v['line']}:{v['model']}:{v['pattern']}"

    known = []
    new = []
    whitelist_keys = set()
    for w in whitelist:
        whitelist_keys.add(
            f"{w.get('file', '')}:{w.get('line', 0)}:{w.get('model', '')}:{w.get('pattern', '')}"
        )

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
    apps_dir = APPS_DIR

    # Apps that have these internal modules
    INTERNAL_MODULES = ["service", "runner", "consumer", "callbacks", "state_machine"]

    whitelist = _load_boundary_whitelist()
    violations = []

    for scan_dir in [apps_dir]:
        for py_file in scan_dir.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue

            rel_path = str(py_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
            try:
                content = py_file.read_text(encoding="utf-8")
            except Exception:
                continue

            # Detect: from backend.apps.X.{internal} import ...
            for mod in INTERNAL_MODULES:
                for m in re.finditer(
                    rf"from\s+{APP_IMPORT_PREFIX}\.(\w+)\.{mod}\s+import\s+([^#\n]+)",
                    content,
                ):
                    source_app = m.group(1)
                    imported_names = m.group(2).strip()
                    # Skip if same app
                    if f"apps/{source_app}/" in rel_path:
                        continue
                    line_no = content[: m.start()].count("\n") + 1
                    violations.append(
                        {
                            "file": rel_path,
                            "line": line_no,
                            "source_app": source_app,
                            "module": mod,
                            "imports": imported_names[:100],
                            "snippet": content.split("\n")[line_no - 1].strip()[:120],
                        }
                    )

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


def _iter_code_line_nos(content):
    """返回含真实代码的行号集合（跳过注释/字符串/docstring）。

    tokenize 失败时返回 None（调用方退化为所有行皆代码）。
    """
    import io
    import tokenize as _tokenize

    code_lines = set()
    try:
        for tok in _tokenize.generate_tokens(io.StringIO(content).readline):
            if tok.type not in (
                _tokenize.COMMENT,
                _tokenize.STRING,
                _tokenize.NL,
                _tokenize.NEWLINE,
                _tokenize.INDENT,
                _tokenize.DEDENT,
                _tokenize.ENDMARKER,
            ):
                code_lines.add(tok.start[0])
    except Exception:
        return None
    return code_lines


def scan_engine_leak_violations():
    """Detect engine capability leak to upper layers (L1c boundary).

    Rule (engine boundary): only `engines/` may import third-party
    engine libs (uiautomator2) or touch concrete engine implementations.
    Upper layers (backend/apps/, backend/gateway/) must consume device capability ONLY via
    `engines.device.base.UiEngine` protocol (obtained through `engines.device.registry`).

    Detects 3 leak categories:
      - engine_lib:  backend/apps 或 backend/gateway importing uiautomator2 directly
      - engine_impl: backend/apps 或 backend/gateway importing engines.device.android concrete implementation
      - raw_handle:  backend/apps 或 backend/gateway accessing .u2 raw engine handles（仅代码行）

    Returns (new_violations, known_violations) — new violations fail CI.
    """
    scan_dirs = [APPS_DIR, GATEWAY_DIR]
    whitelist = _load_boundary_whitelist()

    # 行首 import 模式：[ \t] 而非 \s，避免 \s 跨空行吞换行导致行号偏移
    import_patterns = [
        (
            "engine_lib",
            re.compile(r"^[ \t]*(?:import|from)[ \t]+(uiautomator2)\b", re.MULTILINE),
        ),
        (
            "engine_impl",
            re.compile(r"^[ \t]*(?:import|from)[ \t]+engines\.device\.android\b", re.MULTILINE),
        ),
    ]
    raw_handle_re = re.compile(r"\.u2\b")

    violations = []
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for py_file in scan_dir.rglob("*.py"):
            if "migrations" in str(py_file) or "__pycache__" in str(py_file):
                continue
            rel_path = str(py_file.relative_to(PROJECT_ROOT)).replace("\\", "/")
            try:
                content = py_file.read_text(encoding="utf-8")
            except Exception:
                continue
            lines = content.split("\n")

            for category, compiled in import_patterns:
                for m in compiled.finditer(content):
                    line_no = content[: m.start()].count("\n") + 1
                    violations.append(
                        {
                            "file": rel_path,
                            "line": line_no,
                            "category": category,
                            "snippet": lines[line_no - 1].strip()[:120],
                        }
                    )

            code_lines = _iter_code_line_nos(content)
            seen_raw = set()
            for m in raw_handle_re.finditer(content):
                line_no = content[: m.start()].count("\n") + 1
                if code_lines is not None and line_no not in code_lines:
                    continue
                # 同一行访问 .u2 只计一次（按行去重）
                key = (rel_path, line_no)
                if key in seen_raw:
                    continue
                seen_raw.add(key)
                violations.append(
                    {
                        "file": rel_path,
                        "line": line_no,
                        "category": "raw_handle",
                        "snippet": lines[line_no - 1].strip()[:120],
                    }
                )

    # Match against whitelist（pattern == "engine-leak" 的条目）
    def _key(v):
        return f"{v['file']}:{v['line']}:engine-leak:{v['category']}"

    known = []
    new = []
    whitelist_keys = set()
    for w in whitelist:
        if w.get("pattern") != "engine-leak":
            continue
        whitelist_keys.add(
            f"{w.get('file', '')}:{w.get('line', 0)}:engine-leak:{w.get('category', '')}"
        )

    for v in violations:
        if _key(v) in whitelist_keys:
            known.append(v)
        else:
            new.append(v)

    return new, known


# ── 6. 设备状态 ──


def scan_device_statuses():
    """从 device_pool/models.py 提取设备状态定义。"""
    models_path = APPS_DIR / "device_pool" / "models.py"
    if not models_path.exists():
        return {"count": 0, "statuses": []}

    content = models_path.read_text(encoding="utf-8")
    # Pattern 1: comment-based # ONLINE | BUSY | OFFLINE
    for m in re.finditer(
        r"#\s*((?:ONLINE|BUSY|OFFLINE|DISCONNECTED)(?:\s*\|\s*(?:ONLINE|BUSY|OFFLINE|DISCONNECTED))*)",
        content,
    ):
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
    lines.append(f"<!-- ARCH_STATS — 由 utils/gen_arch_stats.py 自动生成，请勿手动编辑 -->")
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
        prefix = TABLE_PREFIX.get(a["name"], "??")
        for t in a["tables"]:
            lines.append(f"| `{prefix}` | `{a['name']}` | `{t}` |")
    lines.append("")

    # Agent 工具
    lines.append("### Agent 工具清单（已装配给角色）")
    lines.append("")
    lines.append(f"| Tool 名称 | 工具组 | 角色 | 定义文件 |")
    lines.append(f"|-----------|--------|------|----------|")
    for t in tools:
        roles = "/".join(t["roles"])
        lines.append(f"| `{t['name']}` | `{t['group']}` | {roles} | `{t['file']}` |")
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
            lines.append(
                f"| `{v['file']}` | {v['lines']} | {v['limit']} | +{v['excess']} | {v['type']} |"
            )
    else:
        lines.append("✅ 无超标文件")
    lines.append("")

    lines.append(f"<!-- ARCH_STATS_END -->")

    # ── 设备状态 ──
    dev_status = scan_device_statuses()
    lines.append("### 设备状态定义")
    lines.append("")
    lines.append(
        f"**{dev_status['count']} 种状态**: " + " · ".join(f"`{s}`" for s in dev_status["statuses"])
    )
    lines.append("")

    return "\n".join(lines)


def generate_json():
    """输出 JSON 格式（供 CI/hook 消费）。"""
    new_violations, known_violations = scan_orm_write_violations()
    eng_new, eng_known = scan_engine_leak_violations()
    return json.dumps(
        {
            "django_apps": scan_django_apps(),
            "tools": scan_tools(),
            "frontend_modules": scan_frontend_modules(),
            "file_size_violations": scan_file_size_violations(),
            "cross_app_imports": scan_cross_app_imports(),
            "orm_write_violations": {
                "new": new_violations,
                "known": known_violations,
            },
            "engine_leak_violations": {
                "new": eng_new,
                "known": eng_known,
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
                "engine_leak_violation_new": len(eng_new),
                "engine_leak_violation_known": len(eng_known),
            },
        },
        indent=2,
        ensure_ascii=False,
    )


def check_drift(doc_path: Path):
    """对比给定架构文档中的 auto 区域，检测 drift。"""
    if not doc_path.exists():
        return {"status": "no_doc", "message": f"{doc_path.name} 不存在"}

    doc_content = doc_path.read_text(encoding="utf-8")
    current = generate_markdown()

    # 提取文档中的 auto 区域
    match = re.search(r"<!-- ARCH_STATS.*?-->.*?<!-- ARCH_STATS_END -->", doc_content, re.DOTALL)
    if not match:
        return {
            "status": "no_auto_section",
            "message": f"{doc_path.name} 中无 ARCH_STATS 区域，需要初始化",
        }

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
            drift_items.append(
                f"{key}: 文档 {existing_nums.get(key)} → 实际 {current_nums.get(key)}"
            )

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
    lines = []
    lines.append(f"| 前缀 | App | 表名 |")
    lines.append(f"|------|-----|------|")
    for a in apps:
        prefix = TABLE_PREFIX.get(a["name"], "??")
        for t in a["tables"]:
            lines.append(f"| `{prefix}` | `{a['name']}` | `{t}` |")
    lines.append(f"| **合计** | **{len(apps)} App** | **{total_tables} 张表** |")
    sections["db-tables"] = "\n".join(lines)

    # ── Tool list ──
    lines = []
    lines.append(f"| Tool 名称 | 工具组 | 角色 | 定义文件 |")
    lines.append(f"|-----------|--------|------|----------|")
    for t in tools:
        roles = "/".join(t["roles"])
        lines.append(f"| `{t['name']}` | `{t['group']}` | {roles} | `{t['file']}` |")
    lines.append(f"| **合计 {len(tools)} 个** | | | |")
    sections["tool-list"] = "\n".join(lines)

    # ── Frontend module list ──
    lines = []
    lines.append(
        f"| 模块 | index.vue | api.js | routes.js | store | composables | components | Vue 行数 |"
    )
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
        print(
            "   请在 AGENTS.md 中添加 <!-- AUTO_STATS: {name} -->...<!-- AUTO_STATS_END: {name} --> 标记"
        )

    return 0


# ── CLI ──


def _setup_boundary_logger():
    """配置边界检查日志到 logs/boundary-check.log。

    Returns:
        (logger, log_path)：日志已落盘时 log_path 为文件路径；只读检出无法写盘时为空串。
    """
    log_dir = PROJECT_ROOT / "logs"
    logger = logging.getLogger("boundary-check")
    for h in list(logger.handlers):
        logger.removeHandler(h)
        h.close()
    log_path = log_dir / "boundary-check.log"
    try:
        log_dir.mkdir(exist_ok=True)
        handler = logging.FileHandler(log_path, encoding="utf-8")
    except OSError:
        # 只读检出（沙箱 / 受限 CI 容器）无法落盘日志，退化为仅控制台输出；
        # 检查结果与退出码不受影响，但明确告知日志没写成功，避免静默。
        return logger, ""
    handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger, str(log_path)


def _known_debt_lines(orm_known, imp_known, eng_known):
    """返回已知技术债明细的文本行列表（--verbose 时打印 + 写日志）。"""
    notes = {}
    for w in _load_boundary_whitelist():
        notes.setdefault((w.get("file", ""), w.get("line", 0)), w.get("note", ""))

    def _note(v):
        return notes.get((v["file"], v["line"]), "")

    sections = []
    if orm_known:
        sections.append(
            (
                "防火墙 #2: 跨模块 ORM 写入",
                [
                    (
                        f"  {v['file']}:{v['line']}  {v['model']}.{v['pattern']}",
                        v["snippet"],
                        _note(v),
                    )
                    for v in orm_known
                ],
            )
        )
    if imp_known:
        sections.append(
            (
                "防火墙 #1: 跨模块内部实现 import",
                [
                    (
                        f"  {v['file']}:{v['line']}  from backend.apps.{v['source_app']}.{v['module']} import {v['imports']}",
                        v["snippet"],
                        _note(v),
                    )
                    for v in imp_known
                ],
            )
        )
    if eng_known:
        sections.append(
            (
                "L1c 引擎边界: 引擎能力泄露上层",
                [
                    (f"  {v['file']}:{v['line']}  [{v['category']}]", v["snippet"], _note(v))
                    for v in eng_known
                ],
            )
        )

    if not sections:
        return []
    lines = ["── 已知技术债明细（白名单，不阻塞）──"]
    for title, items in sections:
        lines.append(f"【{title}】")
        for head, snippet, note in items:
            lines.append(head)
            if snippet:
                lines.append(f"    → {snippet}")
            if note:
                lines.append(f"    ✎ {note}")
        lines.append("")
    return lines


if __name__ == "__main__":
    if "--json" in sys.argv:
        print(generate_json())
    elif "--check-boundaries" in sys.argv:
        verbose = "--verbose" in sys.argv or "-v" in sys.argv
        logger, log_path = _setup_boundary_logger()
        exit_code = 0

        # Firewall #2: ORM write violations
        orm_new, orm_known = scan_orm_write_violations()
        # Firewall #1: Internal import violations
        imp_new, imp_known = scan_cross_app_internal_imports()
        # L1c 引擎边界: 引擎能力泄露上层
        eng_new, eng_known = scan_engine_leak_violations()

        total_new = len(orm_new) + len(imp_new) + len(eng_new)
        total_known = len(orm_known) + len(imp_known) + len(eng_known)

        out = []  # 报告行（控制台打印 + 日志落盘）

        if total_new > 0:
            out.append("╔══════════════════════════════════════════╗")
            out.append(f"║  🔴 模块边界违规 — {total_new} 个新违规（已知 {total_known} 条技术债）║")
            out.append("╚══════════════════════════════════════════╝")
            out.append("")

            if orm_new:
                out.append("── 防火墙 #2: 跨模块 ORM 写入 ──")
                for v in orm_new:
                    out.append(f"  {v['file']}:{v['line']}  {v['model']}.{v['pattern']}")
                    out.append(f"    → {v['snippet']}")
                out.append("  修复: 跨 App 写操作必须走目标 App 的 api.py")
                out.append("")

            if imp_new:
                out.append("── 防火墙 #1: 跨模块内部实现 import ──")
                for v in imp_new:
                    out.append(
                        f"  {v['file']}:{v['line']}  from apps.{v['source_app']}.{v['module']} import {v['imports']}"
                    )
                    out.append(f"    → {v['snippet']}")
                out.append("  修复: 跨 App 只能 import api.py 或 models，禁止 import 内部实现")
                out.append("")

            if eng_new:
                out.append("── L1c 引擎边界: 引擎能力泄露上层 ──")
                for v in eng_new:
                    out.append(f"  {v['file']}:{v['line']}  [{v['category']}]")
                    out.append(f"    → {v['snippet']}")
                out.append(
                    "  修复: 上层只经 engines.device.base.UiEngine 协议 / engines.device.registry 工厂消费设备能力"
                )
                out.append("")

            out.append("  如果是有意豁免，请添加到 utils/boundary-whitelist.json")
            if verbose and total_known:
                out.extend(_known_debt_lines(orm_known, imp_known, eng_known))
            exit_code = 1
        else:
            if total_known:
                out.append(f"✅ 模块边界检查通过（已知 {total_known} 条技术债已登记）")
                if verbose:
                    out.extend(_known_debt_lines(orm_known, imp_known, eng_known))
            else:
                out.append("✅ 模块边界检查通过 — 零违规")
            exit_code = 0

        # 写日志（整份报告一次落盘，带时间戳前缀）
        logger.info("\n".join(out))

        # 控制台：首行说明日志路径，再打印明细
        if log_path:
            print(f"📝 详细日志: {log_path}")
        else:
            print("⚠️  logs/ 不可写，本次未落盘日志（仅控制台输出）")
        print()
        for line in out:
            print(line)

        sys.exit(exit_code)
    elif "--check-frontend" in sys.argv:
        violations = scan_file_size_violations()
        vue_violations = [v for v in violations if v["type"] == "vue"]
        if not vue_violations:
            print("✅ 前端文件体积检查通过 ─ 所有 .vue 文件 < 500 行")
            sys.exit(0)

        # Load frontend whitelist
        fwl_path = PROJECT_ROOT / "utils" / "frontend-whitelist.json"
        whitelist = set()
        if fwl_path.exists():
            try:
                data = json.loads(fwl_path.read_text(encoding="utf-8"))
                for w in data.get("whitelist", []):
                    whitelist.add(w.get("file", ""))
            except Exception:
                pass

        new_violations = [v for v in vue_violations if v["file"] not in whitelist]

        if new_violations:
            print(f"🔴 前端文件体积超标 ─ {len(new_violations)} 个新增超标文件:\n")
            for v in new_violations[:10]:
                print(f"  {v['file']}: {v['lines']}行 (+{v['excess']})")
            print(f"\n  修复: CSS外置 / composable提取 / 常量外提 / 子组件拆分")
            print(f"  如需豁免: 添加到 utils/frontend-whitelist.json")
            sys.exit(1)
        else:
            known = len(vue_violations)
            print(f"✅ 无新增前端文件超标（已知 {known} 个文件在白名单中）")
            sys.exit(0)
    elif "--check-md" in sys.argv:
        if "--doc" not in sys.argv or sys.argv.index("--doc") + 1 >= len(sys.argv):
            print("用法: python utils/gen_arch_stats.py --check-md --doc <架构文档路径>")
            sys.exit(2)
        result = check_drift(Path(sys.argv[sys.argv.index("--doc") + 1]))
        if result["status"] == "drift":
            print(f"🔴 架构文档落后于代码: {', '.join(result['items'])}")
            sys.exit(1)
        elif result["status"] == "no_auto_section":
            print(f"💡 {result['message']}")
            sys.exit(0)
        elif result["status"] == "no_doc":
            print(f"💡 {result['message']}")
            sys.exit(0)
        else:
            print("✅ 架构文档与实际代码一致")
            sys.exit(0)
    elif "--update-agents-md" in sys.argv:
        sys.exit(update_agents_md())
    else:
        print(generate_markdown())
