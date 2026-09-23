"""把页面 dump 按两级结构分组，并为每个叶子分组出一张圈选图。

L1：布局容器 / 滚动·集合容器 / 内容控件 / 其它（不属于以上三类的）
L2：内容控件再拆 文本 / 图标 / 其它

输入：capture_page.py 产出的页面目录（window_dump.xml + screen.png）
输出：<out-dir>/two_level_elements.json + 每个非空叶子一张 <NN>_<key>.png
"""

import argparse
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from vendor.hierarchy import parse_hierarchy_xml
from vendor.xpath import gen_xpath_candidates, trim_hierarchy

LAYOUT = {
    "ViewGroup", "FrameLayout", "LinearLayout", "RelativeLayout", "ConstraintLayout",
    "CoordinatorLayout", "GridLayout", "TableLayout", "TableRow", "RadioGroup", "CardView",
    "AppBarLayout", "NavigationView", "DrawerLayout", "SwipeRefreshLayout", "Toolbar",
    "MotionLayout", "TabLayout", "ViewAnimator", "ViewSwitcher",
}
SCROLL = {
    "RecyclerView", "ListView", "GridView", "ScrollView", "HorizontalScrollView",
    "NestedScrollView", "ViewPager", "ViewPager2", "ExpandableListView", "AdapterView",
    "AbsListView", "AbsSpinner", "Spinner",
}
TEXT_CLASSES = {
    "TextView", "Button", "EditText", "AutoCompleteTextView", "CheckBox", "RadioButton",
    "Switch", "ToggleButton", "CheckedTextView", "Chip", "SearchView",
}
ICON_CLASSES = {"ImageView", "ImageButton"}

L1_ORDER = [
    ("layout_container", "布局容器"),
    ("scroll_collection", "滚动/集合容器"),
    ("content_widget", "内容控件"),
    ("unclassified", "其它（不属于以上三类的）"),
]
L2_ORDER = [("text", "文本"), ("icon", "图标"), ("other", "其它")]

COLORS = {
    "layout_container": (25, 200, 185),
    "scroll_collection": (229, 146, 102),
    "text": (183, 125, 238),
    "icon": (136, 157, 240),
    "other": (248, 166, 178),
}
QUALITY = {
    "resource-id": 0, "content-desc": 1, "combined": 2, "resource-id (any)": 3,
    "text": 4, "text (any)": 5, "class": 6, "index": 7,
}


def is_pua(s: str) -> bool:
    """私用区码点：图标字体伪装的文本。"""
    return any(0xE000 <= ord(c) <= 0xF8FF or 0xF0000 <= ord(c) <= 0xFFFFD for c in s)


def classify(class_name: str, text: str, desc: str, clickable: bool):
    """→ (L1, L2 或 None, 细类)"""
    c = class_name.rsplit(".", 1)[-1]
    t, d = text.strip(), desc.strip()
    if c in LAYOUT:
        return "layout_container", None, "layout"
    if c in SCROLL:
        return "scroll_collection", None, "scroll"
    if c in TEXT_CLASSES:
        if t and not is_pua(t):
            return "content_widget", "text", "text"
        if not t:
            return "content_widget", "text", "text_empty"
        return "content_widget", "icon", "icon_font"
    if c in ICON_CLASSES:
        return "content_widget", "icon", "icon_semantic" if d else "icon_bare"
    if c == "View":
        return "content_widget", "other", "hotzone" if clickable else "shape"
    return "unclassified", None, "unclassified"


def primary(e: dict) -> dict:
    """主定位：先筛 count==1 且非位置型候选，再按类型质量选；无唯一候选则 unstable。"""
    cands = [c for c in e["xpaths"] if c.get("xpath")]
    # 位置型候选全程排除（与算法层 algorithms/element_layers.pick_primary 同口径）
    usable = [c for c in cands if c.get("type") != "index"]
    uniq = [c for c in usable if int(c.get("count") or 0) == 1]
    if uniq:
        b = min(uniq, key=lambda c: (QUALITY.get(c.get("type"), 9), len(c.get("xpath", ""))))
        return {"xpath": b["xpath"], "type": b["type"], "count": 1, "stable": True}
    if usable:
        b = min(usable, key=lambda c: (int(c.get("count") or 0), QUALITY.get(c.get("type"), 9)))
        return {"xpath": b["xpath"], "type": b["type"], "count": int(b.get("count") or 0), "stable": False}
    return {"xpath": "", "type": "", "count": 0, "stable": False}


