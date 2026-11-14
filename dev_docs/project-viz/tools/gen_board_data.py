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


def build() -> dict[str, Any]:
    """Assemble the whole board payload."""
    frontend_raw = _frontend_raw()
    backend_rows = collect_backend()
    backend_files = collect_backend_files()
    payload: dict[str, Any] = {
        "generated_at": datetime.now(TZ).strftime("%Y-%m-%d %H:%M"),
        "git": _git_meta(),
        "agents": {},
        "frontend": {},
        "backend": {},
    }
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
    payload["ae_harness"] = collect_ae_harness()
    payload["engineModules"] = collect_engine_modules()
    payload["backendModules"] = collect_backend_modules()
    payload["frontendModules"] = collect_frontend_modules(payload["frontend"])
    payload["projectModules"] = collect_project_modules(payload["frontend"])
    return payload


# 模块 = ae_harness 根目录下的五个文件夹（顺序按需求：agent / tools / assistant / workflow / event）
AE_HARNESS_GROUPS = (
    ("agents", "创建智能体", "创建智能体：模型配置 + 提示词 + create_agent"),
    ("tools", "智能体工具箱", "智能体工具箱：给 Agent 提供工具（adb 设备动作）"),
    ("assistant", "智能体助手", "智能体助手：Agent + tools 合成一个可运行角色"),
    ("workflow", "工作流", "工作流：多个 Agent 组合成一条 SOP"),
    ("event", "智能体事件", "智能体事件：可视化 assistant 与 workflow 的执行过程"),
    ("middleware", "观测中间件", "观测中间件：只读 hook，采集事件流看不到的信息（system prompt / 上下文压缩）"),
)

# 跨组引用「为什么被调用」：import 只能证明引用了，因果得人写；key = "引用方->被引用方"
AE_HARNESS_WHY = {
    "assistant->agents": "入口要跑一轮角色，必须先经 create_agent 拿到 AgentBundle（Agent 实例 + 密钥名），工具挂载与 reply 都要用它。",
    "assistant->tools": "工具不属于角色三要素，create_agent 不接收；入口建好 Agent 后，自己把 adb 工具 add_tool 挂上去（验收侧只挂只读集）。",
    "assistant->event": "一轮执行的过程要落成结构化记录并出 HTML 报告，报告统一走 event/ 的记录器与渲染器，入口不自己拼页面。",
    "workflow->agents": "SOP 每一步都要一对执行者与验收者，必须先经 create_agent 造出两个角色再交给 run_sop。",
    "workflow->assistant": "编排入口复用 assistant/_bootstrap 的运行时骨架（编码、日志级别、汇总、异常包装），不重复实现一套。",
    "workflow->event": "每步的执行与验收事件都要记下来并出报告，记录与渲染都用 event/，workflow 不碰 HTML。",
    "workflow->tools": "执行者要写操作工具、验收者只要只读工具，两套工具集在编排入口装配后传给角色。",
    "assistant->middleware": "入口创建角色时可注入只读观测中间件，采样本轮最终 system prompt 与上下文压缩决策；中间件不改行为、不落盘。",
    "workflow->middleware": "SOP 里两个角色共用同一个观测实例，记录带 agent 名区分归属；同样只读，不参与编排。",
}


