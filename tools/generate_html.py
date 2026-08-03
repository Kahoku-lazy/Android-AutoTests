"""
HTML 生成器 v2 — 支持滚轮切换层级 + 元素树 + 右键菜单
输出: phone_ui.html（自包含，可直接在浏览器打开）
"""

import base64
import json
import os
import sys

if sys.platform == "win32":
    import io

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

OUT_DIR = os.path.dirname(os.path.abspath(__file__))

PHONE_W = 1440
PHONE_H = 3040
DISPLAY_W = 405
SCALE = DISPLAY_W / PHONE_W
DISPLAY_H = int(PHONE_H * SCALE)


def encode_image_base64(path: str) -> str:
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def flatten_tree(nodes: list[dict], depth: int = 0) -> list[dict]:
    """递归展平，保留 children 引用"""
    result = []
    for node in nodes:
        node["depth"] = depth
        children = node.get("children", [])
        result.append(node)
        if children:
            result.extend(flatten_tree(children, depth + 1))
    return result


def build_parent_map(nodes: list[dict]) -> dict:
    """从展平列表构建 parent_id 映射"""
    pmap = {}
    # 两遍：先分配 _id，再遍历 children 建映射
    # 但 nodes 还没 _id。我们用 id(node) 做中间映射
    obj_to_nid = {id(n): i for i, n in enumerate(nodes)}
    for i, node in enumerate(nodes):
        for child in node.get("children", []):
            cid = obj_to_nid.get(id(child))
            if cid is not None:
                pmap[cid] = i
    return pmap


def class_short(class_name: str) -> str:
    return class_name.rsplit(".", 1)[-1] if "." in class_name else class_name


def esc(s: str) -> str:
    """HTML 属性转义"""
    return s.replace("&", "&amp;").replace('"', "&quot;").replace("<", "&lt;").replace(">", "&gt;")


def build_tree_html(nodes: list[dict], id_map: dict) -> str:
    """生成可折叠树 HTML"""
    items = []
    for node in nodes:
        nid = id_map[id(node)]
        cls = class_short(node.get("class", ""))
        text = node.get("text", "")
        desc = node.get("content_desc", "")
        rid = node.get("resource_id", "")

        # 标签：优先 text，其次 desc，再次 class 短名
        if text:
            label = f'"{text[:20]}"'
        elif desc:
            label = f'"{desc[:20]}"'
        elif rid:
            label = rid.split("/")[-1] if "/" in rid else rid[-20:]
        else:
            label = cls

        label_esc = esc(label)
        children = node.get("children", [])

        if children:
            items.append(f"""<li>
                <span class="tree-toggle" onclick="toggleTree(this)">[-]</span>
                <span class="tree-node" data-nid="{nid}" onclick="selectByTree({nid})" title="{esc(cls)}">{label_esc}</span>
                <ul>{build_tree_html(children, id_map)}</ul>
            </li>""")
        else:
            items.append(f"""<li>
                <span class="tree-leaf">·</span>
                <span class="tree-node" data-nid="{nid}" onclick="selectByTree({nid})" title="{esc(cls)}">{label_esc}</span>
            </li>""")
    return "\n".join(items)


def generate_html(hierarchy: dict, screenshot_b64: str) -> str:
    # ---- 1. 展平并分配 ID ----
    all_nodes = flatten_tree(hierarchy.get("children", [hierarchy]))
    id_map = {id(n): i for i, n in enumerate(all_nodes)}
    for i, node in enumerate(all_nodes):
        node["_id"] = i

    visible_nodes = [
        n
        for n in all_nodes
        if n.get("rect", {}).get("width", 0) > 0 and n.get("rect", {}).get("height", 0) > 0
    ]
    max_depth = max((n["depth"] for n in all_nodes), default=0)

    print(f"  总节点: {len(all_nodes)}, 可见节点: {len(visible_nodes)}, 最大深度: {max_depth}")

    # ---- 2. 生成元素 div + 父级映射 ----
    parent_map = build_parent_map(visible_nodes)
    element_divs = []
    for node in visible_nodes:
        r = node["rect"]
        left = r["x"] * SCALE
        top = r["y"] * SCALE
        w = r["width"] * SCALE
        h = r["height"] * SCALE
        nid = node["_id"]
        z = nid + 1  # 全局 DOM 顺序 = z-index，后面的元素（如底栏）自然覆盖前面的重叠区域
        pid = parent_map.get(nid, -1)
        hue = (node["depth"] * 37) % 360
        border_color = f"hsl({hue}, 70%, 55%)"

        t = node.get("text", "")
        d = node.get("content_desc", "")
        rid = node.get("resource_id", "")
        full_cls = node.get("class", "")
        idx = node.get("index", "")
        tooltip = " | ".join(
            filter(
                None,
                [
                    f'Text: "{t}"' if t else "",
                    f'Desc: "{d}"' if d else "",
                    f"Class: {class_short(full_cls)}",
                    f"ID: {rid}" if rid else "",
                ],
            )
        )

        # 文字标签内容
        if t:
            label = t[:8] + (".." if len(t) > 8 else "")
        elif d:
            label = d[:8] + (".." if len(d) > 8 else "")
        elif rid:
            label = rid.split("/")[-1][:10] if "/" in rid else rid[:10]
        else:
            label = class_short(full_cls)[:10]
        label_esc = esc(label)

        element_divs.append(f"""<div class="el"
 style="left:{left:.1f}px;top:{top:.1f}px;width:{w:.1f}px;height:{h:.1f}px;z-index:{z};border-color:{border_color}"
 data-nid="{nid}"
 data-pid="{pid}"
 data-d="{node["depth"]}"
 data-t="{esc(t)}"
 data-desc="{esc(d)}"
 data-rid="{esc(rid)}"
 data-fullcls="{esc(full_cls)}"
 data-shortcls="{esc(class_short(full_cls))}"
 data-idx="{esc(idx)}"
 data-bounds="[{r["x"]},{r["y"]}][{r["x"] + r["width"]},{r["y"] + r["height"]}]"
 data-pkg="{esc(node.get("package", ""))}"
 data-clickable="{node.get("clickable", False)}"
 data-enabled="{node.get("enabled", False)}"
 data-scrollable="{node.get("scrollable", False)}"
 data-checkable="{node.get("checkable", False)}"
 data-checked="{node.get("checked", False)}"
 title="{esc(tooltip)}"><span class="el-label">{label_esc}</span></div>""")

    # ---- 3. 元素树 HTML ----
    root_children = hierarchy.get("children", [hierarchy])
    tree_html = build_tree_html(root_children, id_map)

    # ---- 4. 完整 HTML 模板 ----
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Phone UI Inspector</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Quicksand:wght@500;600;700&display=swap');

