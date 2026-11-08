"""项目看板数据生成器：扫仓库，产出 data/board.json 与 data/board.js。

本模块的业务功能如下：
1. collect_frontend: 调 tools/count_frontend.mjs（TypeScript 语法树）统计前端各模块。
2. collect_backend: AST 扫 backend/apps/<app> 的文件/类/方法/非空行；功能数取 API 端点数。
3. collect_engines: AST 扫 engines/<子包>；功能数取模块 docstring 的「简介说明」条目数。
4. write_outputs: 写 data/board.json（机器读）与 data/board.js（页面用，file:// 可加载）。

口径（页面脚注同步展示，改之前先想清"功能"到底数什么）：
- 功能：前端=路由条目数；后端=DRF API 端点数；引擎=模块 docstring 声明的能力条目数。
  三层口径不同，**只做各自量级对照，不可横向相加比较**。
- 文件：代码文件数（.py/.vue/.ts/.js；排除 __pycache__、migrations、vendor）。
- 类：class 定义数（AST ClassDeclaration / ClassDef）。
- 方法：命名函数/方法定义数（不含 lambda、匿名回调）。
- 代码行：非空物理行。

python -m 调试路径: 本脚本在 dev_docs 下，直接运行 `python dev_docs/project-viz/tools/gen_board_data.py`。

Usage:
    python dev_docs/project-viz/tools/gen_board_data.py          # 重新生成数据
    python dev_docs/project-viz/tools/gen_board_data.py --check  # 只报告与现有数据是否有差异
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve()
PROJECT_VIZ = HERE.parent.parent
REPO = next(
    (p for p in HERE.parents if (p / "engines" / "AGENTS.md").is_file()),
    HERE.parents[-1],
)
DATA_DIR = PROJECT_VIZ / "data"

EXCLUDE_DIRS = frozenset(
    {
        "__pycache__",
        "migrations",
        "node_modules",
        "dist",
        "vendor",
        # 供应商技能树：与 ruff.toml / 风格检查器同口径，不计入本仓代码量
        "skill-creator",
    }
)
CODE_EXT_FRONTEND = (".vue", ".ts", ".js")
TZ = ZoneInfo("Asia/Shanghai")


def _nonblank_lines(path: Path) -> int:
    """Return the number of non-blank physical lines in a text file."""
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return 0
    return sum(1 for line in text.splitlines() if line.strip())


def _walk_code(root: Path, exts: tuple[str, ...]) -> list[Path]:
    """Collect code files under root, skipping caches / migrations / vendor."""
    out: list[Path] = []
    for path in sorted(root.rglob("*")):
        if not path.is_file() or path.suffix not in exts:
            continue
        if EXCLUDE_DIRS & set(path.parts):
            continue
        out.append(path)
    return out


def _ranked(counter: Counter[Any], limit: int | None = None) -> list[tuple[Any, int]]:
    """计数排序：次数降序 → 键升序。

    Counter.most_common() 的并列项按插入序，而插入序来自 set 迭代（受 PYTHONHASHSEED
    影响），跨进程不一致；这里显式排序，保证生成结果可复现。
    """
    items = sorted(counter.items(), key=lambda item: (-item[1], str(item[0])))
    return items[:limit] if limit else items


def _py_counts(files: list[Path]) -> tuple[int, int, int, int]:
    """Return (files, classes, methods, loc) for python files, counting AST nodes."""
    classes = methods = loc = 0
    parsed = 0
    for path in files:
        loc += _nonblank_lines(path)
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        parsed += 1
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes += 1
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                methods += 1
    return len(files), classes, methods, loc


def _git_meta() -> dict[str, Any]:
    """Return {commit, dirty} for the current worktree (best effort)."""

    def _git(*args: str) -> str:
        proc = subprocess.run(
            ["git", *args], cwd=REPO, capture_output=True, text=True, encoding="utf-8"
        )
        return proc.stdout.strip() if proc.returncode == 0 else ""

    status = _git("status", "--porcelain")
    return {"commit": _git("rev-parse", "--short", "HEAD"), "dirty": bool(status)}


def _frontend_raw() -> dict[str, Any]:
    """Run tools/count_frontend.mjs and return its raw payload (modules/shared/edges/routes).

    Raises:
        SystemExit: node 不可用或脚本失败。
    """
    script = PROJECT_VIZ / "tools" / "count_frontend.mjs"
    proc = subprocess.run(
        ["node", str(script), str(REPO)],
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"前端计数失败：{proc.stderr.strip() or proc.stdout.strip()}")
    return json.loads(proc.stdout)


def _frontend_row(row: dict[str, Any], *, shared: bool = False) -> dict[str, Any]:
    """node 输出的一个模块 → 看板行。"""
    out = {
        "name": row["name"],
        "features": row["routes"],
        "files": row["files"],
        "classes": row["classes"],
        "methods": row["functions"],
        "loc": row["loc"],
    }
    if shared:
        out["shared"] = True
    return out


def collect_frontend(raw: dict[str, Any]) -> list[dict[str, Any]]:
    """Return frontend rows: one per module + one shared-layer row."""
    rows = [_frontend_row(row) for row in raw["modules"]]
    rows.extend(_frontend_row(row, shared=True) for row in raw.get("shared", []))
    return rows


def frontend_page(raw: dict[str, Any]) -> dict[str, Any]:
    """前端页数据：模块行 + 路由明细 + 模块间依赖边。"""
    rows = collect_frontend(raw)
    totals = _totals(rows)
    totals["modules"] = len(rows)
    return {
        "modules": rows,
        "edges": raw.get("edges", []),
        "routesByModule": raw.get("routesByModule", {}),
        "totals": totals,
    }


def _endpoint_counts() -> dict[str, int]:
    """Return {app_name: endpoint_count} from utils/gen_arch_stats.py --json."""
    proc = subprocess.run(
        [sys.executable, str(REPO / "utils" / "gen_arch_stats.py"), "--json"],
        cwd=REPO,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    if proc.returncode != 0:
        raise SystemExit(f"gen_arch_stats 失败：{proc.stderr.strip()[:300]}")
    payload = json.loads(proc.stdout)
    return {row["name"]: int(row.get("endpoint_count") or 0) for row in payload["django_apps"]}


def collect_backend() -> list[dict[str, Any]]:
    """Return backend rows: 12 Django apps + one infrastructure row."""
    endpoints = _endpoint_counts()
    apps_dir = REPO / "backend" / "apps"
    rows: list[dict[str, Any]] = []
    for app_dir in sorted(p for p in apps_dir.iterdir() if p.is_dir()):
        if app_dir.name in EXCLUDE_DIRS:
            continue
        files, classes, methods, loc = _py_counts(_walk_code(app_dir, (".py",)))
        rows.append(
            {
                "name": app_dir.name,
                "features": endpoints.get(app_dir.name, 0),
                "files": files,
                "classes": classes,
                "methods": methods,
                "loc": loc,
            }
        )

    infra = [REPO / "backend" / name for name in ("gateway", "config", "models", "shared")]
    infra_files: list[Path] = []
    for path in infra:
        if path.is_dir():
            infra_files.extend(_walk_code(path, (".py",)))
        elif path.is_file():
            infra_files.append(path)
    files, classes, methods, loc = _py_counts(infra_files)
    if files:
        rows.append(
            {
                "name": "基础设施（gateway/config/models/shared）",
                "features": 0,
                "files": files,
                "classes": classes,
                "methods": methods,
                "loc": loc,
                "shared": True,
            }
        )
    return rows


def _file_rows(paths: list[Path]) -> list[dict[str, Any]]:
    """每个 .py 一行：文件名 / 类 / 方法 / 非空行（供「功能模块说明」层用）。"""
    rows: list[dict[str, Any]] = []
    for path in paths:
        _files, classes, methods, loc = _py_counts([path])
        rows.append({"name": path.name, "classes": classes, "methods": methods, "loc": loc})
    rows.sort(key=lambda row: (-int(row["loc"]), row["name"]))
    return rows


def collect_backend_files() -> dict[str, list[dict[str, Any]]]:
    """{app_name: [{name, classes, methods, loc}]}（每个 app 的文件构成）。"""
    apps_dir = REPO / "backend" / "apps"
    out: dict[str, list[dict[str, Any]]] = {}
    for app_dir in sorted(p for p in apps_dir.iterdir() if p.is_dir()):
        if app_dir.name in EXCLUDE_DIRS:
            continue
        out[app_dir.name] = _file_rows(_walk_code(app_dir, (".py",)))
    infra_paths: list[Path] = []
    for name in ("gateway", "config", "models", "shared"):
        path = REPO / "backend" / name
        if path.is_dir():
            infra_paths.extend(_walk_code(path, (".py",)))
        elif path.is_file():
            infra_paths.append(path)
    out["基础设施（gateway/config/models/shared）"] = _file_rows(infra_paths)
    return out


def collect_backend_imports() -> dict[str, Any]:
    """跨 Django App 的 import 关系（App 级汇总）。

    口径：只算 `backend/apps/**` 内部模块之间的 import；同 App 内部依赖单独计数，
    跨 App 出边表 + 模块对 Top 20；`backend.gateway/config/...` 等基础设施不计。
    """
    apps_dir = REPO / "backend" / "apps"
    app_names = {p.name for p in apps_dir.iterdir() if p.is_dir() and p.name not in EXCLUDE_DIRS}
    modules: dict[str, Path] = {}
    for app in sorted(app_names):
        for path in _walk_code(apps_dir / app, (".py",)):
            modules[path.relative_to(REPO).with_suffix("").as_posix().replace("/", ".")] = path

    def app_of(module_name: str) -> str:
        parts = module_name.split(".")
        if (
            len(parts) > 2
            and parts[0] == "backend"
            and parts[1] == "apps"
            and parts[2] in app_names
        ):
            return parts[2]
        return "(其他)"

    def rel_name(module_name: str) -> str:
        parts = module_name.split(".")
        if parts[-1] == "__init__":
            return ".".join(parts[-3:]).replace("backend.apps.", "") + "（包入口）"
        return ".".join(parts[-2:]).replace("backend.apps.", "") + ".py"

    def candidates(src: Path, node: ast.ImportFrom) -> list[str]:
        if node.level:
            base = src.parent
            for _ in range(node.level - 1):
                base = base.parent
            prefix = base.relative_to(REPO).as_posix().replace("/", ".")
            if node.module:
                prefix = prefix + "." + node.module
        else:
            prefix = node.module or ""
        out = [prefix] if prefix else []
        out.extend(prefix + "." + alias.name for alias in node.names if alias.name != "*")
        return out

    cross: Counter[tuple[str, str]] = Counter()
    internal: Counter[str] = Counter()
    pairs: Counter[tuple[str, str]] = Counter()
    for module_name, path in modules.items():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        targets: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                targets.update(candidates(path, node))
            elif isinstance(node, ast.Import):
                targets.update(alias.name for alias in node.names)
        source_app = app_of(module_name)
        for target in sorted(targets):
            resolved = target
            if resolved not in modules:
                candidate = target + ".__init__"
                if candidate in modules:
                    resolved = candidate
                else:
                    continue
            if resolved == module_name:
                continue
            target_app = app_of(resolved)
            if target_app == "(其他)":
                continue
            if target_app == source_app:
                internal[source_app] += 1
                continue
            cross[(source_app, target_app)] += 1
            pairs[(rel_name(module_name), rel_name(resolved))] += 1

    return {
        "edges": [
            {"from": source, "to": target, "count": count}
            for (source, target), count in _ranked(cross)
        ],
        "internal": dict(sorted(internal.items())),
        "pairs": [
            {"from": source, "to": target, "count": count}
            for (source, target), count in _ranked(pairs, 20)
        ],
    }


FRONTEND_SRC = REPO / "frontend" / "src"
TAG_GROUPS = {
    "header": {"WorkbenchHeader", "WorkbenchCrumbs", "PageHeader", "AppHeader"},
    "kpi": {"KpiCard", "StatsAppCard", "MetricCard"},
    "filter": {"FilterTabs", "AppTabs", "el-tabs", "el-radio-group", "el-select", "el-date-picker"},
    "table": {"AppTable", "el-table", "table"},
    "form": {"el-form", "el-form-item", "el-input", "input", "textarea"},
    "dialog": {"el-dialog", "el-drawer", "SidePanel", "Drawer", "StepDrawer"},
    "chart": {"AppChart", "VChart", "ChartPanel", "canvas", "v-chart"},
    "button": {"el-button", "button", "DoodleBtn", "ConfirmButton"},
}
BLOCK_ORDER = ("header", "kpi", "filter", "chart", "table", "form", "button", "dialog")
BLOCK_LABELS = {
    "header": "页头",
    "kpi": "KPI 行",
    "filter": "筛选/标签",
    "chart": "图表区",
    "table": "主体表格",
    "form": "表单",
    "button": "操作按钮",
    "dialog": "抽屉/弹窗",
}
TAG_RE = re.compile(r"<([A-Za-z][\w-]*)")
IMPORT_RE = re.compile(r'^import\s+([A-Z][\w]*)\s+from\s+["\']([^"\']+)["\']', re.M)
# api-client 的本地别名不统一（client / djangoClient / api…）：先解析 import，再按别名抓调用
CLIENT_IMPORT_RE = re.compile(r"""import\s+(\w+)\s+from\s+["']@/shared/api-client["']""")
CALL_RE_TEMPLATE = (
    r"""(?:{names})\.(get|post|put|patch|delete)(?:\s*<[^(]*>)?\(\s*[`'"]([^`'"]+)[`'"]"""
)


def _route_entries(path: Path) -> list[dict[str, str]]:
    """解析 routes.ts：path / name / title / component（只认带 component 的真实路由）。"""
    if not path.is_file():
        return []
    entries: list[dict[str, str]] = []
    current: dict[str, str] | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        match = re.search(r"""path:\s*["']([^"']+)["']""", line)
        if match:
            if current and current.get("component"):
                entries.append(current)
            current = {"path": match.group(1), "name": "", "title": "", "component": ""}
            continue
        if current is None:
            continue
        for key, pattern in (
            ("name", r"""name:\s*["']([^"']+)["']"""),
            ("component", r"""import\(\s*["']([^"']+)["']"""),
            ("title", r"""title:\s*["']([^"']+)["']"""),
        ):
            if current[key]:
                continue
            found = re.search(pattern, line)
            if found:
                current[key] = found.group(1)
    if current and current.get("component"):
        entries.append(current)
    return entries


def _page_blocks(tags: Counter[str]) -> list[str]:
    """按固定顺序把"出现了哪类组件"翻成结构示意块（不猜视觉）。"""
    hit = [key for key in BLOCK_ORDER if any(tag in TAG_GROUPS[key] for tag in tags)]
    return [BLOCK_LABELS[key] for key in hit]


def collect_frontend_pages() -> list[dict[str, Any]]:
    """前端页面构成：每个 .vue 页面的路由 / 组件 / 交互件 / 结构示意。

    口径：页面 = 模块目录下除 components/ 之外的 .vue；组件按模板标签统计；
    「结构示意」是按固定块序推断的**结构**，不是真实界面截图。
    """
    modules_dir = FRONTEND_SRC / "modules"
    out: list[dict[str, Any]] = []
    for module_dir in sorted(p for p in modules_dir.iterdir() if p.is_dir()):
        routes = _route_entries(module_dir / "routes.ts")
        route_by_component = {}
        for route in routes:
            component = route.get("component", "").replace("@/", "")
            route_by_component[component] = route

        pages: list[dict[str, Any]] = []
        for vue in sorted(module_dir.rglob("*.vue")):
            if "components" in vue.relative_to(module_dir).parts:
                continue
            rel = vue.relative_to(FRONTEND_SRC).as_posix()
            text = vue.read_text(encoding="utf-8", errors="replace")
            template = text.split("<template", 1)[-1]
            tags = Counter(TAG_RE.findall(template))
            imports = [
                {"name": name, "from": src}
                for name, src in IMPORT_RE.findall(text)
                if src.startswith("@/shared") or src.startswith("./components")
            ]
            shared = [item["name"] for item in imports if item["from"].startswith("@/shared")]
            locals_ = [item["name"] for item in imports if item["from"].startswith("./components")]
            route = route_by_component.get(rel, {})
            pages.append(
                {
                    "name": vue.name,
                    "path": rel,
                    "loc": sum(1 for line in text.splitlines() if line.strip()),
                    "route": route.get("path", ""),
                    "title": route.get("title", ""),
                    "shared": shared,
                    "locals": locals_,
                    "blocks": _page_blocks(tags),
                    "buttons": tags.get("el-button", 0)
                    + tags.get("button", 0)
                    + tags.get("DoodleBtn", 0),
                    "inputs": tags.get("el-input", 0)
                    + tags.get("input", 0)
                    + tags.get("textarea", 0),
                    "tables": tags.get("AppTable", 0)
                    + tags.get("el-table", 0)
                    + tags.get("table", 0),
                    "dialogs": tags.get("el-dialog", 0)
                    + tags.get("el-drawer", 0)
                    + tags.get("Drawer", 0),
                }
            )

        calls: Counter[tuple[str, str]] = Counter()
        for ts in sorted(module_dir.rglob("*.ts")):
            if "components" in ts.relative_to(module_dir).parts:
                continue
            text = ts.read_text(encoding="utf-8", errors="replace")
            names = CLIENT_IMPORT_RE.findall(text) or ["client"]
            pattern = re.compile(
                CALL_RE_TEMPLATE.format(names="|".join(re.escape(n) for n in names))
            )
            for method, path in pattern.findall(text):
                calls[(method.upper(), path)] += 1
        pages.sort(key=lambda page: (-int(page["loc"]), page["name"]))
        components = [
            vue
            for vue in module_dir.rglob("*.vue")
            if "components" in vue.relative_to(module_dir).parts
        ]
        out.append(
            {
                "name": module_dir.name,
                "pages": pages,
                "components": len(components),
                "calls": [
                    {"method": method, "path": path, "count": count}
                    for (method, path), count in _ranked(calls)
                ],
            }
        )
    return out


def collect_engines() -> list[dict[str, Any]]:
    """Return engine rows: one per first-level subpackage, features from docstrings."""
    sys.path.insert(0, str(REPO))
    from utils.module_docstring import extract_module_docstrings  # noqa: PLC0415 - 延迟导入

    rows: list[dict[str, Any]] = []
    engines_dir = REPO / "engines"
    for pkg in sorted(p for p in engines_dir.iterdir() if p.is_dir()):
        if pkg.name in EXCLUDE_DIRS:
            continue
        files, classes, methods, loc = _py_counts(_walk_code(pkg, (".py",)))
        records = extract_module_docstrings(pkg, repo_root=REPO)
        features = 0
        for record in records:
            intro = record["fields"].get("简介说明") or ""
            features += sum(1 for line in intro.splitlines() if line.strip()[:1].isdigit())
        rows.append(
            {
                "name": pkg.name,
                "features": features,
                "files": files,
                "classes": classes,
                "methods": methods,
                "loc": loc,
                "modules": len(records),
            }
        )
    return rows


# engines/agents 下的目录 → 侧边栏/看板用的中文标签
AGENT_GROUP_LABELS = {
    "tools": "tools · 角色工具",
    "workflow": "workflow · SOP 工作流",
    "models": "models · 模型连接与工厂",
    "rag": "rag · 检索增强",
    "middleware": "middleware · 中间件",
    "messaging": "messaging · 事件与计费",
    "config": "config · 角色与模型配置",
    "realtime_vocie": "realtime_vocie · 语音会话",
    "(根)": "根级模块（装配与入口）",
}


def collect_agents() -> dict[str, Any]:
    """Return the 引擎/agents 模块清单（按目录分组），供「智能体功能模块」视图使用。

    口径：一行 = 一个 .py 模块；功能条目 = 模块 docstring「简介说明」的编号条目数；
    类/方法/代码行 = AST 统计；测试 = docstring「测试」字段的条目数。
    """
    sys.path.insert(0, str(REPO))
    from utils.module_docstring import extract_module_docstrings  # noqa: PLC0415 - 延迟导入

    agents_root = REPO / "engines" / "agents"
    records = extract_module_docstrings(agents_root, repo_root=REPO)
    rows: list[dict[str, Any]] = []
    for record in records:
        fields = record["fields"]
        rel = record["file"]
        rest = rel[len("engines/agents/") :] if rel.startswith("engines/agents/") else rel
        group = rest.split("/")[0] if "/" in rest else "(根)"
        intro = fields.get("简介说明") or ""
        tests = fields.get("测试") or ""
        files, classes, methods, loc = _py_counts([REPO / rel])
        rows.append(
            {
                "name": (REPO / rel).name,
                "path": rel,
                "group": group,
                "type": (fields.get("类型") or "").strip(),
                "summary": (fields.get("模块功能") or "").strip(),
                "entry": (fields.get("Python 调试") or "").strip(),
                "features": sum(1 for line in intro.splitlines() if line.strip()[:1].isdigit()),
                "tests": sum(1 for line in tests.splitlines() if line.strip()[:1].isdigit()),
                "classes": classes,
                "methods": methods,
                "loc": loc,
            }
        )

    rows.sort(key=lambda row: (-int(row["loc"]), row["name"]))
    groups: list[dict[str, Any]] = []
    for key in sorted({row["group"] for row in rows}):
        items = [row for row in rows if row["group"] == key]
        totals = _totals(items)
        totals["modules"] = len(items)
        totals["tests"] = sum(int(row["tests"]) for row in items)
        groups.append(
            {
                "key": key,
                "label": AGENT_GROUP_LABELS.get(key, key),
                "modules": items,
                "totals": totals,
            }
        )
    groups.sort(key=lambda group: (group["key"] == "(根)", -int(group["totals"]["loc"])))
    totals = _totals(rows)
    totals["modules"] = len(rows)
    totals["tests"] = sum(int(row["tests"]) for row in rows)
    return {"groups": groups, "totals": totals, "imports": collect_agent_imports(rows)}


def collect_agent_imports(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """统计 engines/agents 内部的 import 关系（模块级 → 目录级汇总）。

    口径：只算 `engines/agents/**` 内部模块之间的 import（绝对导入 + 相对导入都解析），
    同目录的内部依赖单独计数，跨目录依赖出边表；外部依赖（agentscope 等）不计。
    """
    root = REPO / "engines" / "agents"
    modules: dict[str, Path] = {}
    for path in _walk_code(root, (".py",)):
        modules[path.relative_to(REPO).with_suffix("").as_posix().replace("/", ".")] = path
    # 真实存在的子目录（用于判"目录"）：包级导入（如 from engines.agents.models import x）
    # 的目标是 "engines.agents.models"，没有第二个点——旧实现会把它误判成根级模块。
    group_dirs = {p.name for p in root.iterdir() if p.is_dir() and p.name not in EXCLUDE_DIRS}

    def dir_of(module_name: str) -> str:
        rest = (
            module_name[len("engines.agents.") :]
            if module_name.startswith("engines.agents.")
            else module_name
        )
        head = rest.split(".", 1)[0]
        return head if head in group_dirs else "(根)"

    def candidates(src: Path, node: ast.ImportFrom) -> list[str]:
        if node.level:
            base = src.parent
            for _ in range(node.level - 1):
                base = base.parent
            prefix = base.relative_to(REPO).as_posix().replace("/", ".")
            if node.module:
                prefix = prefix + "." + node.module
        else:
            prefix = node.module or ""
        out = [prefix] if prefix else []
        out.extend(prefix + "." + alias.name for alias in node.names if alias.name != "*")
        return out

    cross: Counter[tuple[str, str]] = Counter()
    internal: Counter[str] = Counter()
    pairs: Counter[tuple[str, str]] = Counter()

    def rel_name(module_name: str) -> str:
        """engines.agents.a.b → a/b.py（包入口显示为 a（包））。"""
        rest = (
            module_name[len("engines.agents.") :]
            if module_name.startswith("engines.agents.")
            else module_name
        )
        parts = rest.split(".")
        if parts[-1] == "__init__":
            return ".".join(parts[:-1]) + "（包入口）"
        return "/".join(parts) + ".py"

    for module_name, path in modules.items():
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeDecodeError):
            continue
        targets: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                targets.update(candidates(path, node))
            elif isinstance(node, ast.Import):
                targets.update(alias.name for alias in node.names)
        for target in sorted(targets):
            # 包级导入的目标是 "...models" 而不是 "...models.__init__"：补一次解析
            resolved = target
            if resolved not in modules:
                candidate = target + ".__init__"
                if candidate in modules:
                    resolved = candidate
                else:
                    continue
            if resolved == module_name:
                continue
            source_dir = dir_of(module_name)
            target_dir = dir_of(resolved)
            if source_dir == target_dir:
                internal[source_dir] += 1
                continue
            cross[(source_dir, target_dir)] += 1
            pairs[(rel_name(module_name), rel_name(resolved))] += 1

    return {
        "edges": [
            {"from": source, "to": target, "count": count}
            for (source, target), count in _ranked(cross)
        ],
        "internal": dict(sorted(internal.items())),
        "pairs": [
            {"from": source, "to": target, "count": count}
            for (source, target), count in _ranked(pairs, 20)
        ],
    }


def _totals(rows: list[dict[str, Any]]) -> dict[str, int]:
    """Sum the metric columns of rows."""
    keys = ("features", "files", "classes", "methods", "loc")
    return {key: sum(int(row.get(key) or 0) for row in rows) for key in keys}


DOMAINS_PATH = PROJECT_VIZ / "tools" / "domains.json"
DOCSTRING_SKILL = REPO / ".agents" / "skills" / "engines-docstring-check"
# 健康分权重：改这里 → 页面脚注自动跟着变（唯一真相源）
HEALTH_WEIGHTS = {"docs": 40, "tests": 30, "coupling": 20, "size": 10}
SIZE_LIMIT = 400
HUB_IN_DEGREE = 5
# 扣分口径（每项扣多少分，直接写死在常量里，页面脚注展示）：
# 文档/测试按比例；耦合 = 双向引用 4 分/组 + 枢纽 3 分/个；体量 = 4 分/个超限文件
BIDIR_PENALTY = 4
HUB_PENALTY = 3
SIZE_PENALTY = 4


def _load_domains() -> list[dict[str, Any]]:
    """读人工维护的业务域对照表（tools/domains.json）。"""
    raw = json.loads(DOMAINS_PATH.read_text(encoding="utf-8"))
    return list(raw.get("domains") or [])


def _docstring_health() -> dict[str, Any]:
    """跑 engines-docstring-check 拿文档问题面（复用技能里的检查器）。"""
    proc = subprocess.run(
        [sys.executable, "-m", "scripts.docstrings", "check", "--all", "--format", "json"],
        cwd=DOCSTRING_SKILL,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    try:
        payload = json.loads(proc.stdout)
    except json.JSONDecodeError:
        return {"available": False, "scanned": 0, "files_with_issues": 0, "error_count": 0}
    paths = {
        item.get("path")
        for item in payload.get("violations") or []
        if item.get("severity") == "error"
    }
    return {
        "available": True,
        "scanned": int(payload.get("files_scanned") or 0),
        "files_with_issues": len(paths),
        "error_count": int(payload.get("error_count") or 0),
    }


def _tests_corpus() -> str:
    """把所有测试文件拼成一份文本，用于"模块有没有被测试文件提到"的粗略匹配。"""
    chunks: list[str] = []
    for path in sorted((REPO / "tests").rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        try:
            chunks.append(path.read_text(encoding="utf-8", errors="replace"))
        except OSError:
            continue
    return "\n".join(chunks)


def _health(payload: dict[str, Any]) -> dict[str, Any]:
    """四项健康分（文档 / 测试 / 耦合 / 体量），全部可核对；不足的数据标 unavailable。"""
    docs = _docstring_health()
    agents_groups = payload["agents"]["groups"]
    modules = [module for group in agents_groups for module in group["modules"]]
    corpus = _tests_corpus()

    with_test = 0
    for module in modules:
        stem = module["name"][:-3] if module["name"].endswith(".py") else module["name"]
        path = module["path"]
        if stem in corpus or path in corpus:
            with_test += 1

    imports = payload["agents"]["imports"]
    edges = imports.get("edges") or []
    inbound: Counter[str] = Counter()
    for edge in edges:
        inbound[edge["to"]] += int(edge["count"] or 0)
    pairs = {(edge["from"], edge["to"]) for edge in edges}
    bidirectional = {tuple(sorted(pair)) for pair in pairs if (pair[1], pair[0]) in pairs}
    hubs = [node for node, count in inbound.items() if count >= HUB_IN_DEGREE]

    engine_files = _walk_code(REPO / "engines", (".py",))
    oversized = sum(1 for path in engine_files if _nonblank_lines(path) > SIZE_LIMIT)

    def clamp(value: float) -> float:
        return max(0.0, min(100.0, value))

    parts = [
        {
            "key": "docs",
            "label": "文档",
            "weight": HEALTH_WEIGHTS["docs"],
            "score": clamp(
                100.0 * (1 - docs["files_with_issues"] / docs["scanned"])
                if docs["scanned"]
                else 0.0
            ),
            "detail": (
                f"{docs['error_count']} 条 docstring error，涉及 {docs['files_with_issues']}/"
                f"{docs['scanned']} 个引擎文件"
            ),
        },
        {
            "key": "tests",
            "label": "测试",
            "weight": HEALTH_WEIGHTS["tests"],
            "score": 100.0 * with_test / len(modules) if modules else 0,
            "detail": f"{with_test}/{len(modules)} 个 agents 模块在 tests/ 里被提到（按名字匹配，可能低估）",
        },
        {
            "key": "coupling",
            "label": "耦合",
            "weight": HEALTH_WEIGHTS["coupling"],
            "score": clamp(100.0 - BIDIR_PENALTY * len(bidirectional) - HUB_PENALTY * len(hubs)),
            "detail": f"目录级双向引用 {len(bidirectional)} 组，入度 ≥{HUB_IN_DEGREE} 的枢纽 {len(hubs)} 个",
        },
        {
            "key": "size",
            "label": "体量",
            "weight": HEALTH_WEIGHTS["size"],
            "score": clamp(100.0 - SIZE_PENALTY * oversized),
            "detail": f"引擎里超过 {SIZE_LIMIT} 行的文件 {oversized} 个（共 {len(engine_files)} 个）",
        },
    ]
    for part in parts:
        part["deduction"] = round(part["weight"] * (1 - part["score"] / 100), 1)
        part["score"] = round(part["score"], 1)
    total = round(sum(part["weight"] * part["score"] / 100 for part in parts), 1)
    return {
        "score": total,
        "target": 85,
        "weights": dict(HEALTH_WEIGHTS),
        "scope": "engines/**（前端/后端暂不参与：没有 docstring 与测试字段可对齐）",
        "parts": parts,
        "docs": docs,
    }


def _overview(payload: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    """总览页数据：领域矩阵 + 健康分 + 北向 KPI + 快照变化。"""
    fe_by_name = {row["name"]: row for row in payload["frontend"]["modules"]}
    be_by_name = {row["name"]: row for row in payload["backend"]["apps"]}
    agents_groups = {group["key"]: group for group in payload["agents"]["groups"]}
    engines_by_name = {row["name"]: row for row in payload["categories"][2]["modules"]}

    domains: list[dict[str, Any]] = []
    for item in _load_domains():
        fe_rows = [fe_by_name[name] for name in item.get("fe", []) if name in fe_by_name]
        be_rows = [be_by_name[name] for name in item.get("be", []) if name in be_by_name]
        engine_loc = engine_modules = 0
        engine_dirs: list[str] = []
        for path in item.get("engine", []):
            if path.startswith("agents/"):
                group = agents_groups.get(path.split("/", 1)[1])
                if group:
                    engine_loc += int(group["totals"].get("loc") or 0)
                    engine_modules += int(group["totals"].get("modules") or 0)
                    engine_dirs.append(path)
            elif path in engines_by_name:
                engine_loc += int(engines_by_name[path].get("loc") or 0)
                engine_modules += int(engines_by_name[path].get("files") or 0)
                engine_dirs.append(path)
        domains.append(
            {
                "key": item["key"],
                "label": item["label"],
                "coverage": item.get("coverage", "none"),
                "note": item.get("note", ""),
                "fe": {
                    "count": len(fe_rows),
                    "routes": sum(int(row.get("features") or 0) for row in fe_rows),
                    "loc": sum(int(row.get("loc") or 0) for row in fe_rows),
                },
                "be": {
                    "count": len(be_rows),
                    "endpoints": sum(int(row.get("features") or 0) for row in be_rows),
                    "loc": sum(int(row.get("loc") or 0) for row in be_rows),
                },
                "engine": {
                    "dirs": engine_dirs,
                    "modules": engine_modules,
                    "loc": engine_loc,
                },
            }
        )

    tiers: Counter[str] = Counter(domain["coverage"] for domain in domains)
    health = _health(payload)

    # 快照变化：取最近两个"含分层数据"的历史点
    full = [row for row in history if "frontend" in row and "engine" in row]
    delta: list[dict[str, Any]] = []
    if len(full) >= 2:
        previous, current = full[-2], full[-1]
        for key, label in (
            ("frontend", "前端"),
            ("backend", "后端"),
            ("engine", "引擎"),
            ("agents", "智能体"),
        ):
            before = previous.get(key) or {}
            after = current.get(key) or {}
            before_loc = int(before.get("loc") or 0)
            after_loc = int(after.get("loc") or 0)
            if not before_loc:
                continue
            delta.append(
                {
                    "key": key,
                    "label": label,
                    "from": before_loc,
                    "to": after_loc,
                    "diff": after_loc - before_loc,
                    "pct": round((after_loc / before_loc - 1) * 100, 1),
                    "at": previous.get("at", ""),
                    "modules_from": int(before.get("modules") or 0),
                    "modules_to": int(after.get("modules") or 0),
                }
            )

    aligned = tiers.get("direct", 0) + tiers.get("via", 0)
    capability = int(payload["agents"]["totals"].get("features") or 0)
    role_count = sum(
        1
        for path in _walk_code(REPO / "engines" / "agents", (".py",))
        if path.name.startswith("role_")
    )
    total_delta = sum(item["diff"] for item in delta)

    return {
        "kpis": [
            {
                "key": "alignment",
                "label": "领域打通率",
                "value": f"{aligned}/{len(domains)}",
                "pct": round(100 * aligned / len(domains), 0) if domains else 0,
                "target": "100%",
                "sub": f"直连 {tiers.get('direct', 0)} · 间接 {tiers.get('via', 0)} · 无 {tiers.get('none', 0)}",
            },
            {
                "key": "capability",
                "label": "引擎能力条目",
                "value": str(capability),
                "pct": None,
                "target": "随需求增长",
                "sub": (
                    f"{len(payload['agents']['groups'])} 个目录 · "
                    f"{sum(len(g['modules']) for g in payload['agents']['groups'])} 个模块 · "
                    f"{payload['agents']['totals'].get('tests', 0)} 条测试条目"
                ),
            },
            {
                "key": "health",
                "label": "引擎健康分",
                "value": str(health["score"]),
                "pct": health["score"],
                "target": f"≥ {health['target']}",
                "sub": "文档 / 测试 / 耦合 / 体量 四项加权",
            },
            {
                "key": "churn",
                "label": "最近一次快照净增",
                "value": f"{total_delta:+d} 行",
                "pct": None,
                "target": "看方向，不看绝对量",
                "sub": (delta[0]["at"] if delta else "快照不足 2 个基线"),
            },
        ],
        "domains": domains,
        "tiers": {key: tiers.get(key, 0) for key in ("direct", "via", "none")},
        "health": health,
        "delta": delta,
        "roles": role_count,
    }


def build() -> dict[str, Any]:
    """Assemble the whole board payload."""
    frontend_raw = _frontend_raw()
    backend_rows = collect_backend()
    backend_files = collect_backend_files()
    categories = [
        ("frontend", "前端", collect_frontend(frontend_raw)),
        ("backend", "后端", backend_rows),
        ("engine", "引擎", collect_engines()),
    ]
    payload: dict[str, Any] = {
        "generated_at": datetime.now(TZ).strftime("%Y-%m-%d %H:%M"),
        "git": _git_meta(),
        "notes": {
            "features": {
                "frontend": "前端 = routes.ts 注册的路由条目数",
                "backend": "后端 = DRF API 端点数（utils/gen_arch_stats.py）",
                "engine": "引擎 = 模块 docstring「简介说明」声明的能力条目数",
                "caveat": "三层口径不同，只做各自量级对照，不可横向相加比较",
            },
            "methods": "命名函数 / 方法定义数（不含 lambda、匿名回调）",
            "loc": "非空物理行（前端含 template/style）",
            "files": "代码文件数；排除 __pycache__、migrations、vendor、skill-creator",
            "scope": "后端含基础设施行；前端含共享层行；引擎按一级子包汇总",
        },
        "categories": [],
        "grand_totals": {},
        "agents": {},
        "frontend": {},
        "backend": {},
    }
    for key, label, rows in categories:
        rows.sort(key=lambda row: (-row["loc"], row["name"]))
        payload["categories"].append(
            {"key": key, "label": label, "modules": rows, "totals": _totals(rows)}
        )
    payload["grand_totals"] = _totals(
        [row for category in payload["categories"] for row in category["modules"]]
    )
    payload["agents"] = collect_agents()
    payload["frontend"] = frontend_page(frontend_raw)
    payload["frontend"]["pages"] = collect_frontend_pages()

    backend_apps = []
    for row in backend_rows:
        backend_apps.append({**row, "files": backend_files.get(row["name"], [])})
    backend_totals = _totals(backend_rows)
    backend_totals["modules"] = len(backend_rows)
    payload["backend"] = {
        "apps": backend_apps,
        "edges": {},
        "totals": backend_totals,
    }
    payload["backend"].update(collect_backend_imports())
    return payload


def _canonical(payload: dict[str, Any]) -> str:
    """Return a stable text of the *numbers* in payload (drops volatile fields).

    ``generated_at`` 与 ``git`` 每次生成都会变；它们只用于页面标注"快照时间"，
    不应该让 --check 永远报"过期"。
    """
    stable = {key: value for key, value in payload.items() if key not in {"generated_at", "git"}}
    return json.dumps(stable, ensure_ascii=False, sort_keys=True)


HISTORY_PATH = DATA_DIR / "history.json"
HISTORY_LIMIT = 60
HISTORY_KEYS = ("modules", "features", "files", "classes", "methods", "loc")
CATEGORY_KEYS = ("frontend", "backend", "engine", "agents")


def _read_history() -> list[dict[str, Any]]:
    """Read the append-only history file (list of snapshots); tolerate junk and legacy rows."""
    if not HISTORY_PATH.is_file():
        return []
    try:
        rows = json.loads(HISTORY_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []
    if not isinstance(rows, list):
        return []
    # 旧格式是平铺的 agents 指标（{at, modules, features, ...}）：迁移成 {at, agents: {...}}
    out: list[dict[str, Any]] = []
    for row in rows:
        if isinstance(row, dict) and "agents" not in row and "modules" in row:
            out.append(
                {"at": row.get("at", ""), "agents": {k: int(row.get(k) or 0) for k in HISTORY_KEYS}}
            )
        elif isinstance(row, dict):
            out.append(row)
    return out


def _history_snapshot(payload: dict[str, Any]) -> dict[str, Any]:
    """One history entry: 四个分层各自的模块量与代码量。"""
    snapshot: dict[str, Any] = {"at": datetime.now(TZ).strftime("%Y-%m-%d %H:%M")}
    for category in payload["categories"]:
        totals = category["totals"]
        row = {key: int(totals.get(key) or 0) for key in HISTORY_KEYS}
        row["modules"] = len(category["modules"])  # 分类下的模块/App 个数
        snapshot[category["key"]] = row
    agents_totals = payload["agents"]["totals"]
    snapshot["agents"] = {key: int(agents_totals.get(key) or 0) for key in (*HISTORY_KEYS, "tests")}
    return snapshot


def _append_history(payload: dict[str, Any]) -> list[dict[str, Any]]:
    """Append the current snapshot when any category changed; keep the last N entries.

    Args:
        payload: build() 的结果。

    Returns:
        追加后的完整历史（按时间升序）。
    """
    rows = _read_history()
    snapshot = _history_snapshot(payload)
    changed = True
    if rows:
        last = rows[-1]
        changed = any(
            {k: v for k, v in last.get(cat, {}).items() if k != "at"}
            != {k: v for k, v in snapshot.get(cat, {}).items() if k != "at"}
            for cat in CATEGORY_KEYS
        )
    if changed:
        rows.append(snapshot)
    return rows[-HISTORY_LIMIT:]


def write_outputs(payload: dict[str, Any], *, check_only: bool) -> int:
    """Write data/board.json + data/board.js, or compare with existing files.

    Args:
        payload: build() 的结果。
        check_only: True 时只比较数字口径、不写盘（忽略 generated_at / git 的漂移）。

    Returns:
        进程退出码（check 模式下有差异返回 1）。
    """
    json_path = DATA_DIR / "board.json"
    js_path = DATA_DIR / "board.js"

    # 总览页的数据依赖历史快照：check 模式只读、write 模式追加（保证写出的文件与历史自洽）
    history = _read_history() if check_only else _append_history(payload)
    payload["overview"] = _overview(payload, history)
    js_text = (
        "/* 由 dev_docs/project-viz/tools/gen_board_data.py 生成，勿手改。 */\n"
        "window.__BOARD__ = "
        + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        + ";\n"
    )

    if check_only:
        stale: list[str] = []
        existing: dict[str, Any] | None = None
        if json_path.is_file():
            try:
                existing = json.loads(json_path.read_text(encoding="utf-8"))
            except json.JSONDecodeError:
                existing = None
        if existing is None or _canonical(existing) != _canonical(payload):
            stale.append("board.json")
        if not js_path.is_file():
            stale.append("board.js")
        if stale:
            print(f"数据已过期：{', '.join(stale)}（重跑 gen_board_data.py）")  # noqa: T201
            return 1
        print("数据最新（忽略 generated_at / git 快照时间）")  # noqa: T201
        return 0

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    js_path.write_text(js_text, encoding="utf-8")

    # 历史趋势：上面已追加过，这里落盘（单独成文件，避免把 --check 变成"永远过期"）
    HISTORY_PATH.write_text(
        json.dumps(history, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (DATA_DIR / "history.js").write_text(
        "/* 由 dev_docs/project-viz/tools/gen_board_data.py 生成，勿手改。 */\n"
        "window.__HISTORY__ = "
        + json.dumps(history, ensure_ascii=False, separators=(",", ":"))
        + ";\n",
        encoding="utf-8",
    )

    totals = payload["grand_totals"]
    print(  # noqa: T201
        f"已写出 {json_path.name}, {js_path.name}, history.js："
        f"{len(payload['categories'])} 类 / 模块 {sum(len(c['modules']) for c in payload['categories'])} 个 / "
        f"功能 {totals['features']} · 文件 {totals['files']} · 类 {totals['classes']} · "
        f"方法 {totals['methods']} · 代码行 {totals['loc']} · 历史 {len(history)} 次"
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """CLI entry point."""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="生成项目看板数据（data/board.json + board.js）")
    parser.add_argument("--check", action="store_true", help="只比较现有数据是否过期，不写盘")
    args = parser.parse_args(argv)
    return write_outputs(build(), check_only=args.check)


if __name__ == "__main__":
    raise SystemExit(main())
