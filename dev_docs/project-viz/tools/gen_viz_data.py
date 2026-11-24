"""
模块功能：➡️ 按目标目录产出项目可视化三节所需的数据（代码量 CSV / 依赖 JSON / 页面壳 viz.js）🏁
Python 调试：➡️python dev_docs/project-viz/tools/gen_viz_data.py --target engines/ae_harness 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 与旧口径对账：python dev_docs/project-viz/tools/gen_viz_data.py --check
2. 页面自检：双击 dev_docs/project-viz/index.html，三节齐全（见 README「自检」）
🏁

口径（改之前先想清"模块"到底指什么）：
1. 模块 = 目标目录的展开首层（目录或代码文件），只展开这一级；默认目标是仓库根。
2. 单元 = 目录模块的直接子项数；模块本身是文件时为 None（页面显示「—」）。
3. 代码行 = 非空物理行；文件 = 代码文件数（排除 __init__.py / __pycache__ / migrations / vendor / logs）。
4. 依赖 = 一个文件对同一目标模块只计一次；前端→后端是 HTTP 调用，不是 import。
5. 架构 = config/architecture.<slug>.json（人工语义，代码检测不出来，由 Agent 维护）。

Usage:
    python dev_docs/project-viz/tools/gen_viz_data.py                        # 仓库总览
    python dev_docs/project-viz/tools/gen_viz_data.py --target engines       # engines 首层
    python dev_docs/project-viz/tools/gen_viz_data.py --target engines/ae_harness
    python dev_docs/project-viz/tools/gen_viz_data.py --check                # 只比对是否过期
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys

from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Iterator
from zoneinfo import ZoneInfo

HERE = Path(__file__).resolve()
PROJECT_VIZ = HERE.parent.parent
REPO = next(
    (path for path in HERE.parents if (path / "engines" / "AGENTS.md").is_file()),
    HERE.parents[-1],
)
CONFIG_DIR = PROJECT_VIZ / "config"
DATA_DIR = PROJECT_VIZ / "data"
TZ = ZoneInfo("Asia/Shanghai")

CODE_EXTS = {".py", ".ts", ".tsx", ".vue", ".js", ".mjs", ".css", ".html"}
SKIP_FILES = {"__init__.py"}
SKIP_DIRS = {
    "__pycache__",
    "migrations",
    "node_modules",
    "dist",
    "build",
    "vendor",
    "logs",
    "temps",
    "data",
    "dev_docs",
    "platform-tools",
    "pytest-of-zhiyan",
    "site-packages",
}
CLIENT_IMPORT_RE = re.compile(r"""import\s+(\w+)\s+from\s+["']@/shared/api-client["']""")
CALL_RE = r"""(?:{names})\.(get|post|put|patch|delete)(?:\s*<[^(]*>)?\(\s*[`'"]([^`'"]+)[`'"]"""


def slugify(target: str) -> str:
    """目标目录 → 产物与配置文件的 slug（'.' → repo-root，'a/b' → a-b）。"""
    cleaned = target.strip().strip("/\\") or "."
    if cleaned == ".":
        return "repo-root"
    return re.sub(r"[^0-9a-zA-Z]+", "-", cleaned).strip("-").lower()


def resolve_target(target: str) -> Path:
    """把 --target 解析成目录；越界或不存在直接报错退出。"""
    path = (REPO / target).resolve() if target not in (".", "") else REPO
    if not path.is_dir():
        raise SystemExit(f"目标不是目录：{target}")
    if REPO not in path.parents and path != REPO:
        raise SystemExit(f"目标必须在本仓库内：{target}")
    return path


def nonblank_lines(path: Path) -> int:
    """文件里的非空物理行数。"""
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return 0
    return sum(1 for line in text.splitlines() if line.strip())


def is_skipped(name: str) -> bool:
    """条目是否属于缓存 / 第三方 / 文档 / 运行数据这类非模块目录。"""
    return name.startswith(".") or name in SKIP_DIRS or name in SKIP_FILES


def code_files(folder: Path) -> list[Path]:
    """目录下（递归）的代码文件，跳过隐藏目录与 SKIP_DIRS。"""
    found: list[Path] = []
    for path in sorted(folder.rglob("*")):
        if not path.is_file() or path.suffix not in CODE_EXTS or is_skipped(path.name):
            continue
        if any(is_skipped(part) for part in path.relative_to(folder).parts[:-1]):
            continue
        found.append(path)
    return found


def count_units(folder: Path) -> int:
    """目录模块的直接子项数（子目录需含代码才算一个单元）。"""
    total = 0
    for child in sorted(folder.iterdir()):
        if is_skipped(child.name):
            continue
        if child.is_dir():
            total += 1 if code_files(child) else 0
        elif child.suffix in CODE_EXTS:
            total += 1
    return total


def module_row(entry: Path) -> dict[str, Any] | None:
    """首层条目 → 一行模块；不含代码的目录不算模块。"""
    if entry.is_file():
        if entry.suffix not in CODE_EXTS or is_skipped(entry.name):
            return None
        return {
            "key": entry.name,
            "kind": "file",
            "loc": nonblank_lines(entry),
            "files": 1,
            "units": None,
        }
    files = code_files(entry)
    if not files:
        return None
    return {
        "key": entry.name,
        "kind": "dir",
        "loc": sum(nonblank_lines(path) for path in files),
        "files": len(files),
        "units": count_units(entry),
    }


def scan(target_dir: Path) -> list[tuple[Path, dict[str, Any]]]:
    """目标目录的首层模块（目录或代码文件），按代码行降序。"""
    rows: list[tuple[Path, dict[str, Any]]] = []
    for entry in sorted(target_dir.iterdir()):
        if is_skipped(entry.name):
            continue
        row = module_row(entry)
        if row:
            rows.append((entry, row))
    return sorted(rows, key=lambda item: (-item[1]["loc"], item[1]["key"]))


def dotted(path: Path) -> str:
    """仓库内路径 → 点分模块名（__init__.py 取包名，仓库根取空串）。"""
    if path == REPO:
        return ""
    parts = list(path.relative_to(REPO).with_suffix("").parts)
    if parts and parts[-1] == "__init__":
        parts = parts[:-1]
    return ".".join(parts)


def module_paths(entry: Path) -> list[Path]:
    """一个模块拥有的文件（文件模块只有自己）。"""
    return [entry] if entry.is_file() else code_files(entry)


def dotted_owner(pairs: list[tuple[Path, dict[str, Any]]]) -> dict[str, str]:
    """点分模块名 → 所属模块 key，用于把 import 归到模块上。

    `__init__.py` 不计入代码文件，但它所在的包名仍要能解析（`from engines.x import y`），
    所以除了文件本身的点分名，也登记它所在的包名。
    """
    owner: dict[str, str] = {}
    for entry, row in pairs:
        for path in module_paths(entry):
            if path.suffix != ".py":
                continue
            owner[dotted(path)] = row["key"]
            package = dotted(path.parent)
            if package:
                owner.setdefault(package, row["key"])
    return owner


def resolve_import(name: str, level: int, package: str, owner: dict[str, str]) -> str | None:
    """把一条 import 语句解析成模块 key；解析不出来就丢弃。"""
    if level == 0:
        return owner.get(name)
    parts = package.split(".") if package else []
    base = parts[: len(parts) - (level - 1)] if level > 1 else parts
    full = ".".join([*base, name]) if name else ".".join(base)
    return owner.get(full)


def imports_of(tree: ast.AST) -> Iterator[tuple[str, int]]:
    """AST 里的 (模块名, 相对层级)；from X import a, b 里的 a/b 不展开。"""
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                yield alias.name, 0
        elif isinstance(node, ast.ImportFrom):
            yield (node.module or ""), node.level


def collect_edges(pairs: list[tuple[Path, dict[str, Any]]], target_dir: Path) -> list[dict[str, Any]]:
    """模块之间的依赖边：Python import + 前端→后端的 HTTP 调用。"""
    owner = dotted_owner(pairs)
    keys = {row["key"] for _, row in pairs}
    cross: Counter[tuple[str, str]] = Counter()
    for entry, row in pairs:
        for path in module_paths(entry):
            if path.suffix != ".py":
                continue
            try:
                tree = ast.parse(path.read_text(encoding="utf-8", errors="ignore"))
            except (SyntaxError, OSError):
                continue
            package = dotted(path.parent)
            targets = {
                other
                for name, level in imports_of(tree)
                if (other := resolve_import(name, level, package, owner)) and other != row["key"]
            }
            for other in targets:
                cross[(row["key"], other)] += 1
    edges = [
        {"from": source, "to": target, "kind": "import", "count": count}
        for (source, target), count in sorted(cross.items(), key=lambda item: (-item[1], item[0]))
    ]
    http = http_call_count()
    if http and {"frontend", "backend"} <= keys:
        edges.append({"from": "frontend", "to": "backend", "kind": "http", "count": http})
        edges.sort(key=lambda row: (-int(row["count"]), str(row["from"])))
    return edges


def http_call_count() -> int:
    """前端调后端的 HTTP 次数：扫 frontend/src/modules 下的 .ts，按 api-client 别名抓调用。"""
    modules_dir = REPO / "frontend" / "src" / "modules"
    if not modules_dir.is_dir():
        return 0
    total = 0
    for path in sorted(modules_dir.rglob("*.ts")):
        if "components" in path.relative_to(modules_dir).parts:
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        names = CLIENT_IMPORT_RE.findall(text) or ["client"]
        pattern = re.compile(CALL_RE.format(names="|".join(re.escape(name) for name in names)))
        total += len(pattern.findall(text))
    return total


def load_architecture(slug: str) -> dict[str, Any] | None:
    """读 config/architecture.<slug>.json；没有就返回 None（页面显示空态，不编造）。"""
    path = CONFIG_DIR / f"architecture.{slug}.json"
    if not path.is_file():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"架构配置不是合法 JSON：{path}（{exc}）") from exc