def collect_frontend_modules(frontend: dict[str, Any]) -> dict[str, Any]:
    """frontend/src/modules 下每个业务模块按「一层」统计。

    口径：
    1. 模块 = frontend/src/modules/ 下的一个业务目录（共享层 shared/views/router 不计）。
    2. 单元 = 模块下的直接子目录（递归汇总 .vue/.ts/.js，整体算一个）或直接文件（各算一个）；
       样式 .css 与 AGENTS.md 不计入。
    3. 依赖 = 业务模块之间的 import，复用 count_frontend.mjs 的 edges，过滤掉指向共享层的边。
    """
    base = REPO / "frontend" / "src" / "modules"
    code_ext = {".vue", ".ts", ".js"}

    def count_loc(files: list[Path]) -> int:
        total = 0
        for path in files:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            total += sum(1 for line in text.splitlines() if line.strip())
        return total

    names = [
        module.get("name")
        for module in frontend.get("modules", [])
        if module.get("name") and not str(module.get("name")).startswith("共享层")
    ]

    modules: list[dict[str, Any]] = []
    for name in names:
        folder = base / name
        if not folder.is_dir():
            continue
        units: list[dict[str, Any]] = []
        for item in sorted(folder.iterdir()):
            if item.name == "AGENTS.md":
                continue
            if item.is_dir():
                files = [f for f in sorted(item.rglob("*")) if f.is_file() and f.suffix in code_ext]
                if not files:
                    continue
                units.append(
                    {"name": item.name + "/", "kind": "dir", "files": len(files), "loc": count_loc(files)}
                )
            elif item.suffix in code_ext:
                units.append({"name": item.name, "kind": "file", "files": 1, "loc": count_loc([item])})
        units.sort(key=lambda unit: (-int(unit["loc"]), unit["name"]))
        modules.append(
            {
                "key": name,
                # 前端模块没有中文名，label 留空，卡片上就只显示目录名
                "label": "",
                "units": units,
                "totals": {
                    "units": len(units),
                    "files": sum(int(unit["files"]) for unit in units),
                    "loc": sum(int(unit["loc"]) for unit in units),
                },
            }
        )

    business = {module["key"] for module in modules}
    relations = []
    for edge in frontend.get("edges", []):
        source = edge.get("from")
        target = edge.get("to")
        if source not in business:
            continue
        relations.append(
            {
                "from": source,
                "to": target,
                "count": int(edge["count"]),
                "shared": target not in business,
            }
        )
    relations.sort(key=lambda row: (-row["count"], row["from"], row["to"]))
    return {
        "modules": modules,
        "relations": relations,
        "totals": {
            "modules": len(modules),
            "units": sum(int(module["totals"]["units"]) for module in modules),
            "files": sum(int(module["totals"]["files"]) for module in modules),
            "loc": sum(int(module["totals"]["loc"]) for module in modules),
        },
    }


PROJECT_MODULES = (
    ("backend", "后端"),
    ("engines", "引擎"),
    ("frontend", "前端"),
    ("tests", "测试"),
    ("utils", "公共工具"),
)

# 总览页排除的目录：缓存、临时、第三方资产、文档与本看板自身
PROJECT_SKIP_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
    "temps",
    ".pytest_cache",
    ".pytest-tmp",
    ".testtmp",
    ".ruff_cache",
    ".mypy_cache",
    ".cache",
    "pytest-of-zhiyan",
    "logs",
    "vendor",
    "platform-tools",
}
# 前端接口前缀 → 后端 app（人工对照 backend/apps/*/urls.py，前缀不是自动推出来的）
HTTP_API_APPS = {
    "/cases": "case_manager",
    "/workflow": "workflow",
    "/tasks": "task_list",
    "/devices": "device_pool",
    "/ai": "ai_assistant",
    "/bugs": "bug_manager",
    "/serial-log": "serial_log",
    "/dashboard": "dashboard",
    "/reports": "report_generator",
    "/knowledge-assistant": "knowledge_assistant",
}

PROJECT_CODE_EXT = {".py", ".ts", ".tsx", ".vue", ".js", ".mjs", ".css", ".html"}
PROJECT_SKIP_FILES = {"__init__.py"}


