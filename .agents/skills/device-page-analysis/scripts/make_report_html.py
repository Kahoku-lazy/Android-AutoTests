"""压缩预览图 + ECharts 自包含 HTML 报告（animal-island-ui 设计规范）。"""

import argparse
import base64
import json
from datetime import datetime
from pathlib import Path

from PIL import Image


CSS = """
:root{
  --primary:#19c8b9; --primary-bg:#e6f9f6;
  --text:#794f27; --text-body:#725d42; --text-secondary:#9f927d; --text-muted:#8a7b66;
  --bg:#f8f8f0; --bg-content:rgb(247,243,223); --bg-disabled:#f0ece2;
  --border:#c4b89e; --border-hover:#a89878; --border-strong:#9f927d;
  --success:#6fba2c; --warning:#f5c31c; --error:#e05a5a;
  --focus-yellow:#ffcc00;
  --r-sm:12px; --r-base:18px; --r-lg:24px;
  --ease:cubic-bezier(0.4,0,0.2,1);
  --mono:"SF Mono","Fira Code","Cascadia Code",Consolas,monospace;
}
*{box-sizing:border-box;margin:0;padding:0}
body{font-family:Nunito,"Noto Sans SC",-apple-system,"PingFang SC",sans-serif;font-weight:500;letter-spacing:.01em;background:var(--bg);color:var(--text-body);line-height:1.65}
:focus-visible{outline:2px solid var(--focus-yellow);outline-offset:2px}
.page{max-width:1180px;margin:0 auto;padding:40px 32px 72px}
.ribbon{--rb:#e0a92e;display:inline-flex;align-items:center;position:relative;height:2em;padding:0 1.6em;background:#f7cd67;color:var(--text);font-weight:900;font-size:26px;line-height:1;letter-spacing:.03em;filter:drop-shadow(0 .08em .12em rgba(0,0,0,.05))}
.ribbon-back{position:absolute;bottom:-.4em;width:1.7em;height:1.7em;background:var(--rb);z-index:1}
.ribbon-back.left{right:100%;clip-path:polygon(100% 0%,100% 100%,0% 100%,30% 50%,0% 0%)}
.ribbon-back.right{left:100%;clip-path:polygon(0% 0%,100% 0%,70% 50%,100% 100%,0% 100%)}
.ribbon span{position:relative;z-index:4;padding-top:.11em}
.sub{margin-top:18px;font-size:15px;font-weight:600;color:var(--text-muted)}
.meta{margin-top:12px;display:flex;flex-wrap:wrap;gap:8px}
h2{font-size:20px;font-weight:800;color:var(--text);letter-spacing:.02em;margin:38px 0 14px;padding-left:14px;border-left:6px solid var(--primary);line-height:1.3}
h3{font-size:17px;font-weight:800;color:var(--text);margin:0}
p{font-size:14.5px;color:var(--text-body);margin:8px 0}
code{font-family:var(--mono);font-size:12.5px;font-weight:600;background:var(--bg-disabled);border:1px solid var(--border);border-radius:var(--r-sm);padding:1px 6px;color:#8a5a2b}
.card{background:var(--bg-content);border:2px solid var(--border);border-radius:var(--r-base);padding:18px 22px;margin:14px 0}
.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:14px}
.stat{background:var(--bg-content);border:2px solid var(--border);border-radius:var(--r-lg);padding:18px 20px;transition:transform .25s var(--ease)}
.stat:hover{transform:translateY(-2px)}
.stat-n{font-size:34px;font-weight:900;line-height:1.05;color:var(--text)}
.stat-l{margin-top:6px;font-size:13.5px;font-weight:700;color:var(--text-body)}
.stat-s{margin-top:3px;font-size:12px;color:var(--text-secondary)}
.grid2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
@media(max-width:900px){.grid2{grid-template-columns:1fr}}
.chart{width:100%;height:360px}
.chart.tall{height:420px}
.chart.sm{height:300px}
table{width:100%;border-collapse:separate;border-spacing:0;background:var(--bg-content);border-radius:var(--r-base);overflow:hidden;margin:12px 0;font-size:13.5px}
th{background:#f3ecd6;color:var(--text);font-weight:800;text-align:left;padding:12px 16px;letter-spacing:.02em;font-size:13px}
td{padding:11px 16px;color:var(--text-body);font-weight:500;border-top:1.5px dashed #e6dcc4}
tbody tr:nth-child(even){background:rgba(248,248,240,.6)}
td.num,th.num{text-align:right;font-family:var(--mono);font-weight:600}
.tag{display:inline-flex;align-items:center;height:24px;padding:0 10px;border-radius:999px;border:1.5px solid transparent;font-size:12px;font-weight:700;line-height:21px;background:var(--bg-content);color:#8f734f;border-color:var(--border)}
.tag.lv{background:var(--primary);color:#fffdf5}
.tag.lv2{background:#b77dee;color:#fffdf5}
.leaf{display:grid;grid-template-columns:300px 1fr;gap:22px;background:var(--bg-content);border:2px solid var(--border);border-radius:var(--r-lg);padding:20px;margin:18px 0;align-items:start}
@media(max-width:820px){.leaf{grid-template-columns:1fr}}
.leaf-img img{width:100%;border:2px solid var(--border);border-radius:var(--r-sm);display:block}
.cap{margin-top:8px;font-size:12px;color:var(--text-secondary);font-weight:600;text-align:center}
.leaf-head{display:flex;align-items:center;gap:10px;flex-wrap:wrap}
.badge{display:inline-flex;align-items:center;justify-content:center;width:30px;height:30px;border-radius:50%;color:#fffdf5;font-weight:900;font-size:13px}
.metrics{display:flex;flex-wrap:wrap;gap:8px;margin:12px 0}
.metric{background:#fffdf5;border:1.5px solid var(--border);border-radius:var(--r-sm);padding:6px 11px;font-size:12.5px;font-weight:700;color:var(--text-body)}
.metric b{font-family:var(--mono);font-size:14px;color:var(--text)}
.split{height:12px;border-radius:999px;overflow:hidden;border:1.5px solid var(--border);background:#fffdf5;display:flex;margin:6px 0 12px}
.split i{display:block;height:100%}
.legend-min{font-size:12px;color:var(--text-secondary);font-weight:600;margin-bottom:6px}
.note{font-size:12.5px;color:var(--text-secondary);font-weight:500}
.dl{font-size:13.5px;margin:6px 0}
.dl b{color:var(--text);font-weight:800}
footer{margin-top:44px;padding-top:20px;border-top:2px solid var(--border);font-size:13px;color:var(--text-secondary);font-weight:500}
ul{margin:8px 0 8px 20px}
li{font-size:14px;color:var(--text-body);margin:4px 0}
"""