def build(target: str) -> dict[str, Any]:
    """采集一个目标层级，返回三节数据。"""
    target_dir = resolve_target(target)
    slug = slugify(target)
    pairs = scan(target_dir)
    return {
        "target": "." if target in (".", "") else target.strip("/\\"),
        "slug": slug,
        "generated_at": datetime.now(TZ).strftime("%Y-%m-%d %H:%M"),
        "modules": [row for _, row in pairs],
        "edges": collect_edges(pairs, target_dir),
        "arch": load_architecture(slug),
        "docs": collect_docs(),
    }


def csv_text(modules: list[dict[str, Any]]) -> str:
    """模块级 CSV：表头 + 每行一个模块（文件模块的 units 留空）。"""
    lines = ["module,loc,files,units"]
    for row in modules:
        units = "" if row["units"] is None else str(row["units"])
        lines.append(f"{row['key']},{row['loc']},{row['files']},{units}")
    return "\n".join(lines) + "\n"


def deps_payload(bundle: dict[str, Any]) -> dict[str, Any]:
    """依赖 JSON：只放目标、快照时间与边（模块在 CSV 里，不重复序列化）。"""
    return {
        "target": bundle["target"],
        "slug": bundle["slug"],
        "generated_at": bundle["generated_at"],
        "edges": bundle["edges"],
    }