def collect_project_modules(frontend: dict[str, Any] | None = None) -> dict[str, Any]:
    """总览页：仓库一级目录 × 每个目录的第一层单元。

    口径：
    1. 模块 = 仓库根下的工程目录（backend / engines / frontend / tests / utils）。
       缓存、临时时间戳目录、第三方 skill 资产（.agents）、文档（dev_docs，含本看板自身）
       与运行数据（data）不计入。
    2. 单元 = 模块下的直接子目录（递归汇总代码文件，整体算一个）或直接代码文件（各算一个）。
    3. 依赖 = 目录之间的 Python import 次数；另外补一条 frontend → backend 的
       **HTTP 调用**（前端是 TS/Vue，不产生 Python import，但它确实在调后端接口，
       不补这条边图上就会有一个孤立节点）。
    """
    root = REPO

    def count_loc(files: list[Path]) -> int:
        total = 0
        for path in files:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            total += sum(1 for line in text.splitlines() if line.strip())
        return total

    def code_files(folder: Path) -> list[Path]:
        return [
            f
            for f in sorted(folder.rglob("*"))
            if f.is_file()
            and f.suffix in PROJECT_CODE_EXT
            and "__pycache__" not in f.parts
            and not any(part in PROJECT_SKIP_DIRS for part in f.parts)
        ]

    modules: list[dict[str, Any]] = []
    module_of_path: dict[str, str] = {}

    for key, label in PROJECT_MODULES:
        base = root / key
        if not base.is_dir():
            continue
        units: list[dict[str, Any]] = []
        owned: list[Path] = []
        for item in sorted(base.iterdir()):
            if item.name in PROJECT_SKIP_DIRS or item.name in PROJECT_SKIP_FILES:
                continue
            if item.is_dir():
                files = code_files(item)
                if not files:
                    continue
                units.append(
                    {"name": item.name + "/", "kind": "dir", "files": len(files), "loc": count_loc(files)}
                )
                owned.extend(files)
            elif item.suffix in PROJECT_CODE_EXT:
                units.append({"name": item.name, "kind": "file", "files": 1, "loc": count_loc([item])})
                owned.append(item)
        units.sort(key=lambda unit: (-int(unit["loc"]), unit["name"]))
        for path in owned:
            module_of_path[path.as_posix()] = key
        modules.append(
            {
                "key": key,
                "label": label,
                "units": units,
                "totals": {
                    "units": len(units),
                    "files": sum(int(unit["files"]) for unit in units),
                    "loc": sum(int(unit["loc"]) for unit in units),
                },
            }
        )

    known = {key for key, _ in PROJECT_MODULES}
    cross: dict[tuple[str, str], int] = {}
    for path_text, source in module_of_path.items():
        if not path_text.endswith(".py"):
            continue
        try:
            tree = ast.parse(Path(path_text).read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError):
            continue
        targets: set[str] = set()
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module]
            for name in names:
                head = name.split(".")[0]
                if head in known and head != source:
                    targets.add(head)
        for target in targets:
            cross[(source, target)] = cross.get((source, target), 0) + 1

    relations = [
        {"from": source, "to": target, "count": count, "kind": "import"}
        for (source, target), count in sorted(cross.items(), key=lambda item: (-item[1], item[0]))
    ]

    # 前端调后端的 HTTP 次数（数据来自 count_frontend.mjs 采集的 api-client 调用）
    http_calls = 0
    http_paths: set[str] = set()
    http_by_app: dict[str, dict[str, Any]] = {}
    for page in (frontend or {}).get("pages", []):
        for call in page.get("calls", []):
            count = int(call.get("count") or 0)
            path = str(call.get("path") or "")
            http_calls += count
            http_paths.add(path)
            prefix = "/" + path.strip("/").split("/")[0]
            app = HTTP_API_APPS.get(prefix, "（未映射）")
            bucket = http_by_app.setdefault(
                app, {"app": app, "prefix": prefix, "calls": 0, "paths": set()}
            )
            bucket["calls"] += count
            bucket["paths"].add(path)
    if http_calls and any(module["key"] == "frontend" for module in modules):
        relations.append(
            {"from": "frontend", "to": "backend", "count": http_calls, "kind": "http"}
        )
        relations.sort(key=lambda row: (-int(row["count"]), str(row["from"])))

    http_by_app_rows = [
        {
            "app": bucket["app"],
            "prefix": bucket["prefix"],
            "calls": bucket["calls"],
            "paths": len(bucket["paths"]),
        }
        for bucket in sorted(http_by_app.values(), key=lambda item: (-item["calls"], item["app"]))
    ]

    return {
        "modules": modules,
        "relations": relations,
        "http": {"calls": http_calls, "paths": len(http_paths), "byApp": http_by_app_rows},
        "totals": {
            "modules": len(modules),
            "units": sum(int(module["totals"]["units"]) for module in modules),
            "files": sum(int(module["totals"]["files"]) for module in modules),
            "loc": sum(int(module["totals"]["loc"]) for module in modules),
        },
    }


BACKEND_MODULES = (
    ("accounts", "账号与权限"),
    ("ai_assistant", "AI 助手"),
    ("bug_manager", "缺陷管理"),
    ("case_manager", "用例管理"),
    ("dashboard", "看板聚合"),
    ("device_pool", "设备池"),
    ("knowledge_assistant", "知识问答"),
    ("report_generator", "报告生成"),
    ("serial_log", "串口日志"),
    ("task_list", "任务清单"),
    ("usage_ledger", "用量记账"),
    ("workflow", "工作流"),
)


