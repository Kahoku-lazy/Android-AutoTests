#!/usr/bin/env python3
"""需求 × 代码 关系图生成器 — 图 JSON + 工作台页面 + 方案文档页。

把「需求（PRD 功能域 / OpenSpec 规格与 Requirement）」「代码（文件 / 符号 / 路由 / 数据表）」
「测试（文件 + 文件头规格锚点）」编成一张**每个节点都带可重放锚点**的 JSON 图，
再渲染成自包含 HTML（工作台可载入任意同 schema 的 JSON）。

人工输入只有一处：``tools/arch_graph/declarations.json`` 里的「功能域 → 代码」声明；
其余节点与关系全部从仓库真实文件里读出来。

用法:
  python tools/gen_arch_graph.py                      # 全部范围：JSON + 工作台页 + 文档页
  python tools/gen_arch_graph.py --only workbench     # 只出 JSON + 工作台页
  python tools/gen_arch_graph.py --scope login --quiet
  python tools/gen_arch_graph.py --out-dir temps/x    # 换产物目录

产物目录与文件名由声明文件 ``tools/arch_graph/declarations.json`` 决定（``out_dir`` 加每个
scope 的 ``outputs``）；工具代码不写死任何文档位置。

schema: ``arch-graph/1`` —— 节点 ``{id, kind, title, anchor, anchor_ok, anchor_detail, ...}``，
边 ``{id, from, to, type, confidence, evidence}``；``confidence`` 取 declared（人声明）或
derived（机器推断）。锚点类型：file / md_heading / symbol / route / db_table。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# 控制台统一 UTF-8：本脚本会打印 emoji，Windows 中文环境默认 GBK 会在管道下抛
# UnicodeEncodeError 并与「真实失败」无法区分。被 pytest 等捕获时 stdout 可能不是
# TextIOWrapper，故用 hasattr 守卫。
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        _stream.reconfigure(encoding="utf-8", errors="replace")

TOOLS_DIR = Path(__file__).resolve().parent
ROOT = TOOLS_DIR.parent
ARCH_DIR = TOOLS_DIR / "arch_graph"
DECLARATIONS = ARCH_DIR / "declarations.json"
TEMPLATES = ARCH_DIR / "templates"
FALLBACK_OUT_DIR = ARCH_DIR / "out"

SCHEMA_VERSION = "arch-graph/1"
PLACEHOLDER = "__GRAPH_JSON__"


# ── 0. 基础 ─────────────────────────────────────────────────


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8", errors="replace")


def exists(rel: str) -> bool:
    return (ROOT / rel).exists()


def git_rev() -> str:
    try:
        return subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=20,
        ).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def load_declarations() -> tuple[list[dict], Path]:
    """读声明文件，返回（scopes, 默认产物目录）。"""
    data = json.loads(DECLARATIONS.read_text(encoding="utf-8"))
    scopes = data.get("scopes") or []
    if not scopes:
        raise SystemExit(f"声明文件里没有任何 scope：{DECLARATIONS}")
    raw_out = data.get("out_dir") or ""
    out_dir = (ROOT / raw_out).resolve() if raw_out else FALLBACK_OUT_DIR
    return scopes, out_dir


# ── 1. 需求侧：PRD ──────────────────────────────────────────


def parse_prd(rel: str) -> dict:
    """抽出 PRD 的标题、功能域小节锚点、以及「规格真相源」一行里登记的规格 id。"""
    lines = read(rel).splitlines()
    title = next((ln[2:].strip() for ln in lines if ln.startswith("# ")), "PRD")

    domains: list[dict] = []
    spec_line = ""
    in_product = False
    for i, ln in enumerate(lines, start=1):
        if ln.startswith("## 产品功能"):
            in_product = True
            continue
        if ln.startswith("## 测试"):
            in_product = False
        if "规格真相源" in ln and not spec_line:
            spec_line = ln
        if in_product and re.match(r"^### \S", ln):
            domains.append({"name": ln[4:].strip(), "line": i, "anchor": ln})

    return {
        "title": title,
        "domains": domains,
        "declared_specs": re.findall(r"`([a-z0-9][a-z0-9/-]+)`", spec_line),
    }


# ── 2. 需求侧：OpenSpec 规格 ────────────────────────────────


def parse_spec(spec_id: str) -> dict | None:
    rel = f"openspec/specs/{spec_id}/spec.md"
    if not exists(rel):
        return None
    reqs: list[dict] = []
    current: dict | None = None
    for i, ln in enumerate(read(rel).splitlines(), start=1):
        if ln.startswith("### Requirement:"):
            current = {"name": ln.split(":", 1)[1].strip(), "line": i, "scenarios": []}
            reqs.append(current)
        elif ln.startswith("#### Scenario:") and current is not None:
            current["scenarios"].append({"name": ln.split(":", 1)[1].strip(), "line": i})
    return {"path": rel, "requirements": reqs}


# ── 3. 代码侧：符号与端点 ───────────────────────────────────


def symbol_exists(rel: str, name: str) -> bool:
    if not exists(rel):
        return False
    pat = re.compile(rf"^\s*(?:async\s+)?(?:def|class)\s+{re.escape(name)}\b", re.M)
    return bool(pat.search(read(rel)))


def parse_endpoints(routes: dict) -> list[dict]:
    """从 urls.py 的路由表读静态端点（router 展开的动态路由不计）。"""
    rel = routes["urls"]
    out = []
    for m in re.finditer(r'path\(\s*"([^"]+)"\s*,\s*(\w+)', read(rel)):
        out.append({"literal": m.group(1), "view": m.group(2)})
    return out


# ── 4. 测试侧：文件 + 文件头的规格锚点 ──────────────────────


def scan_tests(cfg: dict) -> list[dict]:
    """扫测试文件，认三种并存的锚点写法（规格路径 / 变更 delta 路径 / 变更单号）。"""
    name_re = re.compile(cfg["name_pattern"], re.I)
    found: list[dict] = []
    for d in cfg["dirs"]:
        base = ROOT / d
        if not base.exists():
            continue
        for f in sorted(base.rglob("*")):
            if f.suffix not in (".py", ".ts") or not f.is_file() or not name_re.search(f.name):
                continue
            rel = f.relative_to(ROOT).as_posix()
            text = f.read_text(encoding="utf-8", errors="replace")

            direct = re.findall(r"openspec/specs/([a-z0-9][a-z0-9/-]+)/spec\.md", text)
            direct += re.findall(r"openspec/specs/([a-z0-9][a-z0-9-]+)(?![a-z0-9/.-])", text)
            direct = list(dict.fromkeys(direct))
            delta = re.findall(
                r"openspec/changes/(?:archive/\d{4}-\d{2}-\d{2}-)?[a-z0-9-]+"
                r"/specs/([a-z0-9][a-z0-9/-]+)/spec\.md",
                text,
            )
            change = re.findall(r"OpenSpec[:：]\s*([a-z0-9][a-z0-9-]+)", text)

            if direct:
                target, style = direct[0], "openspec_specs_path"
            elif delta:
                target, style = delta[0], "change_delta_path"
            elif change:
                target, style = change[0], "openspec_change_id"
            else:
                target, style = "", ""

            case_count = (
                len(re.findall(r"^\s*def test_", text, re.M))
                if f.suffix == ".py"
                else len(re.findall(r"^\s*it\(", text, re.M))
            )
            found.append(
                {
                    "path": rel,
                    "target": target,
                    "anchor_style": style,
                    "header_change": change[0] if change else "",
                    "case_count": case_count,
                }
            )
    return found


# ── 5. 建图 ─────────────────────────────────────────────────


class Graph:
    """节点表 + 边表，按 id 去重；边只允许落在已存在的节点上。"""

    def __init__(self) -> None:
        self.nodes: dict[str, dict] = {}
        self.edges: list[dict] = []
        self._keys: set[tuple[str, str, str]] = set()

    def node(self, nid: str, kind: str, title: str, anchor: dict, **extra: Any) -> str:
        if nid not in self.nodes:
            self.nodes[nid] = {"id": nid, "kind": kind, "title": title, "anchor": anchor, **extra}
        return nid

    def edge(self, src: str, dst: str, etype: str, confidence: str, evidence: str) -> None:
        key = (src, dst, etype)
        if key in self._keys or src not in self.nodes or dst not in self.nodes:
            return
        self._keys.add(key)
        self.edges.append(
            {
                "id": f"e{len(self.edges) + 1}",
                "from": src,
                "to": dst,
                "type": etype,
                "confidence": confidence,
                "evidence": evidence,
            }
        )


def _file_node(g: Graph, path: str) -> str:
    fid = f"FILE:{path}"
    g.node(
        fid,
        "file",
        path.split("/")[-1],
        {"type": "file", "path": path},
        layer="code",
        subtitle=path,
        lang=path.rsplit(".", 1)[-1],
    )
    return fid


def build_scope(scope: dict) -> dict:
    """把一条 scope 声明 + 仓库事实编成图。"""
    prd = parse_prd(scope["prd"])
    domain_decl: dict[str, list] = scope["domains"]
    spec_domains: dict[str, list] = scope["spec_domains"]
    specs = {sid: parse_spec(sid) for sid in spec_domains}
    g = Graph()

    # ── 需求来源：PRD + 功能域 ──
    prd_id = f"PRD:{scope['id']}"
    g.node(
        prd_id,
        "prd",
        f"{prd['title']}（PRD-{scope['id']}）",
        {"type": "file", "path": scope["prd"]},
        layer="requirement",
        subtitle=scope["name"],
    )
    domain_ids: dict[str, str] = {}
    for d in prd["domains"]:
        did = f"DOM:{d['name']}"
        domain_ids[d["name"]] = did
        g.node(
            did,
            "domain",
            d["name"],
            {"type": "md_heading", "path": scope["prd"], "heading": d["anchor"]},
            layer="requirement",
        )
        g.edge(prd_id, did, "belongs_to", "declared", f"{scope['prd']}:{d['line']} 功能域小节")

    # ── 代码侧先建节点，需求→代码的边才有落点 ──
    for items in domain_decl.values():
        for path, sym in items:
            fid = _file_node(g, path)
            if sym:
                snode = f"SYM:{path}#{sym}"
                g.node(
                    snode,
                    "symbol",
                    sym,
                    {"type": "symbol", "path": path, "name": sym},
                    layer="code",
                    subtitle=path,
                )
                g.edge(fid, snode, "declares", "derived", f"{path} 定义 {sym}")

    # ── 规格 → 需求 → 场景 ──
    spec_ids: dict[str, str] = {}
    for sid, doms in spec_domains.items():
        s = specs.get(sid)
        rel = f"openspec/specs/{sid}/spec.md"
        spec_node = f"SPEC:{sid}"
        spec_ids[sid] = spec_node
        g.node(
            spec_node,
            "spec",
            sid,
            {"type": "file", "path": rel},
            layer="requirement",
            subtitle=f"{len(s['requirements']) if s else 0} 条 Requirement",
        )
        for dom in doms:
            if dom in domain_ids:
                g.edge(
                    domain_ids[dom],
                    spec_node,
                    "specified_by",
                    "declared",
                    f"声明「{sid}」服务「{dom}」",
                )
        if not s:
            continue
        for r in s["requirements"]:
            rid = f"REQ:{sid}#{r['name']}"
            g.node(
                rid,
                "requirement",
                r["name"],
                {"type": "md_heading", "path": rel, "heading": f"### Requirement: {r['name']}"},
                layer="requirement",
                subtitle=f"{len(r['scenarios'])} 个 Scenario",
                line=r["line"],
            )
            g.edge(spec_node, rid, "contains", "derived", f"{rel}:{r['line']}")
            for sc in r["scenarios"]:
                scid = f"SCN:{sid}#{r['name']}#{sc['name']}"
                g.node(
                    scid,
                    "scenario",
                    sc["name"],
                    {
                        "type": "md_heading",
                        "path": rel,
                        "heading": f"#### Scenario: {sc['name']}",
                    },
                    layer="requirement",
                    line=sc["line"],
                )
                g.edge(rid, scid, "contains", "derived", f"{rel}:{sc['line']}")
            # 需求 → 代码：继承所属规格的功能域声明
            for dom in doms:
                for path, sym in domain_decl.get(dom, []):
                    target = f"SYM:{path}#{sym}" if sym else f"FILE:{path}"
                    g.edge(rid, target, "implemented_by", "derived", f"继承「{dom}」的实现声明")

    # ── 路由端点 ──
    routes = scope["routes"]
    _file_node(g, routes["urls"])
    for ep in parse_endpoints(routes):
        eid = f"API:{routes['prefix']}{ep['literal']}"
        g.node(
            eid,
            "endpoint",
            f"{routes['prefix']}{ep['literal']}",
            {"type": "route", "path": routes["urls"], "literal": ep["literal"]},
            layer="code",
            subtitle=f"→ {ep['view']}",
        )
        g.edge(f"FILE:{routes['urls']}", eid, "exposes", "derived", "urls.py 路由表")
        if symbol_exists(routes["views"], ep["view"]):
            g.edge(
                f"SYM:{routes['views']}#{ep['view']}",
                eid,
                "serves",
                "derived",
                f"{routes['views']} 的 {ep['view']}",
            )

    # ── 数据表 ──
    for t in scope.get("tables", []):
        tnode = f"TBL:{t['name']}"
        g.node(
            tnode,
            "table",
            t["name"],
            {"type": "db_table", "name": t["name"]},
            layer="code",
            subtitle=t.get("note", ""),
        )
        for path, sym in t.get("writes", []):
            g.edge(f"SYM:{path}#{sym}", tnode, "writes", "declared", "声明为唯一写口")
        for path, sym in t.get("reads", []):
            g.edge(f"SYM:{path}#{sym}", tnode, "reads", "declared", "声明为读取方")

    # ── 测试 ──
    for t in scan_tests(scope["tests"]):
        tid = f"TEST:{t['path']}"
        resolved = t["target"] in spec_ids if t["target"] else False
        g.node(
            tid,
            "test",
            t["path"].split("/")[-1],
            {"type": "file", "path": t["path"]},
            layer="test",
            subtitle=f"{t['case_count']} 个用例",
            case_count=t["case_count"],
            anchor_target=t["target"],
            anchor_style=t["anchor_style"],
            anchor_resolved=resolved,
            header_change=t["header_change"],
        )
        if t["target"] and resolved:
            g.edge(tid, spec_ids[t["target"]], "verifies", "declared", f"文件头声明 {t['target']}")

    return {
        "schema_version": SCHEMA_VERSION,
        "scope": {
            "name": scope["name"],
            "id": scope["id"],
            "entry": scope["prd"],
            "granularity": scope.get("granularity", ""),
        },
        "generated_at": datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds"),
        "source_rev": git_rev(),
        "nodes": list(g.nodes.values()),
        "edges": g.edges,
        "_declared_specs": prd["declared_specs"],
    }


# ── 6. 锚点重放 + 健康度 ────────────────────────────────────


def check_anchor(anchor: dict) -> tuple[bool, str]:
    at = anchor.get("type")
    if at == "file":
        ok = exists(anchor["path"])
        return ok, "文件存在" if ok else f"文件不存在: {anchor['path']}"
    if at == "md_heading":
        p, h = anchor["path"], anchor["heading"]
        if not exists(p):
            return False, f"文件不存在: {p}"
        ok = h in read(p).splitlines()
        return ok, "标题命中" if ok else f"标题已改/删除: {h}"
    if at == "symbol":
        p, n = anchor["path"], anchor["name"]
        if not exists(p):
            return False, f"文件不存在: {p}"
        ok = symbol_exists(p, n)
        return ok, "符号存在" if ok else f"符号已改名/删除: {n}"
    if at == "route":
        p, lit = anchor["path"], anchor["literal"]
        if not exists(p):
            return False, f"文件不存在: {p}"
        ok = f'"{lit}"' in read(p)
        return ok, "路由字面量命中" if ok else f"路由已改: {lit}"
    if at == "db_table":
        return True, "内置表（Django auth.User 决定，不随本仓迁移变化）"
    return False, f"未知锚点类型: {at}"


def compute_health(graph: dict) -> dict:
    nodes = graph["nodes"]
    edges = graph["edges"]
    declared = set(graph.pop("_declared_specs", []))

    broken: list[dict] = []
    for n in nodes:
        ok, detail = check_anchor(n["anchor"])
        n["anchor_ok"] = ok
        n["anchor_detail"] = detail
        if not ok:
            broken.append({"node": n["id"], "title": n["title"], "detail": detail})

    has_out = {(e["from"], e["type"]) for e in edges}
    has_in = {(e["to"], e["type"]) for e in edges}

    orphan_reqs = [
        {"node": n["id"], "title": n["title"], "spec": n["id"].split(":")[1].split("#")[0]}
        for n in nodes
        if n["kind"] == "requirement" and (n["id"], "implemented_by") not in has_out
    ]
    verified_specs = {e["to"].split(":", 1)[1] for e in edges if e["type"] == "verifies"}
    unverified_reqs = [
        {"node": n["id"], "title": n["title"], "spec": n["id"].split(":")[1].split("#")[0]}
        for n in nodes
        if n["kind"] == "requirement" and n["id"].split(":")[1].split("#")[0] not in verified_specs
    ]
    orphan_specs = [
        {"title": n["title"], "registered_in_prd": n["title"] in declared}
        for n in nodes
        if n["kind"] == "spec" and (n["id"], "specified_by") not in has_in
    ]

    tests = [n for n in nodes if n["kind"] == "test"]
    unanchored_tests = [
        {
            "title": n["title"],
            "path": n["anchor"]["path"],
            "case_count": n["case_count"],
            "anchor_target": n["anchor_target"],
            "anchor_style": n["anchor_style"],
            "reason": "未声明规格锚点"
            if not n["anchor_target"]
            else f"锚点指向不存在的规格: {n['anchor_target']}",
        }
        for n in tests
        if not n["anchor_resolved"]
    ]
    for t in tests:
        if t["anchor_target"] and not t["anchor_resolved"]:
            broken.append(
                {
                    "node": t["id"],
                    "title": t["title"],
                    "detail": f"文件头锚点指向不存在的规格: {t['anchor_target']}"
                    f"（写法 {t['anchor_style']}）",
                }
            )

    styles: dict[str, int] = {}
    for t in tests:
        key = t["anchor_style"] or "无锚点"
        styles[key] = styles.get(key, 0) + 1
    stale_headers = [
        {
            "title": t["title"],
            "change": t["header_change"],
            "resolved_spec": t["anchor_target"],
            "detail": f"文件头写 OpenSpec: {t['header_change']}（变更单），"
            f"实际守护规格 {t['anchor_target']}",
        }
        for t in tests
        if t["header_change"]
    ]

    kinds: dict[str, int] = {}
    for n in nodes:
        kinds[n["kind"]] = kinds.get(n["kind"], 0) + 1

    return {
        "node_kinds": kinds,
        "requirement_total": kinds.get("requirement", 0),
        "requirement_implemented": kinds.get("requirement", 0) - len(orphan_reqs),
        "requirement_verified_by_spec": kinds.get("requirement", 0) - len(unverified_reqs),
        "broken_anchors": broken,
        "orphan_requirements": orphan_reqs,
        "unverified_requirements": unverified_reqs,
        "orphan_specs": orphan_specs,
        "unanchored_tests": unanchored_tests,
        "anchor_styles": styles,
        "stale_header_anchors": stale_headers,
        "test_files": len(tests),
        "test_cases": sum(n["case_count"] for n in tests),
        "unanchored_test_cases": sum(n["case_count"] for n in unanchored_tests),
    }


# ── 7. 结构自检（工具必须产出合法数据） ─────────────────────


def verify_structure(graph: dict) -> list[str]:
    """图自身的自洽性：边两端必须存在、健康度计数必须与节点表一致。

    这**不是**需求-代码规则检查（本变更明确不做断锚门禁），只是"生成器不能吐坏数据"。
    """
    problems: list[str] = []
    ids = {n["id"] for n in graph["nodes"]}
    if len(ids) != len(graph["nodes"]):
        problems.append("节点 id 有重复")
    for e in graph["edges"]:
        if e["from"] not in ids:
            problems.append(f"边 {e['id']} 的起点不存在: {e['from']}")
        if e["to"] not in ids:
            problems.append(f"边 {e['id']} 的终点不存在: {e['to']}")
    for n in graph["nodes"]:
        if "anchor_ok" not in n:
            problems.append(f"节点 {n['id']} 未重放锚点")
    h = graph.get("health") or {}
    if h.get("requirement_total") != h.get("node_kinds", {}).get("requirement", -1):
        problems.append("健康度：需求总数与节点表不一致")
    return problems


# ── 8. 渲染页面 ─────────────────────────────────────────────


def render(template: str, graph: dict, out_path: Path) -> int:
    html = (TEMPLATES / template).read_text(encoding="utf-8")
    if PLACEHOLDER not in html:
        raise SystemExit(f"模板缺少 {PLACEHOLDER} 占位符: {template}")
    payload = json.dumps(graph, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    out_path.write_text(html.replace(PLACEHOLDER, payload), encoding="utf-8")
    return out_path.stat().st_size


# ── 9. 报告 ─────────────────────────────────────────────────


def print_report(graph: dict, quiet: bool) -> None:
    h = graph["health"]
    if quiet:
        print(
            f"[{graph['scope']['name']}] 节点 {len(graph['nodes'])} · 边 {len(graph['edges'])} · "
            f"需求 {h['requirement_total']}（有实现 {h['requirement_implemented']} / "
            f"有测试 {h['requirement_verified_by_spec']}）· 断锚 {len(h['broken_anchors'])}"
        )
        return
    print(f"范围 {graph['scope']['name']} · rev {graph['source_rev']}")
    print(f"  节点 {len(graph['nodes'])} · 边 {len(graph['edges'])}")
    print(f"  节点构成: {h['node_kinds']}")
    print(
        f"[覆盖] 需求 {h['requirement_total']} 条 · 已声明实现 {h['requirement_implemented']} · "
        f"有测试锚点守护 {h['requirement_verified_by_spec']}"
    )
    print(
        f"[测试] 测试文件 {h['test_files']} 个 / 用例 {h['test_cases']} 条 · "
        f"其中未挂锚点 {h['unanchored_test_cases']} 条"
    )
    print(f"[锚点写法] {h['anchor_styles']}")
    for label, key in (
        ("断锚", "broken_anchors"),
        ("孤儿需求（无实现声明）", "orphan_requirements"),
        ("未验收需求（无测试锚点）", "unverified_requirements"),
        ("孤儿规格（PRD 未登记）", "orphan_specs"),
        ("未归锚测试", "unanchored_tests"),
        ("文件头锚点指向变更单（已归档）", "stale_header_anchors"),
    ):
        rows = h[key]
        print(f"[{label}] {len(rows)}")
        for r in rows[:6]:
            print(
                f"    · {r.get('title') or r.get('node')} — {r.get('detail') or r.get('reason') or ''}"
            )
        if len(rows) > 6:
            print(f"    … 另有 {len(rows) - 6} 条")


# ── 10. 主流程 ──────────────────────────────────────────────


def main() -> int:
    ap = argparse.ArgumentParser(description="生成需求 × 代码 关系图（JSON + 工作台页 + 文档页）")
    ap.add_argument("--scope", default="", help="只处理指定 scope id（默认全部）")
    ap.add_argument(
        "--only",
        default="all",
        choices=["all", "json", "workbench", "doc"],
        help="只产出指定形态（默认 all：JSON + 工作台页 + 文档页）",
    )
    ap.add_argument("--out-dir", default="", help="产物目录（默认取声明文件的 out_dir）")
    ap.add_argument("--quiet", action="store_true", help="只打印每行结论")
    args = ap.parse_args()

    scopes, default_out = load_declarations()
    if args.scope:
        scopes = [s for s in scopes if s["id"] == args.scope]
        if not scopes:
            print(f"没有这个 scope: {args.scope}")
            return 1

    out_dir = Path(args.out_dir) if args.out_dir else default_out
    if not out_dir.is_absolute():
        out_dir = (ROOT / out_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)

    problems: list[str] = []
    for scope in scopes:
        graph = build_scope(scope)
        graph["health"] = compute_health(graph)
        problems += [f"[{scope['id']}] {p}" for p in verify_structure(graph)]

        names = scope["outputs"]
        written: list[str] = []
        if args.only in ("all", "json"):
            p = out_dir / names["json"]
            p.write_text(json.dumps(graph, ensure_ascii=False, indent=2), encoding="utf-8")
            written.append(f"{p.name} ({p.stat().st_size / 1024:.0f} KB)")
        if args.only in ("all", "workbench"):
            kb = render("workbench.html", graph, out_dir / names["workbench"])
            written.append(f"{names['workbench']} ({kb / 1024:.0f} KB)")
        if args.only in ("all", "doc"):
            kb = render("doc.html", graph, out_dir / names["doc"])
            written.append(f"{names['doc']} ({kb / 1024:.0f} KB)")

        print_report(graph, args.quiet)
        for w in written:
            print(f"  ↳ 已写出 {w}")
        print("─" * 64)

    if problems:
        print("结构自检失败：")
        for p in problems:
            print(f"  ✗ {p}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