def viz_text(bundle: dict[str, Any]) -> str:
    """页面壳：三节数据合成一个 window.__VIZ__（file:// 下 <script src> 可加载）。"""
    payload = {
        "target": bundle["target"],
        "slug": bundle["slug"],
        "generatedAt": bundle["generated_at"],
        "modules": bundle["modules"],
        "edges": bundle["edges"],
        "arch": bundle["arch"],
    }
    return "/* 由 dev_docs/project-viz/tools/gen_viz_data.py 生成，勿手改。 */\n" + (
        "window.__VIZ__ = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    )


DOC_FILE_NAME = "AGENTS.md"
DOCS_ROOT = REPO / ".agents" / "docs"
MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)\s]+)\)")


DOC_SKIP_DIRS = {"node_modules", ".venv", ".dvenv", "dist", "build", "site-packages", "temps", "__pycache__"}


def is_doc_dir(part: str) -> bool:
    """文档扫描的目录过滤：依赖 / 临时 / 缓存 / 技能树都不算仓库文档（dev_docs 要算）。"""
    return part in DOC_SKIP_DIRS or (part.startswith(".") and part != ".agents")


def repo_docs() -> list[Path]:
    """全仓文档：所有 AGENTS.md（含 .agents/AGENTS.md 与 dev_docs 下的）+ .agents/docs 下的 Markdown。"""
    agents: list[Path] = []
    for path in REPO.rglob(DOC_FILE_NAME):
        parts = path.relative_to(REPO).parts[:-1]
        if any(is_doc_dir(part) for part in parts):
            continue
        agents.append(path)
    module = sorted(DOCS_ROOT.rglob("*.md")) if DOCS_ROOT.is_dir() else []
    return sorted({*agents, *module})


def doc_title(path: Path, text: str) -> str:
    """文档标题：第一个一级标题，退化成文件名。"""
    for line in text.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return path.name