def collect_backend_modules() -> dict[str, Any]:
    """backend/apps 下每个 Django app 按「一层」统计（口径同 engines 页）。

    口径：
    1. 模块 = backend/apps/ 下的一个 app。
    2. 单元 = app 下的直接子目录（递归汇总，整体算一个）或直接 .py（各算一个）。
    3. 排除 __init__.py、__pycache__、migrations/。
    4. import 只算 app 之间，config/gateway/shared 属于基础设施，不计入跨模块关系。
    """
    root = REPO / "backend" / "apps"
    skip_dirs = {"__pycache__", "migrations"}

    def count_loc(files: list[Path]) -> int:
        total = 0
        for path in files:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            total += sum(1 for line in text.splitlines() if line.strip())
        return total

    modules: list[dict[str, Any]] = []
    module_of_path: dict[str, str] = {}

    for key, label in BACKEND_MODULES:
        base = root / key
        if not base.is_dir():
            continue
        units: list[dict[str, Any]] = []
        owned: list[Path] = []
        for item in sorted(base.iterdir()):
            if item.name == "__init__.py" or item.name in skip_dirs:
                continue
            if item.is_dir():
                files = [
                    f
                    for f in sorted(item.rglob("*.py"))
                    if "__pycache__" not in f.parts and f.name != "__init__.py"
                ]
                if not files:
                    continue
                units.append(
                    {"name": item.name + "/", "kind": "dir", "files": len(files), "loc": count_loc(files)}
                )
                owned.extend(files)
            elif item.suffix == ".py":
                units.append({"name": item.name, "kind": "file", "files": 1, "loc": count_loc([item])})
                owned.append(item)
        units.sort(key=lambda unit: (-int(unit["loc"]), unit["name"]))
        for path in owned:
            module_of_path[path.as_posix()] = key
        modules.append(
            {
                "key": key,
                "label": label,
                "units": units,
                "totals": {
                    "units": len(units),
                    "files": sum(int(unit["files"]) for unit in units),
                    "loc": sum(int(unit["loc"]) for unit in units),
                },
            }
        )

    known = {key for key, _ in BACKEND_MODULES}
    cross: dict[tuple[str, str], int] = {}
    for path, source in module_of_path.items():
        try:
            tree = ast.parse(Path(path).read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError):
            continue
        targets: set[str] = set()
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module]
            for name in names:
                parts = name.split(".")
                for index, part in enumerate(parts[:-1]):
                    if part == "apps" and parts[index + 1] in known and parts[index + 1] != source:
                        targets.add(parts[index + 1])
        for target in targets:
            cross[(source, target)] = cross.get((source, target), 0) + 1

    relations = [
        {"from": source, "to": target, "count": count, "kind": "import"}
        for (source, target), count in sorted(cross.items(), key=lambda item: (-item[1], item[0]))
    ]

    return {
        "modules": modules,
        "relations": relations,
        "totals": {
            "modules": len(modules),
            "units": sum(int(module["totals"]["units"]) for module in modules),
            "files": sum(int(module["totals"]["files"]) for module in modules),
            "loc": sum(int(module["totals"]["loc"]) for module in modules),
        },
    }


ENGINE_MODULES = (
    ("ae_harness", "原型链路", "多智能体编排原型：agents / tools / assistant / workflow / event / middleware"),
    ("agents", "智能体", "角色装配、模型、工具、RAG、实时语音与知识问答"),
    ("backend_bridge", "后端桥", "给 Django 用的入口：智能体调用、报告与用量回写"),
    ("device", "设备", "Android 设备连接、动作执行与日志"),
    ("uart_log", "串口日志", "串口检测、参数、接收、切换与落盘"),
    ("utils", "通用工具", "文件与通用 IO"),
    ("vision", "视觉", "截图 OCR 识别"),
)