:root {{
    --bg: #f5f0f5;
    --glass-bg: rgba(255,255,255,0.5);
    --glass-border: rgba(255,255,255,0.6);
    --text-primary: #3a3450;
    --text-secondary: #8a8098;
    --text-muted: #b0a8b8;
    --accent-pink: #ffafcc;
    --accent-blue: #a2d2ff;
    --accent-green: #bde0fe;
    --accent-lavender: #cdb4db;
    --shadow-soft: 0 8px 32px rgba(31,38,135,0.08);
    --shadow-card: 0 4px 16px rgba(0,0,0,0.04);
}}

* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{
    font-family: 'Quicksand','Segoe UI','PingFang SC','Microsoft YaHei',sans-serif;
    background: linear-gradient(45deg, #ffc8dd, #bde0fe, #a2d2ff, #e2ece9);
    background-size: 300% 300%;
    animation: gradientBG 20s ease infinite;
    color: var(--text-primary);
    display: flex; min-height: 100vh;
}}

@keyframes gradientBG {{
    0% {{ background-position: 0% 50%; }}
    50% {{ background-position: 100% 50%; }}
    100% {{ background-position: 0% 50%; }}
}}

.blob {{
    position: fixed; border-radius: 50%; filter: blur(80px);
    z-index: 0; opacity: 0.6; pointer-events: none;
}}
.blob-1 {{ top: -8%; left: -5%; width: 350px; height: 350px; background: #ffafcc; }}
.blob-2 {{ bottom: -10%; right: -8%; width: 280px; height: 280px; background: #a2d2ff; }}
.blob-3 {{ top: 50%; left: 55%; width: 200px; height: 200px; background: #cdb4db; }}

/* ===== 左侧：手机屏幕 ===== */
#phone-container {{
    flex-shrink: 0; padding: 24px;
    display: flex; justify-content: center; align-items: flex-start;
    position: sticky; top: 0; z-index: 1;
}}
#phone-screen {{
    position: relative;
    width: {DISPLAY_W}px; height: {DISPLAY_H}px;
    border-radius: 24px; overflow: hidden;
    background: #fff;
    border: 2px solid rgba(255,255,255,0.7);
    box-shadow: var(--shadow-soft), 0 0 0 6px rgba(255,255,255,0.25);
    cursor: crosshair;
}}
#phone-screen img {{
    display: block; width: 100%; height: 100%;
    object-fit: contain; pointer-events: none; user-select: none;
}}

/* ===== 覆盖元素 ===== */
.el {{
    position: absolute; border: 1px solid;
    background: transparent; cursor: pointer;
    transition: background 0.12s, border-color 0.12s;
}}
.el.dim {{ background: rgba(180,180,200,0.06); }}
.el-label {{
    position: absolute; top: 0; left: 0;
    background: rgba(58,52,80,0.7); color: #fff;
    font-size: 7px; padding: 1px 4px; border-radius: 0 0 4px 0;
    pointer-events: none; white-space: nowrap;
    max-width: 100%; overflow: hidden; text-overflow: ellipsis;
    line-height: 1.4; font-weight: 600;
}}
.el:hover {{ background: rgba(255,175,204,0.2) !important; border-color: #ffafcc !important; border-width: 2px; z-index: 9999 !important; }}
.el:hover .el-label {{ background: #ffafcc; color: #3a3450; font-weight: 700; }}
.el.cycle-active {{ background: rgba(162,210,255,0.25) !important; border-color: #a2d2ff !important; border-width: 2px; z-index: 9997 !important; }}
.el.cycle-active .el-label {{ background: #a2d2ff; color: #3a3450; font-weight: 700; }}
.el.selected {{ background: rgba(205,180,219,0.3) !important; border-color: #cdb4db !important; border-width: 3px; z-index: 9998 !important; box-shadow: 0 0 14px rgba(205,180,219,0.5), inset 0 0 12px rgba(205,180,219,0.15); animation: pulse 2s ease-in-out infinite; }}
.el.selected .el-label {{ background: #cdb4db; color: #3a3450; font-weight: 700; }}
@keyframes pulse {{
    0%, 100% {{ box-shadow: 0 0 12px rgba(205,180,219,0.5), inset 0 0 10px rgba(205,180,219,0.1); }}
    50% {{ box-shadow: 0 0 22px rgba(205,180,219,0.7), inset 0 0 18px rgba(205,180,219,0.25); }}
}}

/* ===== 浮动标记 ===== */
#hover-badge {{
    display: none; position: absolute;
    background: var(--accent-blue); color: #3a3450;
    font-size: 10px; font-weight: 700;
    padding: 3px 8px; border-radius: 12px;
    pointer-events: none; white-space: nowrap;
    z-index: 99999;
}}

/* ===== 右键菜单 ===== */
#context-menu {{
    display: none; position: absolute;
    background: rgba(255,255,255,0.92);
    border: 1px solid rgba(0,0,0,0.08);
    border-radius: 12px; min-width: 220px; max-height: 360px; overflow-y: auto;
    z-index: 99999; box-shadow: 0 4px 24px rgba(0,0,0,0.1);
    font-size: 12px; padding: 4px 0;
}}
#context-menu .ctx-item {{
    padding: 7px 14px; cursor: pointer;
    border-bottom: 1px solid rgba(0,0,0,0.04);
    display: flex; justify-content: space-between; align-items: center;
    color: var(--text-primary);
}}
#context-menu .ctx-item:hover {{ background: rgba(162,210,255,0.3); }}
#context-menu .ctx-item .ctx-label {{ color: var(--text-primary); font-weight: 500; }}
#context-menu .ctx-item .ctx-depth {{ color: var(--text-muted); font-size: 10px; }}

/* ===== 右侧面板 ===== */
#panel {{
    flex: 1; min-width: 340px; max-width: 520px;
    height: 100vh; overflow-y: auto;
    display: flex; flex-direction: column;
    position: relative; z-index: 1;
    background: rgba(255,255,255,0.25);
}}
#panel-header {{
    padding: 16px 20px 0;
    position: sticky; top: 0; z-index: 10;
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border-bottom: 1px solid rgba(0,0,0,0.06);
}}
#panel-header h2 {{ font-size: 20px; color: var(--text-primary); margin-bottom: 6px; font-weight: 700; }}
#stats {{ font-size: 11px; color: var(--text-secondary); margin-bottom: 10px; font-weight: 500; }}
#stats span {{ color: #4a80c0; background: rgba(162,210,255,0.3); padding: 2px 6px; border-radius: 6px; font-weight: 700; }}

#toolbar {{
    display: flex; gap: 6px; margin-bottom: 10px; flex-wrap: wrap;
}}
#toolbar button {{
    background: rgba(255,255,255,0.65);
    color: var(--text-primary);
    border: 1px solid rgba(0,0,0,0.08); padding: 5px 12px; border-radius: 20px;
    cursor: pointer; font-size: 11px; font-weight: 600;
    transition: all 0.15s;
}}
#toolbar button:hover {{ background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}
#toolbar button.active {{ background: var(--accent-blue); border-color: transparent; color: #3a3450; }}