JS = """
(function () {
  if (typeof echarts === "undefined") {
    var box = document.querySelectorAll(".chart");
    for (var i = 0; i < box.length; i++) {
      box[i].innerHTML = '<p class="note" style="padding:20px">图表库未加载（当前环境无法访问 CDN），请参考上方数据表。</p>';
    }
    return;
  }
  var TXT = "#725d42", TITLE = "#794f27";
  var base = function (t) {
    return { title: { text: t, left: "center", textStyle: { color: TITLE, fontSize: 15, fontWeight: 800, fontFamily: "Nunito, Noto Sans SC" } },
             tooltip: { trigger: "item" },
             textStyle: { color: TXT, fontFamily: "Nunito, Noto Sans SC", fontWeight: 600 } };
  };
  var sun = echarts.init(document.getElementById("cSun"));
  var s = base("L1 / L2 层级与元素数");
  s.series = [{
    type: "sunburst", radius: [0, "92%"], data: DATA.sunburst,
    label: { color: "#794f27", fontWeight: 700, fontSize: 12, minAngle: 5 },
    itemStyle: { borderColor: "#f8f8f0", borderWidth: 2 },
    levels: [{}, { r0: "15%", r: "52%", label: { fontSize: 13, fontWeight: 900 } }, { r0: "55%", r: "90%" }],
    color: ["#19c8b9", "#e59266", "#b77dee", "#c4b89e", "#889df0", "#f8a6b2"]
  }];
  sun.setOption(s);

  var bar = echarts.init(document.getElementById("cBar"));
  var b = base("");
  b.grid = { left: 54, right: 18, top: 46, bottom: 62 };
  b.tooltip = { trigger: "axis" };
  b.legend = { bottom: 6, textStyle: { color: TXT, fontWeight: 700 }, itemWidth: 14, itemHeight: 10 };
  b.xAxis = { type: "category", data: DATA.cats, axisLabel: { color: TXT, fontWeight: 700, interval: 0, rotate: 18, fontSize: 11 }, axisLine: { lineStyle: { color: "#c4b89e" } } };
  b.yAxis = { type: "value", axisLabel: { color: TXT }, splitLine: { lineStyle: { color: "#e6dcc4", type: "dashed" } } };
  b.series = [
    { name: "元素总数", type: "bar", data: DATA.tot, itemStyle: { color: "#19c8b9", borderRadius: [6, 6, 0, 0] }, barMaxWidth: 26 },
    { name: "平台保留", type: "bar", data: DATA.kept, itemStyle: { color: "#889df0", borderRadius: [6, 6, 0, 0] }, barMaxWidth: 26 },
    { name: "稳定主定位", type: "bar", data: DATA.stab, itemStyle: { color: "#6fba2c", borderRadius: [6, 6, 0, 0] }, barMaxWidth: 26 }
  ];
  bar.setOption(b);

  var pie = echarts.init(document.getElementById("cPie"));
  var p = base("各分组元素占比");
  p.legend = { bottom: 0, textStyle: { color: TXT, fontWeight: 700, fontSize: 11 } };
  p.series = [{
    type: "pie", radius: ["38%", "68%"], center: ["50%", "47%"], data: DATA.pie,
    label: { color: TXT, fontWeight: 700, fontSize: 11, formatter: "{b} {c} ({d}%)" },
    labelLine: { lineStyle: { color: "#c4b89e" } },
    itemStyle: { borderColor: "#f8f8f0", borderWidth: 3 },
    color: ["#19c8b9", "#e59266", "#b77dee", "#889df0", "#f8a6b2"]
  }];
  pie.setOption(p);

  var fine = echarts.init(document.getElementById("cFine"));
  var f = base("内容控件：七个细类的元素数");
  f.grid = { left: 130, right: 40, top: 30, bottom: 26 };
  f.tooltip = { trigger: "axis" };
  f.xAxis = { type: "value", axisLabel: { color: TXT }, splitLine: { lineStyle: { color: "#e6dcc4", type: "dashed" } } };
  f.yAxis = { type: "category", data: DATA.fine.map(function (x) { return x.name; }).reverse(), axisLabel: { color: TXT, fontWeight: 700, fontSize: 11 }, axisLine: { lineStyle: { color: "#c4b89e" } } };
  f.series = [{
    type: "bar", data: DATA.fine.map(function (x) { return x.value; }).reverse(),
    itemStyle: { color: "#b77dee", borderRadius: [0, 6, 6, 0] }, barMaxWidth: 18,
    label: { show: true, position: "right", color: TITLE, fontWeight: 800 }
  }];
  fine.setOption(f);

  window.addEventListener("resize", function () { sun.resize(); bar.resize(); pie.resize(); fine.resize(); });
})();
"""