def collect_engine_modules() -> dict[str, Any]:
    """engines 下各模块按「一层」统计：只看模块下的直接子目录与直接文件，不再往里拆。

    口径：
    1. 模块 = engines/ 下的一个顶层目录。
    2. 单元 = 该模块下的一个直接子目录（递归汇总其中全部 .py）或一个直接 .py 文件。
    3. 排除 __init__.py、__pycache__、logs/ 这类不含业务代码的项，与 ae_harness 页一致。
    4. 行数 = 非空物理行；import 只算 engines 内部模块之间的引用。
    """
    root = REPO / "engines"
    skip_dirs = {"__pycache__", "logs", "vendor"}

    def count_loc(files: list[Path]) -> int:
        total = 0
        for path in files:
            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            total += sum(1 for line in text.splitlines() if line.strip())
        return total

    modules: list[dict[str, Any]] = []
    module_of_path: dict[str, str] = {}

    for key, label, note in ENGINE_MODULES:
        base = root / key
        if not base.is_dir():
            continue
        units: list[dict[str, Any]] = []
        all_files: list[Path] = []
        for item in sorted(base.iterdir()):
            if item.name == "__init__.py" or item.name in skip_dirs:
                continue
            if item.is_dir():
                if item.name in skip_dirs:
                    continue
                files = [f for f in sorted(item.rglob("*.py")) if "__pycache__" not in f.parts and f.name != "__init__.py"]
                if not files:
                    continue
                units.append(
                    {
                        "name": item.name + "/",
                        "kind": "dir",
                        "files": len(files),
                        "loc": count_loc(files),
                    }
                )
                all_files.extend(files)
            elif item.suffix == ".py":
                units.append(
                    {
                        "name": item.name,
                        "kind": "file",
                        "files": 1,
                        "loc": count_loc([item]),
                    }
                )
                all_files.append(item)

        units.sort(key=lambda unit: (-int(unit["loc"]), unit["name"]))
        for path in all_files:
            module_of_path[path.as_posix()] = key
        doc_path = base / "AGENTS.md"
        modules.append(
            {
                "key": key,
                "label": label,
                "note": note,
                "agentsDoc": doc_path.read_text(encoding="utf-8") if doc_path.is_file() else "",
                "units": units,
                "totals": {
                    "units": len(units),
                    "files": sum(int(unit["files"]) for unit in units),
                    "loc": sum(int(unit["loc"]) for unit in units),
                },
            }
        )

    # 跨模块 import：source 模块 → target 模块 的次数
    cross: dict[tuple[str, str], int] = {}
    for path, source_key in module_of_path.items():
        try:
            tree = ast.parse(Path(path).read_text(encoding="utf-8", errors="ignore"))
        except (SyntaxError, OSError):
            continue
        targets: set[str] = set()
        for node in ast.walk(tree):
            names: list[str] = []
            if isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module and not node.level:
                names = [node.module]
            for name in names:
                parts = name.split(".")
                if len(parts) >= 2 and parts[0] == "engines" and parts[1] in {item[0] for item in ENGINE_MODULES}:
                    if parts[1] != source_key:
                        targets.add(parts[1])
        for target in targets:
            cross[(source_key, target)] = cross.get((source_key, target), 0) + 1

    relations = [
        {"from": source, "to": target, "count": count, "kind": "import"}
        for (source, target), count in sorted(cross.items(), key=lambda item: (-item[1], item[0]))
    ]

    return {
        "modules": modules,
        "relations": relations,
        "totals": {
            "modules": len(modules),
            "units": sum(int(module["totals"]["units"]) for module in modules),
            "files": sum(int(module["totals"]["files"]) for module in modules),
            "loc": sum(int(module["totals"]["loc"]) for module in modules),
        },
    }