def doc_scope(path: Path) -> list[str]:
    """文档的管辖目录 = 它自己所在的目录（根文档管整仓）。

    为什么不解析正文里写的路径：那些反引号既可能是仓库相对、也可能是文档相对，
    还混着占位符（`<模块>`、`{app}`），解析出来会把图撑满噪声节点；而「本文件只约束 X/」
    的 X 与文档所在目录一致，按位置取更可靠。
    """
    parent = path.parent.relative_to(REPO).as_posix()
    return [parent or "."]


def doc_links(path: Path, text: str) -> list[str]:
    """文档里指向其它 Markdown 的相对链接（去掉锚点、解析成仓库相对路径）。"""
    links: list[str] = []
    for raw in MD_LINK_RE.findall(text):
        target = raw.split("#", 1)[0]
        if not target.endswith(".md") or "://" in target:
            continue
        resolved = (path.parent / target).resolve()
        if REPO in resolved.parents:
            links.append(resolved.relative_to(REPO).as_posix())
    return links


def doc_edges(documents: dict[str, dict[str, Any]]) -> list[dict[str, str]]:
    """文档关系边：层级（父 → 子）、管辖（文档 → 路径）、引用（AGENTS → 它列出的文档）。"""
    edges: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()

    def add(source: str, target: str, kind: str) -> None:
        if source == target or (source, target) in seen:
            return
        seen.add((source, target))
        edges.append({"from": source, "to": target, "kind": kind})

    for rel, item in documents.items():
        for scope in item["scope"]:
            add(rel, f"path:{scope}", "governs")
    for rel, item in documents.items():
        if item["parent"]:
            add(item["parent"], rel, "hierarchy")
    for rel, item in documents.items():
        if not rel.endswith(DOC_FILE_NAME):
            continue
        for target in item["links"]:
            if target in documents:
                add(rel, target, "references")
    return edges


def load_documents() -> dict[str, dict[str, Any]]:
    """读全仓文档，逐个解析出标题 / 管辖 / 出链 / 全文。"""
    documents: dict[str, dict[str, Any]] = {}
    for path in repo_docs():
        rel = path.relative_to(REPO).as_posix()
        text = path.read_text(encoding="utf-8", errors="replace")
        documents[rel] = {
            "id": rel,
            "path": rel,
            "title": doc_title(path, text),
            "kind": "root" if rel == DOC_FILE_NAME else ("agents" if path.name == DOC_FILE_NAME else "doc"),
            "bytes": path.stat().st_size,
            "lines": len(text.splitlines()),
            "scope": doc_scope(path) if path.name == DOC_FILE_NAME else [],
            "links": doc_links(path, text),
            "text": text,
            "parent": "",
        }
    return documents


def wire_parents(documents: dict[str, dict[str, Any]]) -> None:
    """给每篇 AGENTS.md 找最近的祖先 AGENTS.md 作为父文档（根文档没有父）。"""
    for rel, item in documents.items():
        if rel == DOC_FILE_NAME or item["kind"] != "agents":
            continue
        parent = ""
        for ancestor in Path(rel).parents:
            candidate = DOC_FILE_NAME if str(ancestor) == "." else (ancestor / DOC_FILE_NAME).as_posix()
            if candidate != rel and candidate in documents:
                parent = candidate
                break
        item["parent"] = parent or DOC_FILE_NAME


def collect_docs() -> dict[str, Any]:
    """把仓库里的 AGENTS.md 与 .agents/docs 文档整理成「文档树 + 关系边 + 全文」。"""
    documents = load_documents()
    wire_parents(documents)
    paths = sorted({scope for item in documents.values() for scope in item["scope"]})
    return {
        "generated_at": datetime.now(TZ).strftime("%Y-%m-%d %H:%M"),
        "documents": list(documents.values()),
        "paths": [{"id": f"path:{p}", "path": p} for p in paths],
        "edges": doc_edges(documents),
    }


def docs_text(docs: dict[str, Any]) -> str:
    """文档页数据：全文内联（file:// 下不能 fetch，只能一次性带过去）。"""
    payload = {
        "generatedAt": docs["generated_at"],
        "documents": [{key: value for key, value in item.items() if key != "links"} for item in docs["documents"]],
        "paths": docs["paths"],
        "edges": docs["edges"],
    }
    return "/* 由 dev_docs/project-viz/tools/gen_viz_data.py 生成，勿手改。 */\n" + (
        "window.__DOCS__ = " + json.dumps(payload, ensure_ascii=False, separators=(",", ":")) + ";\n"
    )