def element(e: dict, seq: int) -> dict:
    return {
        "seq": seq,
        "coords": {
            "x": e["x"], "y": e["y"], "w": e["width"], "h": e["height"],
            "cx": e["x"] + e["width"] // 2, "cy": e["y"] + e["height"] // 2, "bounds": e["bounds"],
        },
        "class_name": e["class_name"],
        "class_simple": e["class_name"].rsplit(".", 1)[-1],
        "resource_id": e["resource_id"],
        "text": e["text"],
        "content_desc": e["content_desc"],
        "package": e["package"],
        "depth": e["depth"],
        "index_attr": e["index"],
        "flags": {
            "clickable": e["clickable"], "long_clickable": e["long_clickable"],
            "scrollable": e["scrollable"], "checkable": e["checkable"], "checked": e["checked"],
            "enabled": e["enabled"], "focusable": e["focusable"],
        },
        "kept_in_snapshot": e["kept"],
        "content_kind": e["content_kind"],
        "primary": primary(e),
        "xpath_candidates": [
            {"type": c.get("type"), "xpath": c.get("xpath"), "count": c.get("count"),
             **({"note": c["note"]} if c.get("note") else {})}
            for c in e["xpaths"]
        ],
    }


def stats(items: list) -> dict:
    return {
        "count": len(items),
        "kept": sum(1 for e in items if e["kept"]),
        "stable_primary": sum(1 for e in items if primary(e)["stable"]),
        "clickable": sum(1 for e in items if e["clickable"]),
        "long_clickable": sum(1 for e in items if e["long_clickable"]),
        "scrollable": sum(1 for e in items if e["scrollable"]),
        "class_counts": {
            s: sum(1 for e in items if e["class_name"].rsplit(".", 1)[-1] == s)
            for s in sorted({e["class_name"].rsplit(".", 1)[-1] for e in items})
        },
        "content_kind_counts": {
            k: sum(1 for e in items if e["content_kind"] == k)
            for k in sorted({e["content_kind"] for e in items})
        },
    }


def load_font(size: int = 20):
    for cand in ("C:/Windows/Fonts/msyh.ttc", "C:/Windows/Fonts/simhei.ttf", "/System/Library/Fonts/PingFang.ttc"):
        if Path(cand).is_file():
            return ImageFont.truetype(cand, size)
    return ImageFont.load_default()


def dashed_rect(dr, box, color, width=3, dash=14, gap=10) -> None:
    x1, y1, x2, y2 = box
    for x in range(x1, x2, dash + gap):
        dr.line([(x, y1), (min(x + dash, x2), y1)], fill=color, width=width)
        dr.line([(x, y2), (min(x + dash, x2), y2)], fill=color, width=width)
    for y in range(y1, y2, dash + gap):
        dr.line([(x1, y), (x1, min(y + dash, y2))], fill=color, width=width)
        dr.line([(x2, y), (x2, min(y + dash, y2))], fill=color, width=width)