def collect_ae_harness() -> dict[str, Any]:
    """engines/ae_harness 按角色/事件/工具/工作流分组的模块行数与 import 关系。

    口径：一行一个 .py（排除 logs/ 与 vendor）；代码行 = 非空物理行。
    assistant/ 是角色调试入口，并入「角色」组，不单开一栏。
    import 只算本包内部模块之间的引用，外部依赖（agentscope 等）不计。
    """
    root = REPO / "engines" / "ae_harness"
    modules: dict[str, Path] = {}
    for path in _walk_code(root, (".py",)):
        rel = path.relative_to(root).as_posix()
        if rel.startswith("logs/") or "/vendor/" in rel:
            continue
        modules[path.relative_to(REPO).with_suffix("").as_posix().replace("/", ".")] = path

    # 每个模块的一句话职责：取 docstring 模板的「模块功能」字段（读不到就空）
    sys.path.insert(0, str(REPO))
    from utils.module_docstring import extract_module_docstrings  # noqa: PLC0415 - 延迟导入

    summary_of: dict[str, str] = {}
    for record in extract_module_docstrings(root, repo_root=REPO):
        rel = record["file"]
        prefix = "engines/ae_harness/"
        key = rel[len(prefix) :] if rel.startswith(prefix) else rel
        summary_of[key] = (record["fields"].get("模块功能") or "").strip()

    def group_of(module_name: str) -> str:
        rest = (
            module_name[len("engines.ae_harness.") :]
            if module_name.startswith("engines.ae_harness.")
            else ""
        )
        head = rest.split(".", 1)[0] if rest else "(根)"
        return head if head in {item[0] for item in AE_HARNESS_GROUPS} else "(根)"

    def rel_name(module_name: str) -> str:
        rest = (
            module_name[len("engines.ae_harness.") :]
            if module_name.startswith("engines.ae_harness.")
            else module_name
        )
        parts = rest.split(".")
        if parts[-1] == "__init__":
            return "/".join(parts[:-1]) + "/__init__.py" if len(parts) > 1 else "__init__.py"
        return "/".join(parts) + ".py"

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

    files_by_group: dict[str, list[dict[str, Any]]] = {key: [] for key, *_ in AE_HARNESS_GROUPS}
    cross: Counter[tuple[str, str]] = Counter()
    internal: Counter[str] = Counter()
    pairs: list[dict[str, str]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for module_name, path in sorted(modules.items()):
        group = group_of(module_name)
        _files, classes, methods, loc = _py_counts([path])
        rel_in_pkg = path.relative_to(root).as_posix()
        if group in files_by_group and path.name != "__init__.py":
            files_by_group[group].append(
                {
                    "name": path.relative_to(root / group).as_posix()
                    if group != "(根)"
                    else path.name,
                    "path": path.relative_to(REPO).as_posix(),
                    "summary": summary_of.get(rel_in_pkg, ""),
                    "classes": classes,
                    "methods": methods,
                    "loc": loc,
                }
            )
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
            resolved = target if target in modules else target + ".__init__"
            if resolved not in modules or resolved == module_name:
                continue
            source_group = group_of(module_name)
            target_group = group_of(resolved)
            pair = (rel_name(module_name), rel_name(resolved))
            if pair not in seen_pairs:
                seen_pairs.add(pair)
                pairs.append(
                    {
                        "from": pair[0],
                        "to": pair[1],
                        "fromGroup": source_group,
                        "toGroup": target_group,
                    }
                )
            if source_group == target_group:
                internal[source_group] += 1
            else:
                cross[(source_group, target_group)] += 1

    groups = []
    for key, label, note in AE_HARNESS_GROUPS:
        rows = sorted(files_by_group[key], key=lambda row: (-int(row["loc"]), row["name"]))
        doc_path = root / key / "AGENTS.md"
        groups.append(
            {
                "key": key,
                "label": label,
                "note": note,
                "agentsDoc": doc_path.read_text(encoding="utf-8") if doc_path.is_file() else "",
                "files": rows,
                "totals": {
                    "files": len(rows),
                    "classes": sum(int(row["classes"]) for row in rows),
                    "methods": sum(int(row["methods"]) for row in rows),
                    "loc": sum(int(row["loc"]) for row in rows),
                },
            }
        )
    # 跨组引用：按「引用方组 → 被引用组」聚成关系卡（谁引了谁的文件 + 为什么）
    by_key = {group["key"]: group for group in groups}
    file_index: dict[str, dict[str, Any]] = {}
    for group in groups:
        for row in group["files"]:
            rel = row["path"][len("engines/ae_harness/") :]
            file_index[rel] = row

    grouped: dict[tuple[str, str], list[dict[str, str]]] = {}
    for pair in pairs:
        if pair["fromGroup"] == pair["toGroup"]:
            continue
        grouped.setdefault((pair["fromGroup"], pair["toGroup"]), []).append(pair)

    relations = []
    for (from_group, to_group), items in sorted(grouped.items()):
        from_files, to_files = [], []
        seen_from, seen_to = set(), set()
        for item in items:
            source = file_index.get(item["from"], {})
            target = file_index.get(item["to"], {})
            if item["from"] not in seen_from:
                seen_from.add(item["from"])
                from_files.append(
                    {
                        "name": item["from"],
                        "summary": source.get("summary") or summary_of.get(item["from"], ""),
                        "loc": source.get("loc", 0),
                    }
                )
            if item["to"] not in seen_to:
                seen_to.add(item["to"])
                to_files.append(
                    {
                        "name": item["to"],
                        "summary": target.get("summary") or summary_of.get(item["to"], ""),
                        "loc": target.get("loc", 0),
                    }
                )
        relations.append(
            {
                "from": from_group,
                "to": to_group,
                "fromLabel": by_key.get(from_group, {}).get("label", from_group),
                "toLabel": by_key.get(to_group, {}).get("label", to_group),
                "count": int(cross.get((from_group, to_group), 0)),
                "fromFiles": from_files,
                "toFiles": to_files,
                "why": AE_HARNESS_WHY.get(f"{from_group}->{to_group}", ""),
            }
        )

    return {
        "groups": groups,
        "relations": relations,
        "totals": {
            "files": sum(int(group["totals"]["files"]) for group in groups),
            "loc": sum(int(group["totals"]["loc"]) for group in groups),
            "classes": sum(int(group["totals"]["classes"]) for group in groups),
            "methods": sum(int(group["totals"]["methods"]) for group in groups),
        },
        "imports": {
            "edges": [
                {"from": source, "to": target, "count": count}
                for (source, target), count in _ranked(cross)
            ],
            "internal": dict(sorted(internal.items())),
            "pairs": sorted(pairs, key=lambda item: (item["from"], item["to"])),
        },
        "note": "独立原型链路，与 engines/agents 并存，不替代它。assistant 归入角色组。",
    }


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
    for category in payload.get("categories", []):
        totals = category["totals"]
        row = {key: int(totals.get(key) or 0) for key in HISTORY_KEYS}
        row["modules"] = len(category["modules"])  # 分类下的模块/App 个数
        snapshot[category["key"]] = row
    agents_totals = payload["agents"]["totals"]
    snapshot["agents"] = {key: int(agents_totals.get(key) or 0) for key in (*HISTORY_KEYS, "tests")}

    # ae_harness 按组 + 按文件的代码行（供「每个模块的最近三次记录」对比）
    ae_harness = payload.get("ae_harness") or {}
    ae_groups: dict[str, int] = {}
    ae_files: dict[str, int] = {}
    for group in ae_harness.get("groups", []):
        ae_groups[group["key"]] = int(group["totals"].get("loc") or 0)
        for file_row in group.get("files", []):
            ae_files[f"{group['key']}/{file_row['name']}"] = int(file_row.get("loc") or 0)
    if ae_groups:
        snapshot["ae_harness"] = {"groups": ae_groups, "files": ae_files}

    # engines / backend 两页：每个模块的每个子单元行数（供「最近三次对比」）
    for payload_key, history_key in (
        ("engineModules", "engine_modules"),
        ("backendModules", "backend_modules"),
        ("frontendModules", "frontend_modules"),
        ("projectModules", "project_modules"),
    ):
        units_by_module: dict[str, dict[str, int]] = {}
        for module in (payload.get(payload_key) or {}).get("modules", []):
            units_by_module[module["key"]] = {
                unit["name"]: int(unit.get("loc") or 0) for unit in module.get("units", [])
            }
        if units_by_module:
            snapshot[history_key] = units_by_module
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
            for cat in (
        *CATEGORY_KEYS,
        "ae_harness",
        "engine_modules",
        "backend_modules",
        "frontend_modules",
        "project_modules",
    )
        )
    if changed:
        rows.append(snapshot)
    return rows[-HISTORY_LIMIT:]