def read_text_or_empty(path: Path) -> str:
    """读文件；不存在返回空串（供 --check 比对）。"""
    return path.read_text(encoding="utf-8") if path.is_file() else ""
def viz_payload(text: str) -> dict[str, Any] | None:
    """从 viz.js 文本里取回 window.__VIZ__ 的载荷（比对时忽略 generatedAt）。"""
    marker = "window.__VIZ__ = "
    if marker not in text:
        return None
    try:
        payload = json.loads(text.split(marker, 1)[1].rstrip().rstrip(";"))
    except json.JSONDecodeError:
        return None
    payload.pop("generatedAt", None)
    return payload


def docs_payload(text: str) -> dict[str, Any] | None:
    """从 docs.js 文本里取回 window.__DOCS__ 的载荷（比对时忽略 generatedAt）。"""
    marker = "window.__DOCS__ = "
    if marker not in text:
        return None
    try:
        payload = json.loads(text.split(marker, 1)[1].rstrip().rstrip(";"))
    except json.JSONDecodeError:
        return None
    payload.pop("generatedAt", None)
    return payload


def stale_files(bundle: dict[str, Any]) -> list[str]:
    """与盘上产物比对，返回过期清单（忽略 generated_at / generatedAt）。"""
    stale: list[str] = []
    if read_text_or_empty(DATA_DIR / "code-stats.csv") != csv_text(bundle["modules"]):
        stale.append("code-stats.csv")
    expected_deps = {key: value for key, value in deps_payload(bundle).items() if key != "generated_at"}
    try:
        deps = json.loads(read_text_or_empty(DATA_DIR / "dependencies.json"))
        deps.pop("generated_at", None)
    except json.JSONDecodeError:
        deps = None
    if deps != expected_deps:
        stale.append("dependencies.json")
    expected_viz = {
        "target": bundle["target"],
        "slug": bundle["slug"],
        "modules": bundle["modules"],
        "edges": bundle["edges"],
        "arch": bundle["arch"],
    }
    if viz_payload(read_text_or_empty(DATA_DIR / "viz.js")) != expected_viz:
        stale.append("viz.js")
    if docs_payload(read_text_or_empty(DATA_DIR / "docs.js")) != docs_payload(docs_text(bundle["docs"])):
        stale.append("docs.js")
    return stale


def write_outputs(bundle: dict[str, Any]) -> None:
    """写产物（三节 + 文档页；覆盖：一次只维护一个层级）。"""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "code-stats.csv").write_text(csv_text(bundle["modules"]), encoding="utf-8")
    (DATA_DIR / "dependencies.json").write_text(
        json.dumps(deps_payload(bundle), ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (DATA_DIR / "viz.js").write_text(viz_text(bundle), encoding="utf-8")
    (DATA_DIR / "docs.js").write_text(docs_text(bundle["docs"]), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    """CLI：--target 选层级，--check 只比对不写盘。"""
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    parser = argparse.ArgumentParser(description="生成项目可视化的三节数据（覆盖写入 data/）", add_help=True)
    parser.add_argument("--target", default=".", help="模块来源目录（默认仓库根）")
    parser.add_argument("--check", action="store_true", help="只比对现有产物是否过期，不写盘")
    args = parser.parse_args(argv)

    bundle = build(args.target)
    total = sum(int(row["loc"]) for row in bundle["modules"])
    docs = bundle["docs"]
    if args.check:
        stale = stale_files(bundle)
        if stale:
            print(f"数据已过期：{', '.join(stale)}（重跑 gen_viz_data.py --target {bundle['target']}）")
            return 1
        print(f"数据最新：{bundle['target']} · {len(bundle['modules'])} 模块 / {total:,} 行 · 文档 {len(docs['documents'])} 篇")
        return 0

    write_outputs(bundle)
    arch = "有" if bundle["arch"] else "缺（config/architecture.%s.json）" % bundle["slug"]
    print(
        f"已写出 code-stats.csv / dependencies.json / viz.js / docs.js："
        f"{bundle['target']} · {len(bundle['modules'])} 模块 / {total:,} 行 · "
        f"{len(bundle['edges'])} 条边 · 架构 {arch} · 文档 {len(docs['documents'])} 篇 / {len(docs['edges'])} 条关系"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