COLORS = {
    "布局容器": "#19c8b9",
    "滚动/集合容器": "#e59266",
    "文本": "#b77dee",
    "图标": "#889df0",
    "其它": "#f8a6b2",
}


def intros(node: dict, path: str) -> dict:
    """逐组介绍文案（数字来自实际统计，不写死）。"""
    key = path.split(" → ")[-1]
    n = node["count"]
    kinds = node.get("content_kind_counts", {}) or {}
    cc = node.get("class_counts", {}) or {}
    if key == "布局容器":
        return {
            "lead": "只负责摆放子元素的 ViewGroup —— 决定子元素的坐标系与层叠顺序，本身通常不承载内容。",
            "roles": "窗口根容器、Activity 内容根（android:id/content）、Fragment 落点、列表项行、Tab 容器、图标小格。",
            "look": "看虚线框的密度：被裁的多是「多层外壳」——同 bounds 去重只留最具体的一个节点。",
            "watch": "容器不等于不可操作：本组有 %d 个自身 clickable=true，是可以点的。" % node["clickable"],
        }
    if key == "滚动/集合容器":
        return {
            "lead": "带滚动与复用职责的 ViewGroup，是滑动、翻页、列表操作的真正目标。",
            "roles": "ScrollView / RecyclerView / ViewPager / GridView / ListView 等。",
            "look": "这组元素最少但最「关键」：整页滚动往往就靠其中一个容器承载。",
            "watch": "保留 %d / %d：被同框去重裁掉后，就没有稳定的整页滑动目标可用了。" % (node["kept"], n),
        }
    if key == "文本":
        return {
            "lead": "文本类控件（TextView / Button / EditText / CheckBox / RadioButton / Switch …）且当前 text 非空 —— 屏幕上「能读到的字」。",
            "roles": "标题、正文、数值、按钮文案、状态栏时钟。",
            "look": "框应全部贴在文字上；若框里出现图标，说明该页用图标字体伪装了图形。",
            "watch": "text 非空不等于肉眼可见：可能被压成极窄高度，或被上层容器遮挡（dump 无法判断遮挡）。",
        }
    if key == "图标":
        bare = kinds.get("icon_bare", 0)
        return {
            "lead": "图形类控件（ImageView / ImageButton），承载图标与图片。",
            "roles": "头像、功能入口图标、行首图标、右箭头、底部 Tab 图标、状态栏信号图标。",
            "look": "框应逐个贴合图标；注意本组 %d 个里 %d 个既无 text 也无 content-desc。" % (n, bare),
            "watch": "无语义的图标只能靠 resource-id 或位置定位 —— 这是图标类自动化最脆弱的地方。",
        }
    return {
        "lead": "内容控件里的「裸 View」：既不承载文字也不承载图形，但可能承担交互。",
        "roles": "不可见的点击热区、分隔线、色块、导航底色。",
        "look": "若框盖在「图标 + 文字」的整块区域上，那通常是叠在上层的透明点击热区。",
        "watch": "看得见的图标和文字往往不可点，真正的点击目标是透明 View —— 判断「点哪里」必须看 clickable。",
    }