def _ae_comparison(payload: dict[str, Any], history: list[dict[str, Any]]) -> dict[str, Any]:
    """ae_harness 每个组/文件的最近三次代码量（本次在前）。

    Args:
        payload: build() 的结果（用到 ae_harness.groups 的文件名）。
        history: 已按时间升序的历史快照。

    Returns:
        {"at": [本次, 上次, 上上次], "groups": {key: [n, n-1, n-2]}, "files": {...}}；
        历史里没有对应记录的位置是 null，页面据此显示"待记录"而不是 0。
    """
    scope = 3
    entries = [row for row in history if isinstance(row.get("ae_harness"), dict)][-scope:]
    ats = [row.get("at", "") for row in reversed(entries)]
    while len(ats) < scope:
        ats.append("")

    groups: dict[str, list[int | None]] = {
        group["key"]: [] for group in payload.get("ae_harness", {}).get("groups", [])
    }
    files: dict[str, list[int | None]] = {}
    for group in payload.get("ae_harness", {}).get("groups", []):
        for file_row in group.get("files", []):
            files[f"{group['key']}/{file_row['name']}"] = []

    for row in reversed(entries):
        slice_ = row.get("ae_harness") or {}
        group_values = slice_.get("groups") or {}
        file_values = slice_.get("files") or {}
        for key in groups:
            groups[key].append(int(group_values[key]) if key in group_values else None)
        for key in files:
            files[key].append(int(file_values[key]) if key in file_values else None)

    for mapping in (groups, files):
        for key, values in mapping.items():
            while len(values) < scope:
                values.append(None)
    return {"at": ats, "groups": groups, "files": files, "scope": scope}