.info-card {{
    background: rgba(255,255,255,0.55);
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 14px; padding: 12px 14px; margin-bottom: 8px; font-size: 13px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.03);
}}
.info-card .label {{
    color: var(--text-secondary); font-size: 10px; text-transform: uppercase;
    letter-spacing: 0.8px; margin-bottom: 3px; font-weight: 600;
}}
.info-card .value {{
    color: var(--text-primary); word-break: break-all;
    font-family: 'Cascadia Code','Consolas',monospace; font-size: 12px; line-height: 1.5;
    background: rgba(0,0,0,0.02); padding: 4px 8px; border-radius: 6px;
}}
.info-card .value.empty {{ color: var(--text-muted); font-style: italic; }}
.info-card .tag {{
    display: inline-block; padding: 3px 8px; border-radius: 20px;
    font-size: 10px; margin: 2px 3px 2px 0; font-weight: 600;
}}
.info-card .tag.on {{ background: rgba(184,232,198,0.6); color: #1a5c2a; }}
.info-card .tag.off {{ background: rgba(255,192,203,0.5); color: #7a1c2b; }}
.highlight {{ color: #7c5cbf; font-weight: 600; }}

/* ===== 元素树 ===== */
#tree-section {{
    flex: 1; overflow-y: auto; padding: 8px 12px 16px;
    margin: 8px 12px;
    background: rgba(255,255,255,0.55);
    border-radius: 14px; border: 1px solid rgba(0,0,0,0.06);
}}
#tree-section h3 {{
    font-size: 13px; color: var(--text-secondary); margin: 4px 0 8px;
    position: sticky; top: 0; padding: 4px 0; font-weight: 700;
    background: transparent;
}}
#tree ul {{ list-style: none; padding-left: 16px; }}
#tree li {{ margin: 2px 0; }}
#tree .tree-toggle, #tree .tree-leaf {{
    display: inline-block; width: 18px; cursor: pointer;
    color: var(--text-secondary); font-size: 11px; user-select: none;
    font-family: monospace;
}}
#tree .tree-node {{
    cursor: pointer; font-size: 12px; color: var(--text-primary);
    padding: 3px 8px; border-radius: 6px; font-weight: 500;
    transition: all 0.1s; display: inline-block;
}}
#tree .tree-node:hover {{ background: rgba(162,210,255,0.3); }}
#tree .tree-node.active {{ background: var(--accent-lavender); color: #3a3450; font-weight: 700; }}