def build_html(page_dir: Path, out: Path, title: str, img_width: int, quality: int) -> dict:
    data = json.loads((page_dir / "two_level_elements.json").read_text(encoding="utf-8"))
    meta = data["meta"]
    comp = page_dir / "compressed"
    comp.mkdir(parents=True, exist_ok=True)

    LANCZOS = getattr(Image, "LANCZOS", None) or Image.Resampling.LANCZOS

    nodes_by_path, leaves = {}, []
    for g in data["groups"]:
        if g["children"]:
            for c in g["children"]:
                path = g["name"] + " → " + c["name"]
                nodes_by_path[path] = (g, c)
                leaves.append(path)
        else:
            nodes_by_path[g["name"]] = (g, None)
            leaves.append(g["name"])

    shots = []
    for entry in data.get("images", []):
        src = Path(entry["file"])
        dst = comp / (src.stem + ".jpg")
        im = Image.open(str(src)).convert("RGB")
        resized = im.resize((img_width, int(im.height * img_width / im.width)), LANCZOS)
        resized.save(str(dst), "JPEG", quality=quality, optimize=True, progressive=True)
        raw = dst.read_bytes()
        g, c = nodes_by_path[entry["path"]]
        shots.append({
            "path": entry["path"],
            "file_jpg": str(dst).replace("\\", "/"),
            "orig_kb": round(src.stat().st_size / 1024.0),
            "kb": round(len(raw) / 1024.0),
            "w": im.width, "h": im.height,
            "b64": base64.b64encode(raw).decode("ascii"),
            "node": c if c is not None else g,
            "level": 2 if c is not None else 1,
        })

    sun = []
    for g in data["groups"]:
        if g["count"] == 0:
            continue
        item = {"name": g["name"], "value": g["count"]}
        if g["children"]:
            item["children"] = [{"name": c["name"], "value": c["count"]} for c in g["children"] if c["count"] > 0]
        sun.append(item)

    cats = [s["path"] for s in shots]
    payload = {
        "sunburst": sun,
        "cats": cats,
        "tot": [s["node"]["count"] for s in shots],
        "kept": [s["node"]["kept"] for s in shots],
        "stab": [s["node"]["stable_primary"] for s in shots],
        "pie": [{"name": s["path"].split(" → ")[-1], "value": s["node"]["count"]} for s in shots],
        "fine": [
            {"name": k, "value": v}
            for g in data["groups"] if g["key"] == "content_widget"
            for c in g["children"]
            for k, v in (c.get("content_kind_counts") or {}).items()
        ],
    }

    total = data["summary"]["total_elements"]
    kept_n = sum(g["kept"] for g in data["groups"])
    stable_n = sum(g["stable_primary"] for g in data["groups"])
    click_n = sum(g["clickable"] for g in data["groups"])

    p = []
    p.append("<!DOCTYPE html>")
    p.append('<html lang="zh-CN">')
    p.append("<head>")
    p.append('<meta charset="UTF-8">')
    p.append('<meta name="viewport" content="width=device-width, initial-scale=1.0">')
    p.append("<title>" + title + "</title>")
    p.append('<link rel="preconnect" href="https://fonts.googleapis.com">')
    p.append('<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>')
    p.append('<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;500;600;700;800;900&family=Noto+Sans+SC:wght@400;500;700&display=swap" rel="stylesheet">')
    p.append('<script src="https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js"></script>')
    p.append("<style>")
    p.append(CSS)
    p.append("</style>")
    p.append("</head>")
    p.append("<body>")
    p.append('<div class="page">')
    p.append('<div class="ribbon"><span class="ribbon-back left"></span><span class="ribbon-back right"></span><span>' + title + "</span></div>")
    p.append('<p class="sub">两级分组：L1 布局容器 / 滚动·集合容器 / 内容控件 / 其它　·　L2 内容控件 → 文本 / 图标 / 其它</p>')
    p.append('<div class="meta">')
    p.append('<span class="tag">' + meta.get("package", "") + " " + meta.get("activity", "") + "</span>")
    p.append('<span class="tag">屏幕 ' + str(meta["screen"][0]) + " × " + str(meta["screen"][1]) + "</span>")
    p.append('<span class="tag">元素 ' + str(total) + "</span>")
    p.append('<span class="tag">生成 ' + datetime.now().strftime("%Y-%m-%d %H:%M") + "</span>")
    p.append('<span class="tag">来源 ' + meta["source_dir"] + "</span>")
    p.append("</div>")

    p.append("<h2>一、总览</h2>")
    p.append('<div class="stats">')
    for n, label, sub in [
        (total, "元素总数", "L1 三类 + 其它"),
        (len(shots), "分组数量", "本轮统计的数据分层"),
        (kept_n, "平台快照保留", "其余 " + str(total - kept_n) + " 个被展示裁剪丢弃"),
        (stable_n, "有稳定主定位", "其余 " + str(total - stable_n) + " 个只能位置型/多义定位"),
        (click_n, "可点击元素", "跨全部分组统计"),
    ]:
        p.append('<div class="stat"><div class="stat-n">' + str(n) + '</div><div class="stat-l">' + label + '</div><div class="stat-s">' + sub + "</div></div>")
    p.append("</div>")
    p.append('<div class="card"><div id="cSun" class="chart tall"></div><p class="note">旭日图：内环是 L1 分组，外环是「内容控件」的二级拆分；数字为该组元素数。</p></div>')

    p.append("<h2>二、分组数量对比</h2>")
    p.append('<div class="grid2">')
    p.append('<div class="card"><div id="cBar" class="chart"></div><p class="note">元素总数 / 平台保留 / 稳定主定位</p></div>')
    p.append('<div class="card"><div id="cPie" class="chart"></div><p class="note">各分组元素占比</p></div>')
    p.append("</div>")
    p.append('<table><thead><tr><th>#</th><th>层级</th><th>分组</th><th class="num">元素</th><th class="num">保留</th><th class="num">被裁</th><th class="num">稳定定位</th><th class="num">可点击</th><th class="num">可滚动</th></tr></thead><tbody>')
    for i, s in enumerate(shots, start=1):
        n = s["node"]
        p.append("<tr><td>" + str(i) + "</td><td>" + ("L1" if s["level"] == 1 else "L2") + "</td><td>" + s["path"] + '</td><td class="num">' + str(n["count"]) + '</td><td class="num">' + str(n["kept"]) + '</td><td class="num">' + str(n["count"] - n["kept"]) + '</td><td class="num">' + str(n["stable_primary"]) + '</td><td class="num">' + str(n["clickable"]) + '</td><td class="num">' + str(n["scrollable"]) + "</td></tr>")
    p.append("</tbody></table>")
    zero = [g["name"] for g in data["groups"] if g["count"] == 0]
    if zero:
        p.append('<p class="note">说明：L1「' + " / ".join(zero) + '」在本页为 <b>0</b> 个，故未出现在图表与上表中。</p>')

    p.append("<h2>三、分组逐个介绍</h2>")
    for i, s in enumerate(shots, start=1):
        n = s["node"]
        key = s["path"].split(" → ")[-1]
        color = COLORS.get(key, "#9f927d")
        iv = intros(n, s["path"])
        p.append('<div class="leaf">')
        p.append('<div class="leaf-img">')
        p.append('<img alt="' + s["path"] + '" src="data:image/jpeg;base64,' + s["b64"] + '">')
        p.append('<div class="cap">压缩预览 ' + str(s["w"]) + "×" + str(s["h"]) + " → " + str(img_width) + "px · " + str(s["kb"]) + " KB（原图 " + str(s["orig_kb"]) + " KB）</div>")
        p.append("</div>")
        p.append('<div class="leaf-body">')
        p.append('<div class="leaf-head"><span class="badge" style="background:' + color + '">' + ("%02d" % i) + "</span><h3>" + s["path"] + '</h3><span class="tag ' + ("lv" if s["level"] == 1 else "lv2") + '">' + ("L1 分组" if s["level"] == 1 else "L2 拆分") + "</span></div>")
        p.append('<p style="margin-top:10px">' + iv["lead"] + "</p>")
        p.append('<div class="metrics">')
        for lab, val in [("元素", n["count"]), ("保留", n["kept"]), ("被裁", n["count"] - n["kept"]), ("稳定定位", n["stable_primary"]), ("可点击", n["clickable"]), ("可滚动", n["scrollable"])]:
            p.append('<span class="metric">' + lab + " <b>" + str(val) + "</b></span>")
        p.append("</div>")
        kept_pct = (100.0 * n["kept"] / n["count"]) if n["count"] else 0
        p.append('<div class="legend-min">保留 ' + str(n["kept"]) + " / 被裁 " + str(n["count"] - n["kept"]) + "</div>")
        p.append('<div class="split"><i style="width:' + ("%.1f" % kept_pct) + "%;background:" + color + '"></i><i style="width:' + ("%.1f" % (100 - kept_pct)) + '%;background:#e6dcc4"></i></div>')
        cc = n.get("class_counts") or {}
        kk = n.get("content_kind_counts") or {}
        if cc:
            p.append('<p class="dl"><b>类名分布：</b>' + " · ".join(k + " " + str(v) for k, v in sorted(cc.items(), key=lambda x: -x[1])) + "</p>")
        if kk:
            p.append('<p class="dl"><b>细类分布：</b>' + " · ".join(k + " " + str(v) for k, v in sorted(kk.items(), key=lambda x: -x[1])) + "</p>")
        p.append('<p class="dl"><b>典型角色：</b>' + iv["roles"] + "</p>")
        p.append('<p class="dl" style="color:#8a5a2b"><b>图上看什么：</b>' + iv["look"] + "</p>")
        p.append('<p class="dl" style="color:#a85565"><b>注意：</b>' + iv["watch"] + "</p>")
        p.append("</div></div>")

    p.append("<h2>四、内容控件二级拆分的判定依据</h2>")
    p.append("<table><thead><tr><th>细类</th><th>归到 L2</th><th>判据</th></tr></thead><tbody>")
    for fine, lvl2, rule in [
        ("text", "文本", "文本类控件且 text 非空且非私用区字符"),
        ("text_empty", "文本", "文本类控件但 text 为空（占位/间距）"),
        ("icon_font", "图标", "文本类控件但 text 是私用区码点（图标字体伪装的图标）"),
        ("icon_semantic", "图标", "ImageView / ImageButton 且有 content-desc"),
        ("icon_bare", "图标", "ImageView / ImageButton 且无 content-desc（纯图形）"),
        ("hotzone", "其它", "裸 View 且 clickable=true（不可见点击热区）"),
        ("shape", "其它", "裸 View 且不可点击（分隔线 / 色块 / 占位）"),
    ]:
        p.append("<tr><td><code>" + fine + "</code></td><td>" + lvl2 + "</td><td>" + rule + "</td></tr>")
    p.append("</tbody></table>")
    p.append('<div class="card"><div id="cFine" class="chart sm"></div><p class="note">七个细类的元素数（它们决定 L2 的三个分组）</p></div>')

    p.append("<h2>五、口径与局限</h2>")
    p.append('<div class="card"><ul>')
    p.append("<li><b>排序</b>：每个分组内按 (y, x, depth) 升序，即先上后下、同高再左到右；坐标单位为像素，与截图同一坐标空间。</li>")
    p.append("<li><b>L1 判据</b>：按控件类名所属集合划分（Android 框架类层级 + 职责），不在任何集合内的类名归「其它」，不做猜测。</li>")
    p.append("<li><b>主定位</b>：先筛 <code>count==1</code> 且非位置型（index）的候选，再按 resource-id &gt; content-desc &gt; combined &gt; text &gt; class 选一条；没有唯一候选时标记为不稳定。<b>这是本报告的分析口径，平台当前没有这个字段。</b></li>")
    p.append("<li><b>保留/被裁</b>：来自平台 <code>algorithms/xpath.trim_hierarchy</code> 的两条规则（纯布局容器、同 bounds 去重），只影响写库的展示集合，不代表元素不存在。</li>")
    p.append("<li><b>样本</b>：单页面单次采样（" + str(total) + " 个元素）。计数随页面状态变化，换页必须重跑，不要跨页面复用数字。</li>")
    p.append("<li><b>图片</b>：正文截图是压缩预览（宽 " + str(img_width) + "px JPEG），仅用于对照分组范围；原始 PNG 与 XML 在 <code>" + meta["source_dir"] + "</code> 下。</li>")
    p.append("<li><b>可见性</b>：<code>text</code> 非空不等于肉眼可见（可能存在被压成极窄高度、或被上层遮挡的文本）；dump 无法判断遮挡。</li>")
    p.append("</ul></div>")
    p.append("<footer>" + title + " · 由 <code>device-page-analysis</code> skill 生成 · 数据源 " + meta["source_xml"] + "</footer>")
    p.append("</div>")
    p.append("<script>")
    p.append("var DATA = " + json.dumps(payload, ensure_ascii=False) + ";")
    p.append(JS)
    p.append("</script>")
    p.append("</body>")
    p.append("</html>")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(p), encoding="utf-8")
    return {
        "out": str(out).replace("\\", "/"),
        "html_kb": round(out.stat().st_size / 1024.0),
        "images": [{"path": s["path"], "orig_kb": s["orig_kb"], "kb": s["kb"], "file": s["file_jpg"]} for s in shots],
        "total_orig_kb": sum(s["orig_kb"] for s in shots),
        "total_comp_kb": sum(s["kb"] for s in shots),
    }