def _module_comparison(
    payload: dict[str, Any],
    history: list[dict[str, Any]],
    *,
    payload_key: str,
    history_key: str,
) -> dict[str, Any]:
    """某个 payload 键下每个模块/单元的最近三次行数（本次在前）。

    Args:
        payload: build() 的结果。
        history: 已按时间升序的历史快照。
        payload_key: payload 里存模块结构的键，例如 engineModules。
        history_key: history 里存行数的键，例如 engine_modules。

    Returns:
        {"at": [本次, 上次, 上上次], "units": {module: {unit: [n, n-1, n-2]}},
         "totals": {module: [n, n-1, n-2]}, "scope": 3}；缺的位置是 null。
    """
    scope = 3
    entries = [row for row in history if isinstance(row.get(history_key), dict)][-scope:]
    ats = [row.get("at", "") for row in reversed(entries)]
    while len(ats) < scope:
        ats.append("")

    modules = payload.get(payload_key, {}).get("modules", [])
    units: dict[str, dict[str, list[int | None]]] = {
        module["key"]: {unit["name"]: [] for unit in module.get("units", [])} for module in modules
    }
    totals: dict[str, list[int | None]] = {module["key"]: [] for module in modules}

    for row in reversed(entries):
        slice_ = row.get(history_key) or {}
        for module in modules:
            key = module["key"]
            values = slice_.get(key) or {}
            subtotal = 0
            for unit in module.get("units", []):
                name = unit["name"]
                has = name in values
                units[key][name].append(int(values[name]) if has else None)
                if has:
                    subtotal += int(values[name])
            totals[key].append(subtotal if values else None)

    for per_unit in units.values():
        for values in per_unit.values():
            while len(values) < scope:
                values.append(None)
    for values in totals.values():
        while len(values) < scope:
            values.append(None)
    return {"at": ats, "units": units, "totals": totals, "scope": scope}


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
    payload["ae_harness"]["comparison"] = _ae_comparison(payload, history)
    for payload_key, history_key in (
        ("engineModules", "engine_modules"),
        ("backendModules", "backend_modules"),
        ("frontendModules", "frontend_modules"),
        ("projectModules", "project_modules"),
    ):
        section = payload.get(payload_key)
        if not section:
            continue
        comparison = _module_comparison(payload, history, payload_key=payload_key, history_key=history_key)
        section["comparison"] = comparison
        for module in section["modules"]:
            for unit in module["units"]:
                trend = comparison["units"].get(module["key"], {}).get(unit["name"]) or []
                unit["trend"] = (trend + [None, None, None])[:3]
            total = (comparison["totals"].get(module["key"]) or []) + [None, None, None]
            module["totalTrend"] = total[:3]
    # 把三次代码量挂到每个文件上，页面按模块一图一柱组直接用
    comparison = payload["ae_harness"]["comparison"]
    for group in payload["ae_harness"]["groups"]:
        for file_row in group["files"]:
            key = f"{group['key']}/{file_row['name']}"
            file_row["trend"] = comparison["files"].get(key, [])[:3] or [
                file_row["loc"],
                None,
                None,
            ]
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

    summary = [
        ("总览", payload["projectModules"]),
        ("前端", payload["frontendModules"]),
        ("后端", payload["backendModules"]),
        ("引擎", payload["engineModules"]),
    ]
    detail = " · ".join(
        f"{label} {section['totals']['modules']} 模块 / {section['totals']['loc']} 行" for label, section in summary
    )
    print(  # noqa: T201
        f"已写出 {json_path.name}, {js_path.name}, history.js：{detail} · 历史 {len(history)} 次"
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