.locator-card {{ background: rgba(255,255,255,0.6) !important; border-color: rgba(162,210,255,0.4) !important; }}
.loc-table {{ width: 100%; border-collapse: collapse; font-size: 11px; margin: 8px 0 4px; }}
.loc-table th {{ text-align: left; color: var(--text-secondary); font-size: 10px; text-transform: uppercase; padding: 4px 6px; border-bottom: 1px solid rgba(0,0,0,0.06); font-weight: 600; }}
.loc-table td {{ padding: 4px 6px; border-bottom: 1px solid rgba(0,0,0,0.03); vertical-align: middle; }}
.loc-type {{ color: var(--text-secondary); white-space: nowrap; width: 1%; font-size: 10px; font-weight: 600; }}
.loc-xpath {{ color: #6b5b9a; font-family: 'Cascadia Code','Consolas',monospace; font-size: 11px; word-break: break-all; cursor: pointer; }}
.loc-xpath:hover {{ background: rgba(162,210,255,0.2); border-radius: 4px; }}
.loc-xpath.copied {{ background: rgba(184,232,198,0.4); }}
.loc-count {{ text-align: center; width: 1%; }}
.loc-badge {{ display: inline-block; min-width: 22px; padding: 1px 6px; border-radius: 20px; text-align: center; font-size: 10px; font-weight: 700; }}
.loc-badge.unique {{ background: rgba(184,232,198,0.55); color: #1a5c2a; }}
.loc-badge.good {{ background: rgba(184,232,198,0.4); color: #2a7a3a; }}
.loc-badge.fair {{ background: rgba(255,220,180,0.5); color: #8a5a1a; }}
.loc-badge.many {{ background: rgba(255,192,203,0.5); color: #7a1c2b; }}
.loc-row.loc-unique {{ background: rgba(184,232,198,0.08); }}
.loc-hint {{ font-size: 10px; color: var(--text-muted); margin-top: 4px; font-style: italic; }}

.parent-btn {{
    background: rgba(255,255,255,0.55); color: var(--text-primary);
    border: 1px solid rgba(0,0,0,0.08); padding: 6px 16px; border-radius: 20px;
    cursor: pointer; font-size: 11px; font-weight: 600;
}}
.parent-btn:hover {{ background: #fff; box-shadow: 0 2px 8px rgba(0,0,0,0.06); }}

.action-btn {{
    padding: 7px 16px; border-radius: 20px; cursor: pointer;
    font-size: 11px; font-weight: 700; border: 1px solid;
    transition: all 0.15s; margin-right: 6px; margin-bottom: 4px;
}}
.action-btn.tap {{ background: rgba(184,232,198,0.5); color: #1a5c2a; border-color: rgba(184,232,198,0.7); }}
.action-btn.tap:hover {{ background: rgba(184,232,198,0.8); }}
.action-btn.input {{ background: rgba(162,210,255,0.5); color: #1c4a7a; border-color: rgba(162,210,255,0.7); }}
.action-btn.input:hover {{ background: rgba(162,210,255,0.8); }}
.action-btn.screenshot {{ background: rgba(255,175,204,0.5); color: #5a2a4a; border-color: rgba(255,175,204,0.7); }}
.action-btn.screenshot:hover {{ background: rgba(255,175,204,0.8); }}
.action-btn:disabled {{ opacity: 0.4; cursor: not-allowed; }}

.input-row {{ display: flex; gap: 6px; margin-top: 4px; align-items: center; }}
.input-row input {{
    flex: 1; background: rgba(255,255,255,0.7); color: var(--text-primary);
    border: 1px solid rgba(0,0,0,0.1); border-radius: 10px;
    padding: 6px 12px; font-size: 12px; outline: none;
}}
.input-row input:focus {{ border-color: var(--accent-blue); box-shadow: 0 0 0 3px rgba(162,210,255,0.2); }}
.input-row button {{
    background: var(--accent-blue); color: #3a3450; border: none;
    padding: 6px 14px; border-radius: 20px; cursor: pointer; font-size: 11px; font-weight: 700;
}}

.toast {{
    position: fixed; bottom: 30px; left: 50%; transform: translateX(-50%);
    background: rgba(255,255,255,0.9); color: #3a3450;
    backdrop-filter: blur(16px); -webkit-backdrop-filter: blur(16px);
    padding: 10px 24px; border-radius: 30px;
    font-size: 13px; font-weight: 700; z-index: 99999;
    pointer-events: none; opacity: 0; transition: opacity 0.3s;
    border: 1px solid rgba(0,0,0,0.06);
    box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}}
.toast.show {{ opacity: 1; }}
.toast.error {{ background: rgba(255,192,203,0.9); color: #7a1c2b; }}

::-webkit-scrollbar {{ width: 5px; }}
::-webkit-scrollbar-track {{ background: transparent; }}
::-webkit-scrollbar-thumb {{ background: rgba(0,0,0,0.12); border-radius: 3px; }}

.empty {{ color: var(--text-muted); font-size: 13px; text-align: center; margin-top: 30px; line-height: 1.8; font-weight: 500; }}
</style>
</head>
<body>

<!-- ====== 背景装饰球 ====== -->
<div class="blob blob-1"></div>
<div class="blob blob-2"></div>
<div class="blob blob-3"></div>

<!-- ====== 手机屏幕 ====== -->
<div id="phone-container">
    <div id="phone-screen">
        <img src="data:image/png;base64,{screenshot_b64}" alt="screenshot" draggable="false">
        {"".join(element_divs)}
        <div id="hover-badge"></div>
        <div id="context-menu"></div>
    </div>
</div>

<!-- ====== 右侧面板 ====== -->
<div id="panel">
    <div id="panel-header">
        <h2>UI Inspector</h2>
        <div id="stats">
            可见元素: <span>{len(visible_nodes)}</span> |
            总节点: <span>{len(all_nodes)}</span> |
            最深: <span>{max_depth}</span>
        </div>
        <div id="toolbar">
            <button onclick="setMode('all')" id="btn-all" class="active">全部边框</button>
            <button onclick="setMode('clickable')" id="btn-clickable">仅可点击</button>
            <button onclick="setMode('text')" id="btn-text">有文本的</button>
            <button onclick="setMode('hover')" id="btn-hover">仅悬停</button>
            <button onclick="clearSelection()">清除选择</button>
        </div>
        <div id="detail-cards"></div>
    </div>
    <div id="tree-section">
        <h3>Element Tree</h3>
        <div id="tree"><ul>{tree_html}</ul></div>
    </div>
</div>

<script>
// ===== 全局状态 =====
let mode = 'all';
let selectedNid = null;
let cycleStack = [];     // 当前鼠标位置下所有元素 nid 列表 (depth 降序)
let cycleIdx = -1;       // 当前高亮的元素索引
let mouseX = 0, mouseY = 0;

const screen = document.getElementById('phone-screen');
const badge = document.getElementById('hover-badge');
const ctxMenu = document.getElementById('context-menu');
const detailCards = document.getElementById('detail-cards');

// ===== 工具函数 =====
function getElsAtPoint(x, y) {{
    const els = document.elementsFromPoint(x, y);
    return els.filter(e => e.classList.contains('el') && e.style.display !== 'none');
}}

function nidFromEl(el) {{ return parseInt(el.dataset.nid); }}

// ===== 模式切换 =====
function setMode(m) {{
    mode = m;
    document.querySelectorAll('#toolbar button').forEach(b => b.classList.remove('active'));
    document.getElementById('btn-' + m).classList.add('active');
    refreshVisibility();
}}

function refreshVisibility() {{
    document.querySelectorAll('.el').forEach(el => {{
        if (mode === 'all') {{
            el.style.display = ''; el.classList.add('dim');
        }} else if (mode === 'clickable') {{
            const ok = el.dataset.clickable === 'True';
            el.style.display = ok ? '' : 'none';
            if (ok) el.classList.add('dim');
        }} else if (mode === 'text') {{
            const hasText = el.dataset.t && el.dataset.t.trim() !== '';
            el.style.display = hasText ? '' : 'none';
            if (hasText) el.classList.add('dim');
        }} else if (mode === 'hover') {{
            el.style.display = ''; el.classList.remove('dim');
        }}
    }});
    // 恢复选中
    if (selectedNid !== null) {{
        const sel = document.querySelector(`.el[data-nid="${{selectedNid}}"]`);
        if (sel) sel.classList.add('selected');
    }}
}}

// ===== 鼠标：悬停追踪 + 滚轮切换 =====
screen.addEventListener('mousemove', function(e) {{
    mouseX = e.clientX; mouseY = e.clientY;
    const rect = screen.getBoundingClientRect();
    const rx = e.clientX - rect.left;
    const ry = e.clientY - rect.top;

    // 重置滚轮状态（鼠标移动了位置）
    if (cycleStack.length > 0) {{
        const lastEl = document.querySelector(`.el[data-nid="${{cycleStack[cycleIdx]}}"]`);
        const moved = !lastEl || !isPointInEl(lastEl, rx, ry);
        if (moved) {{
            clearCycle();
        }}
    }}

    // 计算当前位置下有多少元素
    const els = getElsAtPoint(e.clientX, e.clientY);
    if (els.length > 1) {{
        badge.style.display = 'block';
        badge.style.left = (rx + 10) + 'px';
        badge.style.top = (ry - 22) + 'px';
        badge.textContent = els.length + ' layers';
        badge.style.background = '#0f6';
    }} else if (els.length === 1 && !els[0].classList.contains('selected') && !els[0].classList.contains('cycle-active')) {{
        badge.style.display = 'block';
        badge.style.left = (rx + 10) + 'px';
        badge.style.top = (ry - 22) + 'px';
        badge.textContent = '1 layer';
        badge.style.background = '#666';
    }} else {{
        badge.style.display = 'none';
    }}
}});

screen.addEventListener('wheel', function(e) {{
    const els = getElsAtPoint(e.clientX, e.clientY);
    if (els.length === 0) return;
    e.preventDefault();

    // 构建或更新 cycleStack（按 z-index 降序 = 视觉最顶层在前）
    if (cycleStack.length === 0 || !arraysEqual(cycleStack, els.map(nidFromEl))) {{
        clearCycle();
        cycleStack = els.map(nidFromEl);
        cycleStack.sort((a, b) => {{
            const za = parseInt(document.querySelector(`.el[data-nid="${{a}}"]`)?.style.zIndex || 0);
            const zb = parseInt(document.querySelector(`.el[data-nid="${{b}}"]`)?.style.zIndex || 0);
            return zb - za; // z-index 高的在前（视觉顶层）
        }});
        cycleIdx = 0;
    }} else {{
        cycleIdx = (cycleIdx + (e.deltaY > 0 ? 1 : -1) + cycleStack.length) % cycleStack.length;
    }}

    // 高亮当前 cycle 元素
    document.querySelectorAll('.el.cycle-active').forEach(e => e.classList.remove('cycle-active'));
    const cur = document.querySelector(`.el[data-nid="${{cycleStack[cycleIdx]}}"]`);
    if (cur) {{
        cur.classList.add('cycle-active');
        cur.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
    }}

    // 更新 badge
    badge.style.display = 'block';
    badge.style.background = '#0f6';
    badge.textContent = (cycleIdx + 1) + '/' + cycleStack.length;
    const rect = screen.getBoundingClientRect();
    badge.style.left = (mouseX - rect.left + 10) + 'px';
    badge.style.top = (mouseY - rect.top - 22) + 'px';
}}, {{ passive: false }});

function arraysEqual(a, b) {{
    if (a.length !== b.length) return false;
    const sa = [...a].sort();
    const sb = [...b].sort();
    return sa.every((v, i) => v === sb[i]);
}}

function clearCycle() {{
    document.querySelectorAll('.el.cycle-active').forEach(e => e.classList.remove('cycle-active'));
    cycleStack = [];
    cycleIdx = -1;
    badge.style.display = 'none';
}}

function isPointInEl(el, x, y) {{
    const l = parseFloat(el.style.left);
    const t = parseFloat(el.style.top);
    const w = parseFloat(el.style.width);
    const h = parseFloat(el.style.height);
    return x >= l && x <= l + w && y >= t && y <= t + h;
}}

// ===== 智能选择：在重叠元素中优选有文本/可点击/最小的元素 =====
function smartPick(els) {{
    if (els.length === 0) return null;
    if (els.length === 1) return els[0];
    // 评分：有文本 +10, 可点击 +5, 尺寸小 +3（越小越精确）
    const scored = els.map(el => {{
        let score = 0;
        if (el.dataset.t) score += 10;
        if (el.dataset.clickable === 'True') score += 5;
        const w = parseFloat(el.style.width) || 0;
        const h = parseFloat(el.style.height) || 0;
        const area = w * h;
        if (area > 0 && area < 5000) score += 3; // 小元素加分
        if (area > 50000) score -= 2;            // 大容器减分
        const zi = parseInt(el.style.zIndex || 0);
        score += zi * 0.01; // z-index 微加分（视觉顶层的优先）
        return {{ el, score }};
    }});
    scored.sort((a, b) => b.score - a.score);
    return scored[0].el;
}}

screen.addEventListener('click', function(e) {{
    // 如果正在 cycle 中，选择当前 cycle 元素
    if (cycleStack.length > 0 && cycleIdx >= 0) {{
        const el = document.querySelector(`.el[data-nid="${{cycleStack[cycleIdx]}}"]`);
        if (el) {{
            selectEl(el);
            clearCycle();
            return;
        }}
    }}
    // 使用智能选择
    const els = getElsAtPoint(e.clientX, e.clientY);
    const best = smartPick(els);
    if (best) selectEl(best);
    clearCycle();
}});

// ===== 右键菜单 =====
screen.addEventListener('contextmenu', function(e) {{
    e.preventDefault();
    const els = getElsAtPoint(e.clientX, e.clientY);
    if (els.length === 0) {{ ctxMenu.style.display = 'none'; return; }}

    const rect = screen.getBoundingClientRect();
    const rx = e.clientX - rect.left, ry = e.clientY - rect.top;

    // 智能排序：有文本/可点击/小元素优先
    const sorted = els.map(el => {{
        let sc = 0;
        if (el.dataset.t) sc += 10;
        if (el.dataset.clickable === 'True') sc += 5;
        const area = (parseFloat(el.style.width)||0) * (parseFloat(el.style.height)||0);
        if (area > 0 && area < 5000) sc += 3;
        if (area > 50000) sc -= 2;
        return {{ el, sc }};
    }}).sort((a, b) => b.sc - a.sc);

    let html = '';
    sorted.forEach(({{ el }}, i) => {{
        const nid = nidFromEl(el);
        const d = el.dataset.d;
        const cls = el.dataset.shortcls;
        const t = el.dataset.t;
        const desc = el.dataset.desc;
        const label = t || desc || cls || '(empty)';
        html += `<div class="ctx-item" onclick="selectElByNid(${{nid}});hideCtx()">
            <span class="ctx-label">${{i+1}}. ${{label.substring(0, 40)}}</span>
            <span class="ctx-depth">d:${{d}}</span>
        </div>`;
    }});

    ctxMenu.innerHTML = html;
    ctxMenu.style.display = 'block';
    ctxMenu.style.left = Math.min(rx + 4, {DISPLAY_W} - 230) + 'px';
    ctxMenu.style.top = Math.min(ry + 4, {DISPLAY_H} - 200) + 'px';
}});

document.addEventListener('click', function(e) {{
    if (!ctxMenu.contains(e.target)) ctxMenu.style.display = 'none';
}});

function hideCtx() {{ ctxMenu.style.display = 'none'; }}

// ===== 元素树点击 =====
function selectByTree(nid) {{
    const el = document.querySelector(`.el[data-nid="${{nid}}"]`);
    if (el) {{
        selectEl(el);
        el.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
    }}
}}

function toggleTree(sp) {{
    const ul = sp.parentElement.querySelector('ul');
    if (ul) {{
        const hide = ul.style.display !== 'none';
        ul.style.display = hide ? 'none' : '';
        sp.textContent = hide ? '[+]' : '[-]';
    }}
}}

// ===== 选中元素 & 显示信息 =====
function selectEl(el) {{
    document.querySelectorAll('.el.selected').forEach(e => e.classList.remove('selected'));
    el.classList.add('selected');
    selectedNid = nidFromEl(el);

    // 树节点高亮
    document.querySelectorAll('#tree .tree-node.active').forEach(n => n.classList.remove('active'));
    const treeNd = document.querySelector(`#tree .tree-node[data-nid="${{selectedNid}}"]`);
    if (treeNd) {{
        treeNd.classList.add('active');
        treeNd.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
        // 展开祖先
        let p = treeNd.closest('ul')?.parentElement;
        while (p && p.tagName === 'LI') {{
            const toggle = p.querySelector(':scope > .tree-toggle');
            const childUl = p.querySelector(':scope > ul');
            if (toggle && childUl && childUl.style.display === 'none') {{
                childUl.style.display = '';
                toggle.textContent = '▼';
            }}
            p = p.parentElement?.closest('li');
        }}
    }}

    showDetail(el);
}}

function selectElByNid(nid) {{
    const el = document.querySelector(`.el[data-nid="${{nid}}"]`);
    if (el) selectEl(el);
}}

function selectParent() {{
    if (selectedNid === null) return;
    const el = document.querySelector(`.el[data-nid="${{selectedNid}}"]`);
    if (!el) return;
    const pid = parseInt(el.dataset.pid);
    if (pid < 0) return;
    const parent = document.querySelector(`.el[data-nid="${{pid}}"]`);
    if (parent) {{
        selectEl(parent);
        parent.scrollIntoView({{ block: 'nearest', behavior: 'smooth' }});
    }}
}}

function updateParentBtn(el) {{
    const pid = parseInt(el.dataset.pid);
    const btn = document.getElementById('btn-parent');
    const hint = document.getElementById('parent-hint');
    if (pid >= 0) {{
        const parent = document.querySelector(`.el[data-nid="${{pid}}"]`);
        if (parent) {{
            btn.style.display = '';
            const pcls = parent.dataset.shortcls;
            const pt = parent.dataset.t;
            hint.textContent = pt ? `${{pcls}} "${{pt.substring(0,15)}}"` : pcls;
        }} else {{
            btn.style.display = 'none'; hint.textContent = '(root)';
        }}
    }} else {{
        btn.style.display = 'none'; hint.textContent = '(root)';
    }}
}}

// ===== XPath 定位器生成 =====
function genLocators(el) {{
    const full = el.dataset.fullcls;
    const rid = el.dataset.rid;
    const t = el.dataset.t;
    const desc = el.dataset.desc;
    const idx = parseInt(el.dataset.idx) || 0;
    const pkg = el.dataset.pkg;

    const locators = [];

    // 辅助：计数匹配某条件的元素个数
    const countMatch = (pred) => {{
        let n = 0;
        document.querySelectorAll('.el').forEach(e => {{ if (e.style.display !== 'none' && pred(e)) n++; }});
        return n;
    }};

    // 1) XPath by resource-id
    if (rid) {{
        const xp = `//${{full}}[@resource-id='${{rid}}']`;
        const cnt = countMatch(e => e.dataset.rid === rid && e.dataset.fullcls === full);
        locators.push({{ type: 'resource-id', xpath: xp, count: cnt }});
    }}

    // 2) XPath by text
    if (t) {{
        const xp = `//${{full}}[@text='${{t}}']`;
        const cnt = countMatch(e => e.dataset.t === t && e.dataset.fullcls === full);
        locators.push({{ type: 'text', xpath: xp, count: cnt }});
    }}

    // 3) XPath by content-desc
    if (desc) {{
        const xp = `//${{full}}[@content-desc='${{desc}}']`;
        const cnt = countMatch(e => e.dataset.desc === desc && e.dataset.fullcls === full);
        locators.push({{ type: 'content-desc', xpath: xp, count: cnt }});
    }}

    // 4) XPath by class only
    {{
        const xp = `//${{full}}`;
        const cnt = countMatch(e => e.dataset.fullcls === full);
        locators.push({{ type: 'class', xpath: xp, count: cnt }});
    }}

    // 5) XPath by index (among same-class siblings)
    if (idx > 0) {{
        const xp = `(//${{full}})[${{idx + 1}}]`;
        locators.push({{ type: 'index', xpath: xp, count: 1, note: 'exact position, fragile' }});
    }}

    // 6) Combined: class + text + resource-id (most specific)
    const conds = [];
    if (rid) conds.push(`@resource-id='${{rid}}'`);
    if (t) conds.push(`@text='${{t}}'`);
    if (desc && !t) conds.push(`@content-desc='${{desc}}'`);
    if (conds.length >= 2) {{
        const xp = `//${{full}}[${{conds.join(' and ')}}]`;
        const cnt = countMatch(e => {{
            if (e.dataset.fullcls !== full) return false;
            if (rid && e.dataset.rid !== rid) return false;
            if (t && e.dataset.t !== t) return false;
            if (desc && !t && e.dataset.desc !== desc) return false;
            return true;
        }});
        locators.push({{ type: 'combined', xpath: xp, count: cnt }});
    }}

    // 7) XPath by resource-id only (any class)
    if (rid) {{
        const xp = `//*[@resource-id='${{rid}}']`;
        const cnt = countMatch(e => e.dataset.rid === rid);
        locators.push({{ type: 'resource-id (any)', xpath: xp, count: cnt }});
    }}

    // 8) XPath by text only (any class)
    if (t) {{
        const xp = `//*[@text='${{t}}']`;
        const cnt = countMatch(e => e.dataset.t === t);
        locators.push({{ type: 'text (any)', xpath: xp, count: cnt }});
    }}

    // 去重 + 按 count 升序
    const seen = new Set();
    const uniq = [];
    for (const l of locators) {{
        if (!seen.has(l.xpath)) {{ seen.add(l.xpath); uniq.push(l); }}
    }}
    uniq.sort((a, b) => a.count - b.count);
    return uniq;
}}

function showDetail(el) {{
    const bounds = el.dataset.bounds;
    const fullcls = el.dataset.fullcls;
    const shortcls = el.dataset.shortcls;
    const t = el.dataset.t;
    const desc = el.dataset.desc;
    const rid = el.dataset.rid;
    const pkg = el.dataset.pkg;
    const d = el.dataset.d;
    const idx = el.dataset.idx;
    const tag = (v, label) => `<span class="tag ${{v==='True'?'on':'off'}}">${{label}}: ${{v==='True'?'Y':'N'}}</span>`;

    // 生成定位器并排序
    const locs = genLocators(el);

    // 构建定位器表格行
    let locRows = '';
    locs.forEach((l, i) => {{
        const badge = l.count <= 1 ? 'unique' : l.count <= 3 ? 'good' : l.count <= 10 ? 'fair' : 'many';
        locRows += `<tr class="loc-row loc-${{badge}}">
            <td class="loc-type">${{l.type}}</td>
            <td class="loc-xpath" title="${{l.xpath}}" onclick="copyXPath(this)">${{l.xpath}}</td>
            <td class="loc-count"><span class="loc-badge ${{badge}}">${{l.count}}</span></td>
        </tr>`;
    }});

    detailCards.innerHTML = `
        <div class="info-card locator-card">
            <div class="label">XPath Locators (按匹配数 ↑ 升序)</div>
            <table class="loc-table">
                <thead><tr><th>Type</th><th>XPath</th><th>#</th></tr></thead>
                <tbody>${{locRows}}</tbody>
            </table>
            <div class="loc-hint">Count = 该 XPath 在当前页面匹配的元素数。越少越精确。点击 XPath 可复制。</div>
        </div>
        <div class="info-card"><div class="label">Bounds (定位坐标)</div><div class="value highlight">${{bounds}}</div></div>
        <div class="info-card"><div class="label">Class</div><div class="value">${{fullcls}}</div></div>
        <div class="info-card"><div class="label">Text</div><div class="value${{t?'':' empty'}}">${{t||'(empty)'}}</div></div>
        <div class="info-card"><div class="label">Content Desc</div><div class="value${{desc?'':' empty'}}">${{desc||'(empty)'}}</div></div>
        <div class="info-card"><div class="label">Resource ID</div><div class="value${{rid?'':' empty'}}">${{rid||'(empty)'}}</div></div>
        <div class="info-card"><div class="label">Index (同级序号)</div><div class="value">${{idx||'0'}}</div></div>
        <div class="info-card"><div class="label">Package</div><div class="value">${{pkg}}</div></div>
        <div class="info-card"><div class="label">Attributes</div><div class="value">
            ${{tag(el.dataset.clickable, 'Clickable')}}
            ${{tag(el.dataset.enabled, 'Enabled')}}
            ${{tag(el.dataset.scrollable, 'Scrollable')}}
            ${{tag(el.dataset.checkable, 'Checkable')}}
            ${{tag(el.dataset.checked, 'Checked')}}
        </div></div>
        <div class="info-card"><div class="label">Meta</div><div class="value">Depth: ${{d}} | NID: ${{selectedNid}}</div></div>
        <div class="info-card" style="display:flex;gap:8px;align-items:center;">
            <button class="parent-btn" onclick="selectParent()" id="btn-parent">↑ Select Parent</button>
            <span style="font-size:11px;color:#667;" id="parent-hint"></span>
        </div>
        <div class="info-card">
            <div class="label">📱 Phone Actions</div>
            <div style="display:flex;gap:4px;flex-wrap:wrap;align-items:center;">
                <button class="action-btn tap" onclick="doAction('click')" id="btn-tap">👆 Tap</button>
                <button class="action-btn input" onclick="showInputRow()" id="btn-input-show">⌨️ Input</button>
                <button class="action-btn screenshot" onclick="doAction('screenshot')">📸 Shot</button>
                <button class="action-btn screenshot" onclick="doAction('refresh_ui')" style="background:#3a1a3a;border-color:#5a2a5a;color:#f0a0f0;">🔄 Refresh</button>
                <span style="font-size:10px;color:#556;" id="action-status"></span>
            </div>
            <div class="input-row" id="input-row" style="display:none;">
                <input type="text" id="input-text" placeholder="输入文本后回车..." onkeydown="if(event.key==='Enter')doInput()">
                <button onclick="doInput()">发送</button>
                <button onclick="hideInputRow()" style="background:#333;">✕</button>
            </div>
        </div>
    `;
    // 更新父级按钮状态
    updateParentBtn(el);
    // 重置输入状态
    hideInputRow();
    document.getElementById('action-status').textContent = '';
}}

function copyXPath(td) {{
    const xpath = td.title || td.textContent;
    navigator.clipboard.writeText(xpath).then(() => {{
        td.classList.add('copied');
        setTimeout(() => td.classList.remove('copied'), 800);
    }}).catch(() => {{}});
}}

function clearSelection() {{
    document.querySelectorAll('.el.selected').forEach(e => e.classList.remove('selected'));
    document.querySelectorAll('#tree .tree-node.active').forEach(n => n.classList.remove('active'));
    selectedNid = null;
    clearCycle();
    detailCards.innerHTML = '<div class="empty">Click an element or scroll through layers</div>';
}}

// ===== 手机操作 =====
const ACTION_URL = 'http://localhost:8765/action';

function getActionCoords() {{
    if (selectedNid === null) return null;
    const el = document.querySelector(`.el[data-nid="${{selectedNid}}"]`);
    if (!el) return null;
    const bounds = el.dataset.bounds;
    const m = bounds.match(/\\[(\\d+),(\\d+)\\]\\[(\\d+),(\\d+)\\]/);
    if (!m) return null;
    const cx = Math.round((parseInt(m[1]) + parseInt(m[3])) / 2);
    const cy = Math.round((parseInt(m[2]) + parseInt(m[4])) / 2);
    return {{ x: cx, y: cy }};
}}

async function doAction(action) {{
    const coords = getActionCoords();
    if (!coords && action !== 'screenshot') {{
        toast('请先选中一个元素', 'error'); return;
    }}
    const statusEl = document.getElementById('action-status');
    statusEl.textContent = '...';

    try {{
        const body = {{ action }};
        if (coords) {{ body.x = coords.x; body.y = coords.y; }}
        const r = await fetch(ACTION_URL, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify(body)
        }});
        const data = await r.json();
        if (data.ok) {{
            if (action === 'click') toast('✅ Tapped (' + coords.x + ',' + coords.y + ')');
            else if (action === 'screenshot') toast('📸 Screenshot updated');
            else if (action === 'refresh_ui') {{
                toast('🔄 UI 已刷新，页面即将重载...');
                setTimeout(() => location.reload(), 800);
            }}
            statusEl.textContent = '✓';

            // 自动更新截图
            if (data.image) {{
                const img = document.querySelector('#phone-screen img');
                if (img) img.src = 'data:image/png;base64,' + data.image;
            }}
            setTimeout(() => {{ statusEl.textContent = ''; }}, 2000);
        }} else {{
            toast('❌ ' + (data.error || 'fail'), 'error');
            statusEl.textContent = '✗';
        }}
    }} catch (e) {{
        toast('⚠️ 无法连接到 action_server (localhost:8765)', 'error');
        statusEl.textContent = 'offline';
    }}
}}

function showInputRow() {{
    document.getElementById('input-row').style.display = 'flex';
    document.getElementById('input-text').focus();
}}

function hideInputRow() {{
    document.getElementById('input-row').style.display = 'none';
    document.getElementById('input-text').value = '';
}}

async function doInput() {{
    const text = document.getElementById('input-text').value;
    if (!text) return;
    const coords = getActionCoords();
    if (!coords) {{ toast('请先选中一个元素', 'error'); return; }}
    const statusEl = document.getElementById('action-status');
    statusEl.textContent = '...';

    try {{
        const r = await fetch(ACTION_URL, {{
            method: 'POST',
            headers: {{ 'Content-Type': 'application/json' }},
            body: JSON.stringify({{ action: 'input', text, x: coords.x, y: coords.y }})
        }});
        const data = await r.json();
        if (data.ok) {{
            toast('⌨️ Input: ' + text);
            statusEl.textContent = '✓';
            hideInputRow();
            setTimeout(() => {{ statusEl.textContent = ''; }}, 2000);
        }} else {{
            toast('❌ ' + (data.error || 'fail'), 'error');
            statusEl.textContent = '✗';
        }}
    }} catch (e) {{
        toast('⚠️ 无法连接到 action_server (localhost:8765)', 'error');
        statusEl.textContent = 'offline';
    }}
}}

function toast(msg, type) {{
    let t = document.getElementById('toast');
    if (!t) {{
        t = document.createElement('div');
        t.id = 'toast';
        t.className = 'toast';
        document.body.appendChild(t);
    }}
    t.textContent = msg;
    t.className = 'toast ' + (type || '');
    t.classList.add('show');
    clearTimeout(t._tid);
    t._tid = setTimeout(() => t.classList.remove('show'), 2500);
}}

// ===== 键盘操作 =====
document.addEventListener('keydown', function(e) {{
    if (e.key === 'Escape') {{ clearSelection(); hideCtx(); }}
    if (e.key === 'Tab' && cycleStack.length > 0) {{
        e.preventDefault();
        cycleIdx = (cycleIdx + 1) % cycleStack.length;
        document.querySelectorAll('.el.cycle-active').forEach(el => el.classList.remove('cycle-active'));
        const cur = document.querySelector(`.el[data-nid="${{cycleStack[cycleIdx]}}"]`);
        if (cur) cur.classList.add('cycle-active');
        badge.textContent = (cycleIdx + 1) + '/' + cycleStack.length;
    }}
    if (e.key === 'Enter' && cycleStack.length > 0 && cycleIdx >= 0) {{
        selectElByNid(cycleStack[cycleIdx]);
        clearCycle();
    }}
}});

// ===== 初始化 =====
refreshVisibility();
detailCards.innerHTML = '<div class="empty">Hover and scroll to cycle layers<br>Click to select · Right-click for menu<br>XPath locators auto-generated on select</div>';
</script>
</body>
</html>"""

    return html


def main():
    print("[1/3] 加载数据 ...")
    json_path = os.path.join(OUT_DIR, "ui_data.json")
    png_path = os.path.join(OUT_DIR, "screenshot.png")

    with open(json_path, "r", encoding="utf-8") as f:
        hierarchy = json.load(f)

    print("[2/3] 编码截图 ...")
    screenshot_b64 = encode_image_base64(png_path)
    print(f"      Base64: {len(screenshot_b64)} chars")

    print("[3/3] 生成 HTML v2 ...")
    html = generate_html(hierarchy, screenshot_b64)

    html_path = os.path.join(OUT_DIR, "phone_ui.html")
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    size_kb = os.path.getsize(html_path) / 1024
    print(f"      [OK] {html_path} ({size_kb:.0f} KB)")
    print("\n[DONE] 浏览器打开 phone_ui.html")


if __name__ == "__main__":
    main()