def resolve_title(args) -> str:
    if args.title_file:
        return Path(args.title_file).read_text(encoding="utf-8").strip()
    if args.title:
        return args.title
    return "设备页面元素分层分析"


def main() -> None:
    ap = argparse.ArgumentParser(description="压缩预览图 + ECharts 自包含 HTML 报告")
    ap.add_argument("--dir", required=True, help="页面目录（含 two_level_elements.json）")
    ap.add_argument("--out", default="", help="报告输出路径；缺省=<页面目录>/report.html")
    ap.add_argument("--title", default="", help="报告标题；中文建议改用 --title-file")
    ap.add_argument("--title-file", default="", help="UTF-8 文本文件，内容作为报告标题（推荐）")
    ap.add_argument("--img-width", type=int, default=380, help="预览图宽度（默认 380）")
    ap.add_argument("--quality", type=int, default=76, help="JPEG 质量（默认 76）")
    args = ap.parse_args()
    page_dir = Path(args.dir)
    if not (page_dir / "two_level_elements.json").is_file():
        raise SystemExit("页面目录里没有 two_level_elements.json，请先运行 build_layers.py：%s" % page_dir)
    out = Path(args.out) if args.out else page_dir / "report.html"
    print(json.dumps(build_html(page_dir, out, resolve_title(args), args.img_width, args.quality), ensure_ascii=False, indent=1))


if __name__ == "__main__":
    main()