def build(page_dir: Path, out_dir: Path) -> dict:
    raw = (page_dir / "window_dump.xml").read_text(encoding="utf-8")
    all_nodes = parse_hierarchy_xml(raw)
    for e in all_nodes:
        if e["resource_id"] or e["text"] or e["content_desc"] or e["clickable"]:
            e["xpaths"] = gen_xpath_candidates(e, all_nodes)
        else:
            e["xpaths"] = []
    kept_ids = {id(e) for e in trim_hierarchy(all_nodes)}
    nodes = [n for n in all_nodes if n["class_name"]]

    for n in nodes:
        l1, l2, fine = classify(n["class_name"], n["text"], n["content_desc"], n["clickable"])
        n["level1"], n["level2"], n["content_kind"] = l1, l2, fine
        n["kept"] = id(n) in kept_ids

    ordered = sorted(nodes, key=lambda e: (e["y"], e["x"], e["depth"]))
    seq_of = {id(e): i + 1 for i, e in enumerate(ordered)}

    groups = []
    for key, name in L1_ORDER:
        members = [e for e in ordered if e["level1"] == key]
        node = {"level": 1, "key": key, "name": name, **stats(members), "children": [], "elements": []}
        if key == "content_widget":
            for k2, n2 in L2_ORDER:
                sub = [e for e in members if e["level2"] == k2]
                node["children"].append({
                    "level": 2, "key": k2, "name": n2, **stats(sub),
                    "elements": [element(e, seq_of[id(e)]) for e in sub],
                })
        else:
            node["elements"] = [element(e, seq_of[id(e)]) for e in members]
        groups.append(node)

    meta = {
        "source_dir": str(page_dir).replace("\\", "/"),
        "source_xml": str(page_dir / "window_dump.xml").replace("\\", "/"),
        "screenshot": str(page_dir / "screen.png").replace("\\", "/"),
        "screen": [
            max(e["x"] + e["width"] for e in nodes),
            max(e["y"] + e["height"] for e in nodes),
        ],
        "package": nodes[0]["package"],
        "ordering": "每个分组内按 (y, x, depth) 升序（坐标顺序）",
        "levels": {"L1": dict(L1_ORDER), "L2(仅内容控件)": dict(L2_ORDER)},
        "L2_rules": {
            "text": "文本类控件且 text 非空且非私用区字符（空文本也归文本组）",
            "icon": "ImageView/ImageButton；或文本类但 text 为私用区字符（图标字体）",
            "other": "裸 View（可点热区 / 分隔线 / 色块 / 占位）",
        },
        "primary_rule": "先筛 count==1 且非 index，再按 resource-id > content-desc > combined > text > class 选主定位；无唯一候选则 stable=false",
        "excluded": "合成根节点 <hierarchy>（class 为空）不计入元素",
    }
    manifest = {}
    mf = page_dir / "manifest.json"
    if mf.is_file():
        manifest = json.loads(mf.read_text(encoding="utf-8"))
    meta["activity"] = manifest.get("activity", "")

    result = {
        "meta": meta,
        "summary": {
            "total_elements": len(nodes),
            "by_level1": [
                {"key": g["key"], "name": g["name"], "count": g["count"], "kept": g["kept"],
                 "children": [{"key": c["key"], "name": c["name"], "count": c["count"], "kept": c["kept"]}
                              for c in g["children"]]}
                for g in groups
            ],
        },
        "groups": groups,
    }

    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "two_level_elements.json"
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")

    # ── 出图：一个非空叶子一张 ──
    base_img = Image.open(page_dir / "screen.png").convert("RGB")
    font = load_font(20)
    footer = 104
    leaves = []
    for g in groups:
        if g["children"]:
            for c in g["children"]:
                leaves.append((g, c))
        else:
            leaves.append((g, None))

    rendered = []
    idx = 0
    for g, c in leaves:
        path = g["name"] if c is None else "%s → %s" % (g["name"], c["name"])
        key = g["key"] if c is None else c["key"]
        items = c["elements"] if c is not None else g["elements"]
        if not items:
            continue
        color = COLORS.get(key, (140, 140, 140))
        idx += 1
        overlay = Image.new("RGBA", base_img.size, (0, 0, 0, 0))
        dr = ImageDraw.Draw(overlay)
        for e in items:
            b = e["coords"]
            box = (b["x"], b["y"], b["x"] + b["w"], b["y"] + b["h"])
            dr.rectangle(box, fill=color + (46,))
            if e["kept_in_snapshot"]:
                dr.rectangle(box, outline=color + (255,), width=4)
            else:
                dashed_rect(dr, box, color + (255,), width=3)
            tx, ty = box[0] + 3, box[1] + 3
            tb = dr.textbbox((tx, ty), e["index_attr"], font=font)
            dr.rectangle((tb[0] - 3, tb[1] - 2, tb[2] + 3, tb[3] + 2), fill=color + (235,))
            dr.text((tx, ty), e["index_attr"], fill=(255, 255, 255), font=font)
        composed = Image.alpha_composite(base_img.convert("RGBA"), overlay).convert("RGB")
        canvas = Image.new("RGB", (base_img.width, base_img.height + footer), (248, 248, 240))
        canvas.paste(composed, (0, 0))
        cdr = ImageDraw.Draw(canvas)
        cdr.rectangle((0, base_img.height, base_img.width - 1, base_img.height + footer - 1), outline=color, width=3)
        cdr.rectangle((14, base_img.height + 26, 46, base_img.height + 58), fill=color)
        cdr.text(
            (58, base_img.height + 14),
            "%s · %d 个（保留 %d）" % (path, len(items), sum(1 for e in items if e["kept_in_snapshot"])),
            fill=(121, 79, 39), font=font,
        )
        sub = ({kk: sum(1 for e in items if e["content_kind"] == kk)
                for kk in sorted({e["content_kind"] for e in items})} if c is not None else {})
        cdr.text(
            (58, base_img.height + 58),
            "%s｜实线=保留 虚线=裁 角标=元素 index" % (json.dumps(sub, ensure_ascii=False) + " " if sub else ""),
            fill=(138, 123, 102), font=font,
        )
        out = out_dir / ("%02d_%s.png" % (idx, key))
        canvas.save(str(out))
        rendered.append({
            "path": path, "key": key, "file": str(out).replace("\\", "/"),
            "elements": len(items), "kept": sum(1 for e in items if e["kept_in_snapshot"]),
        })

    result["images"] = rendered
    json_path.write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding="utf-8")
    return {"json": str(json_path).replace("\\", "/"), "images": rendered,
            "total_elements": len(nodes), "by_level1": result["summary"]["by_level1"]}


def main() -> None:
    ap = argparse.ArgumentParser(description="两级分组 + 每叶子一张圈选图")
    ap.add_argument("page_dir", help="capture_page.py 产出的页面目录")
    ap.add_argument("--out-dir", default="", help="输出目录；缺省=页面目录本身")
    args = ap.parse_args()
    page_dir = Path(args.page_dir)
    if not (page_dir / "window_dump.xml").is_file():
        raise SystemExit("页面目录里没有 window_dump.xml：%s" % page_dir)
    print(json.dumps(build(page_dir, Path(args.out_dir) if args.out_dir else page_dir), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()