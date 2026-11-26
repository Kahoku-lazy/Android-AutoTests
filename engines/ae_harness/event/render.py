from __future__ import annotations

import base64
import html
import json
import os

from collections.abc import Callable
from pathlib import Path

from .record import RunRecord, StepRecord

__all__ = ["HtmlReportRenderer"]

_REPO_ROOT = Path(__file__).resolve().parents[3]
_BRAND_MARK = _REPO_ROOT / "frontend" / "public" / "brand" / "ai-mark.png"
_BRAND_FONT = _REPO_ROOT / "frontend" / "public" / "fonts" / "ziku-feiyang.ttf"


def _relpath(target: Path, start: Path) -> str:
    try:
        return os.path.relpath(target, start).replace("\\", "/")
    except ValueError:
        return str(target).replace("\\", "/")


def _brand_font_src(fallback: str) -> str:
    try:
        data = _BRAND_FONT.read_bytes()
    except OSError:
        return fallback
    encoded = base64.b64encode(data).decode("ascii")
    return f"data:font/ttf;base64,{encoded}"


_EVENT_KIND = {
    "reply_start": ("log-start", "开始"),
    "ReplyStartEvent": ("log-start", "开始"),
    "phase": ("log-start", "阶段"),
    "HintBlockEvent": ("log-misc", "注入"),
    "ModelCallStartEvent": ("log-model", "模型"),
    "ModelCallEndEvent": ("log-model", "模型完成"),
    "TextBlockEndEvent": ("log-text", "文本"),
    "ThinkingBlockEndEvent": ("log-think", "思考"),
    "ToolCallStartEvent": ("log-tool", "调用"),
    "ToolCallEndEvent": ("log-tool", "入参"),
    "ToolResultStartEvent": ("log-result", "结果"),
    "ToolResultDataDeltaEvent": ("log-result", "图片"),
    "ToolResultEndEvent": ("log-result", "结果完"),
    "ReplyEndEvent": ("log-end", "结束"),
    "summary": ("log-end", "汇总"),
}

_TILTS = ("-.6deg", ".8deg", "-1.1deg", "1.2deg", "-.4deg", "1deg")

_CARET = '<span class="caret" aria-hidden="true">▸</span>'

_ORDINAL_MAX = 99

_ORDINAL_GLYPHS: dict[str, str] = {
    "0": "M13.5 4 C7 4 4 9.5 4 15.5 C4 22 7.5 27 13 27 C18.5 27 21.5 21.5 21.5 15.5 C21.5 9 18.5 4 13.5 4 Z",
    "1": "M9 10 L13.5 4.5 L13.5 27.5 M8 27.5 L19 27.5",
    "2": "M4.5 9.5 C4.5 5 8.5 3.5 12.5 3.5 C17 3.5 20 6.5 20 10.5 C20 13.5 17 16.5 12 20 L4.5 27.5 L21 27.5",
    "3": "M4.5 4.5 L20.5 4.5 L12.5 13 C17.5 13 21 16 21 20.5 C21 25.5 16.5 28.5 11 28.5 C7.5 28.5 4.5 26.5 4 23.5",
    "4": "M16.5 27.5 L16.5 4 L4 19 L21 19",
    "5": "M20 4.5 L6.5 4.5 L6 14.5 C9 12.5 15.5 12 19 15 C22 18 21.5 23.5 18 26.5 C15 29 9.5 29 5.5 26",
    "6": "M18.5 4 C11 4.5 5.5 10 5.5 18.5 C5.5 25 9.5 28.5 13.5 28.5 C18 28.5 20.5 25 20.5 21 C20.5 17.5 18 14.5 14 14.5 C10 14.5 7 16.5 5.5 19.5",
    "7": "M4.5 4.5 L21 4.5 L10.5 28",
    "8": (
        "M13 14.5 C8.5 14.5 5.5 11.5 5.5 8.5 C5.5 5 9 3.5 13 3.5 C17 3.5 20.5 5.5 20.5 9 "
        "C20.5 12 17 14.5 13 14.5 C8 14.5 4.5 17 4.5 21 C4.5 25.5 8.5 28.5 13 28.5 "
        "C17.5 28.5 21.5 25.5 21.5 21 C21.5 17 18 14.5 13 14.5"
    ),
    "9": "M7 27.5 C14 27 18.5 21.5 18.5 13.5 C18.5 7.5 15.5 3.5 11.5 3.5 C7.5 3.5 4.5 6.5 4.5 10.5 C4.5 14 7 17 11 17 C15.5 17 18.5 14 18.5 10",
}

_ORDINAL_DEFS = """<svg class="ord-defs" width="0" height="0" aria-hidden="true" focusable="false">
  <defs>
    <linearGradient id="ord-grad-red" gradientUnits="userSpaceOnUse" x1="4" y1="0" x2="24" y2="0">
      <stop offset="0" style="stop-color:var(--color-red-40);stop-opacity:.45"></stop>
      <stop offset="1" style="stop-color:var(--color-red-40);stop-opacity:.3"></stop>
    </linearGradient>
    <linearGradient id="ord-grad-blue" gradientUnits="userSpaceOnUse" x1="28" y1="0" x2="48" y2="0">
      <stop offset="0" style="stop-color:var(--color-blue-47);stop-opacity:.45"></stop>
      <stop offset="1" style="stop-color:var(--color-blue-47);stop-opacity:.3"></stop>
    </linearGradient>
    <filter id="ord-crayon" x="-14%" y="-14%" width="128%" height="128%">
      <feTurbulence type="fractalNoise" baseFrequency="0.82" numOctaves="3" seed="7" result="grain"></feTurbulence>
      <feDisplacementMap in="SourceGraphic" in2="grain" scale="2.6" xChannelSelector="R" yChannelSelector="G"></feDisplacementMap>
    </filter>
  </defs>
</svg>"""


def _ordinal_svg(value: int, label: str = "子目标") -> str:
    number = min(max(value, 1), _ORDINAL_MAX)
    shapes: list[str] = []
    for slot, digit in enumerate(f"{number:02d}"):
        path = _ORDINAL_GLYPHS[digit]
        shift = 3 + slot * 24
        tilt = -2.6 if slot == 0 else 1.8
        placement = f"translate({shift} 3) rotate({tilt} 10 15)"
        hue = "ord-red" if slot == 0 else "ord-blue"
        shapes.append(f'<path class="ord-soft {hue}" d="{path}" transform="{placement}"></path>')
        shapes.append(f'<path class="ord-ink {hue}" d="{path}" transform="{placement}"></path>')
    drawn = "".join(shapes)
    return f'<svg class="ord" viewBox="0 0 50 36" role="img" aria-label="第 {number} 个{label}">{drawn}</svg>'


_CSS = """
:root {
  --color-white:#f7f3e8;
  --color-lime-94:#f3efe2;   --color-orange-76:#d8d2c4;
  --color-indigo-13:#1e1e24; --color-indigo-76:#a78bfa;
  --color-yellow-70:#fcdc6b; --color-yellow-63:#f7c948;
  --color-green-61:#6bcb77;  --color-green-87:#c8f5d0;  --color-green-33:#2d7a31;
  --color-teal-49:#4ecdc4;   --color-cyan-74:#89cff0;   --color-red-83:#ffb5a7;
  --color-blue-27:#1a426f;   --color-teal-38:#16aea1;   --color-green-49:#4caf50;
  --color-red-69:#f56b6a;    --color-red-95:#ffe9e8;    --color-red-46:#b23838;
  --color-red-40:#b8354a;    --color-blue-47:#3a6fb0;
  --color-purple-73:#e879f9; --color-ink-47:#7c6f83;    --color-ink-57:#96918c;
  --color-ink-79:#c9cacc;    --color-ink-34:#5d5950;

  --ink:var(--color-indigo-13);  --paper:var(--color-lime-94);
  --app-bg-card:var(--color-white); --app-bg-subtle:var(--color-lime-94);
  --app-highlight:var(--color-yellow-70);
  --app-text-secondary:var(--color-ink-57); --app-stat-text:var(--color-ink-34);
  --c-dashboard:var(--color-yellow-63); --c-device:var(--color-green-61);
  --c-element:var(--color-indigo-76);   --c-case:var(--color-teal-49);
  --c-runner:var(--color-red-83);       --c-report:var(--color-ink-47);
  --c-ai:var(--color-purple-73);        --c-workflow:var(--color-cyan-74);

  --app-status-success-bg:var(--color-green-87); --app-status-success-text:var(--color-green-33);
  --app-status-danger-bg:var(--color-red-95);    --app-status-danger-text:var(--color-red-46);
  --app-marker-red:var(--color-red-69);          --app-offline:var(--color-ink-79);

  --app-font:"HarmonyOS Sans SC","PingFang SC","Noto Sans SC","Microsoft YaHei",system-ui,sans-serif;
  --app-font-mono:"Consolas","Cascadia Mono",ui-monospace,monospace;
  --app-size-xs:12px; --app-size-sm:14px; --app-size-md:16px;
  --app-size-lg:20px; --app-size-xl:24px; --app-size-2xl:32px;
  --app-space-xs:4px; --app-space-sm:8px; --app-space-md:16px;
  --app-space-lg:24px; --app-space-xl:32px; --app-space-2xl:48px;
  --app-radius-sm:4px 8px; --app-radius-md:6px 10px; --app-radius-lg:8px 14px;
  --app-radius-pill:4px 10px 6px 8px; --app-radius-table:4px 10px;
  --app-shadow-sm:2px 2px 0 rgba(0,0,0,.04);
  --app-shadow-md:2px 3px 0 rgba(0,0,0,.05);
  --app-duration-fast:.12s; --app-duration:.15s; --app-duration-slow:.25s;
  --app-ease:cubic-bezier(.25,.1,.25,1);
  --app-topbar-h:88px;
  /* 侧栏默认占三成宽；上下限与「右侧仍要留多少」由脚本按容器实时夹取。 */
  --side-w:30%; --side-min:220px; --side-max:760px;
}
* { box-sizing: border-box; }
body {
  margin: 0; font-family: var(--app-font); font-size: var(--app-size-sm);
  color: var(--ink); background: var(--paper); line-height: 1.6;
}
.shell { display: flex; min-height: 100vh; }
.sidebar {
  width: var(--side-w); min-width: var(--side-min); max-width: var(--side-max);
  flex-shrink: 0; height: 100vh; position: sticky; top: 0;
  background: var(--paper); padding: 20px 16px; overflow: auto;
}
/* 分栏手柄：契约照平台 shared/components/SplitHandle.vue——8px 命中区 + 居中 2px 线，
   常态暖灰，hover / 拖拽转墨色，键盘聚焦另给一圈描边，窄屏（两栏并排失效）不渲染。 */
.splitter {
  position: relative; flex: 0 0 8px; cursor: col-resize;
  background: transparent; touch-action: none;
}
.splitter::before {
  content: ""; position: absolute; top: 0; bottom: 0; left: 3px; width: 2px;
  background: var(--color-orange-76);
  transition: background var(--app-duration-fast) var(--app-ease);
}
.splitter:hover::before, .splitter.is-dragging::before { background: var(--ink); }
.splitter:focus-visible { outline: 2px solid var(--c-dashboard); outline-offset: -2px; }
.main { flex: 1 1 auto; min-width: 0; display: flex; flex-direction: column; position: relative; }
.main__doodles { position: absolute; inset: 0; overflow: hidden; pointer-events: none; z-index: 0; }
.main__body { position: relative; z-index: 1; flex: 1 1 0; min-height: 0; overflow-y: auto; }
.wb-header {
  position: sticky; z-index: 10; min-height: var(--app-topbar-h);
  padding: var(--app-space-sm) var(--app-space-lg); background: var(--paper);
  border-bottom: 2.5px solid var(--ink); display: flex; align-items: center; gap: var(--app-space-md);
}
.doc-body { padding: var(--app-space-lg) var(--app-space-xl) var(--app-space-2xl); }

@font-face {
  font-family: "Ziku FeiYang";
  font-style: normal;
  font-weight: 400;
  font-display: swap;
  src: url("__FONT_SRC__") format("truetype");
}
.brand { display: flex; align-items: center; gap: 10px; padding-bottom: 14px; border-bottom: 2px solid var(--ink); }
.brand-mark {
  flex: 0 0 auto; width: 32px; height: 32px; object-fit: contain;
  border-radius: 8px; mix-blend-mode: multiply;
}
.brand-title {
  display: block;
  font-family: "Ziku FeiYang", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: var(--app-size-lg);
  font-weight: 400;
  letter-spacing: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  color: var(--ink);
}
.brand-accent {
  background-image: linear-gradient(
    100deg,
    var(--color-blue-27) 0%,
    var(--color-teal-38) 52%,
    var(--color-green-49) 100%
  );
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  -webkit-text-stroke: 0.35px color-mix(in srgb, var(--ink) 40%, transparent);
}
.task {
  margin-top: 16px; background: var(--app-bg-card); border: 2.5px solid var(--ink);
  border-radius: 2px; box-shadow: 3px 3px 0 0 var(--app-highlight);
  padding: 10px 12px; transform: rotate(-.6deg);
}
.task .k { font-size: var(--app-size-xs); letter-spacing: .06em; text-transform: uppercase; color: var(--app-text-secondary); }
.task .v { font-size: var(--app-size-sm); margin-top: 4px; }
.check-card {
  background: var(--app-bg-card); border: 2.5px solid var(--ink);
  border-radius: 2px; box-shadow: 3px 3px 0 0 var(--c-device);
  padding: 10px 12px; margin-bottom: 16px; transform: rotate(.4deg);
}
.check-card .k {
  font-size: var(--app-size-xs); letter-spacing: .06em;
  text-transform: uppercase; color: var(--app-text-secondary);
}
.check-card ol { margin: 6px 0 0; padding-left: 18px; }
.check-card li { font-size: var(--app-size-sm); margin-bottom: 6px; }
.check-card li:last-child { margin-bottom: 0; }
.check-card li b { display: block; }
.check-card li span { color: var(--app-text-secondary); }
.stats { display: grid; grid-template-columns: 1fr 1fr; gap: 10px; margin: 16px 0; }
.kpi {
  text-align: center; background: var(--app-bg-card); border: 2.5px solid var(--ink);
  border-radius: 2px; padding: 10px 8px;
  box-shadow: 3px 3px 0 0 var(--kpi, var(--c-dashboard));
  transform: rotate(var(--tilt, -.8deg));
  transition: transform var(--app-duration) var(--app-ease);
}
.kpi:hover { transform: rotate(0) translate(-1px, -1px); }
.kpi em { display: block; font-style: normal; font-size: var(--app-size-xs); letter-spacing: .06em; text-transform: uppercase; color: var(--app-text-secondary); }
.kpi strong { font-family: var(--app-font-mono); font-size: var(--app-size-lg); font-weight: 800; }
.kpi strong.bad { color: var(--app-status-success-text); }
.label { font-size: var(--app-size-xs); letter-spacing: .08em; text-transform: uppercase; color: var(--app-text-secondary); margin-bottom: 8px; }
.token-card {
  background: var(--app-bg-card); border: 2.5px solid var(--ink); border-radius: 2px;
  box-shadow: 3px 3px 0 0 var(--c-workflow); padding: 10px 12px;
  transform: rotate(.5deg); margin-bottom: 16px;
}
.token-card .k { font-size: var(--app-size-xs); letter-spacing: .06em; text-transform: uppercase; color: var(--app-text-secondary); margin-bottom: 6px; }
.token-card .row { display: flex; justify-content: space-between; align-items: baseline; font-size: var(--app-size-sm); padding: 3px 0; }
.token-card .row b { font-family: var(--app-font-mono); font-size: var(--app-size-sm); font-weight: 800; }
.token-card .row.total { border-top: 2px solid var(--ink); margin-top: 4px; padding-top: 6px; }
.token-card .row.total b { font-size: var(--app-size-md); }
.side-list { list-style: none; margin: 0 0 16px; padding: 0; font-size: var(--app-size-sm); }
.side-list li { display: flex; justify-content: space-between; gap: 8px; padding: 4px 0; border-bottom: 1px solid color-mix(in srgb, var(--ink) 12%, transparent); }
.side-list li:last-child { border-bottom: 0; }
.side-list b { font-family: var(--app-font-mono); font-weight: 700; }
.task-box p { margin: 0; font-size: var(--app-size-sm); color: var(--app-text-secondary); word-break: break-word; }

.wb-title {
  font-family: "Ziku FeiYang", "Noto Sans SC", "PingFang SC", "Microsoft YaHei", sans-serif;
  font-size: var(--app-size-xl); font-weight: 400; margin: 0; letter-spacing: 0;
  white-space: nowrap; color: var(--ink);
}
.pill {
  font-size: var(--app-size-xs); padding: 2px 10px; border: 2px solid var(--ink);
  border-radius: var(--app-radius-pill); background: var(--app-status-success-bg);
  color: var(--app-status-success-text); font-weight: 700;
}
.tabs { display: inline-flex; gap: 6px; margin-left: auto; }
.btn {
  min-height: 32px; padding: 0 14px; border: 2.5px solid var(--ink); border-radius: 2px;
  background: var(--paper); font: 800 var(--app-size-sm)/1 var(--app-font); color: var(--ink);
  box-shadow: 3px 3px 0 0 var(--ink); cursor: pointer; text-decoration: none;
  transition: transform var(--app-duration-fast) var(--app-ease), box-shadow var(--app-duration-fast) var(--app-ease);
}
.btn:hover { transform: translate(-1px, -1px); box-shadow: 4px 4px 0 0 var(--ink); }
.btn:active { transform: translate(2px, 2px); box-shadow: 1px 1px 0 0 var(--ink); }
.btn.active { background: var(--c-dashboard); }

.view { display: none; }
.view.active { display: block; }

/* 折叠：标题行是真 <button>（自带键盘与 aria 语义），它所在的盒子带 .fold-box；
   盒子同时带 .is-open 时，直接子级 .fold-b 才显示。
   子目标 / 角色块 / 工具卡 / 轨迹行四层共用这一套规则，靠「直接子级」限定，嵌套时不会互相串开。 */
.fold-box.is-open > .fold-b { display: block; }
.fold-h {
  display: flex; align-items: center; gap: 10px; width: 100%; margin: 0; padding: 0;
  border: 0; background: none; color: inherit; font: inherit; text-align: left;
  cursor: pointer; border-radius: var(--app-radius-sm);
}
.fold-h:hover { background: color-mix(in srgb, var(--ink) 5%, transparent); }
.caret {
  flex: 0 0 auto; width: 12px; text-align: center;
  font-size: var(--app-size-xs); color: var(--app-text-secondary);
}
.fold-b { display: none; }

/* 子目标序号：SVG 描边数字，左位红、右位蓝，各自浓度 45% → 30%，再叠湍流毛边，
   模拟蜡笔手写（参考需求方给的手绘 AE 图）。淡墨层比主笔画粗，只做蜡迹扩散。 */
.ord-defs { position: absolute; width: 0; height: 0; overflow: hidden; }
.ord { flex: 0 0 auto; height: 24px; width: auto; display: block; }
.ord path { fill: none; stroke-linecap: round; stroke-linejoin: round; filter: url(#ord-crayon); }
.ord .ord-soft { stroke-width: 8.4; opacity: .55; }
.ord .ord-ink { stroke-width: 5.2; }
.ord .ord-red { stroke: url(#ord-grad-red); }
.ord .ord-blue { stroke: url(#ord-grad-blue); }

.phase { margin-bottom: var(--app-space-lg); }
.phase-h { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.phase-h h3 { flex: 1 1 auto; min-width: 0; font-size: var(--app-size-md); margin: 0; font-weight: 800; }
.phase-h em { font-style: normal; font-size: var(--app-size-xs); color: var(--app-text-secondary); font-family: var(--app-font-mono); }
.role-block {
  border-left: 3px solid var(--role-accent, var(--c-dashboard));
  padding-left: 12px; margin-bottom: 14px;
}
.role-h { margin-bottom: 8px; }
.role-label {
  display: inline-block; font-size: var(--app-size-xs); font-weight: 800;
  letter-spacing: .06em; text-transform: uppercase;
  background: var(--role-accent, var(--c-dashboard));
  border: 2px solid var(--ink); border-radius: var(--app-radius-pill);
  padding: 1px 10px;
}

.card {
  position: relative; background: var(--app-bg-card); border: 2.5px solid var(--ink);
  border-radius: 2px; padding: 14px 16px; margin-bottom: 12px;
  box-shadow: 4px 4px 0 0 var(--ac-accent, var(--c-dashboard));
  transform: rotate(var(--tilt, .3deg));
  transition: transform var(--app-duration) var(--app-ease), box-shadow var(--app-duration) var(--app-ease);
}
.card:hover { transform: rotate(0) translate(-1px, -1px); box-shadow: 5px 5px 0 0 var(--ac-accent, var(--c-dashboard)); }
.card-h { display: flex; align-items: center; gap: 10px; }
.no {
  width: 26px; height: 26px; flex: 0 0 26px; border: 2.5px solid var(--ink); border-radius: 2px;
  background: var(--app-highlight); font-size: var(--app-size-xs); font-weight: 800;
  display: inline-flex; align-items: center; justify-content: center;
}
.tool { font-family: var(--app-font-mono); font-size: var(--app-size-md); font-weight: 700; }
.t { font-family: var(--app-font-mono); font-size: var(--app-size-xs); color: var(--app-text-secondary); }
.t.ml { margin-left: auto; }
.note { background: var(--app-bg-subtle); border-left: 4px solid var(--c-element); border-radius: 2px; padding: 8px 10px; margin: 10px 0; font-size: var(--app-size-sm); }
.code {
  background: #fff; border: 2px solid var(--ink); border-radius: var(--app-radius-sm);
  padding: 8px 10px; margin: 6px 0; font-family: var(--app-font-mono);
  font-size: var(--app-size-sm); white-space: pre-wrap; word-break: break-all;
}
.code b { font-family: var(--app-font); font-weight: 800; margin-right: 6px; }
.thumb { display: inline-block; margin-top: 8px; cursor: zoom-in; }
.thumb img { display: block; border: 2px solid var(--ink); border-radius: 2px; box-shadow: 2px 2px 0 0 var(--ink); max-width: 160px; }
table.marks { border-collapse: collapse; font-family: var(--app-font-mono); font-size: var(--app-size-sm); margin: 8px 0; }
table.marks th, table.marks td { border: 2px solid var(--ink); padding: 3px 12px; text-align: center; }
table.marks th { background: var(--app-bg-subtle); font-size: var(--app-size-md); font-weight: 800; }
.final {
  background: var(--app-bg-card); border: 2.5px solid var(--ink); border-radius: 2px;
  box-shadow: 4px 4px 0 0 var(--c-case); padding: 14px 16px; white-space: pre-wrap;
  transform: rotate(-.3deg);
}

.chart-card {
  background: var(--app-bg-card); border: 2.5px solid var(--ink); border-radius: 2px;
  padding: 14px 16px; margin-bottom: 14px;
  box-shadow: 4px 4px 0 0 var(--c-workflow); transform: rotate(.4deg);
}
.chart-card h4 { margin: 0 0 10px; font-size: var(--app-size-md); font-weight: 800; display: flex; gap: 8px; align-items: center; }
.legend { display: flex; gap: 14px; font-size: var(--app-size-xs); color: var(--app-text-secondary); margin-left: auto; }
.legend i { display: inline-block; width: 14px; height: 10px; border: 2px solid var(--ink); margin-right: 4px; vertical-align: -1px; }
.timeline { margin-top: 4px; }
.tl-row { display: grid; grid-template-columns: 44px 1fr; gap: 8px; align-items: center; margin-bottom: 6px; }
.tl-label { font-size: var(--app-size-xs); color: var(--app-text-secondary); text-align: right; }
.tl-track { position: relative; height: 20px; background: var(--paper); border: 2px solid var(--ink); border-radius: 2px; }
.tl-bar {
  position: absolute; top: 2px; bottom: 2px; border: 2px solid var(--ink);
  border-radius: 1px; cursor: pointer; transition: filter var(--app-duration-fast) var(--app-ease);
}
.tl-bar.model { background: var(--c-element); }
.tl-bar.tool { background: var(--c-device); }
.tl-bar:hover { filter: brightness(1.12); }
.tl-axis { display: grid; grid-template-columns: 44px 1fr; gap: 8px; margin-top: 4px; }
.tl-axis-track { position: relative; height: 14px; font-family: var(--app-font-mono); font-size: var(--app-size-xs); color: var(--app-text-secondary); }
.tl-tick { position: absolute; transform: translateX(-50%); white-space: nowrap; }

.calls { background: var(--app-bg-card); border: 2.5px solid var(--ink); border-radius: 2px; overflow: hidden; box-shadow: 4px 4px 0 0 var(--c-device); }
.call { border-bottom: 2px solid var(--ink); }
.call:last-child { border-bottom: 0; }
.call-h { display: flex; align-items: center; gap: 10px; height: 40px; padding: 0 14px; cursor: pointer; }
.call-h:hover { background: var(--paper); }
.badge { font-size: var(--app-size-xs); font-weight: 700; padding: 1px 8px; border: 2px solid var(--ink); border-radius: var(--app-radius-pill); }
.badge.m { background: var(--c-element); }
.badge.t { background: var(--c-device); }
.call-n { font-family: var(--app-font-mono); font-size: var(--app-size-sm); }
.call-m { margin-left: auto; font-family: var(--app-font-mono); font-size: var(--app-size-xs); color: var(--app-text-secondary); }
.trace-body { padding: 0 14px 12px; }
.ctabs { display: flex; gap: 6px; margin-bottom: 8px; flex-wrap: wrap; }
.ctabs button {
  border: 2px solid var(--ink); background: #fff; color: var(--ink);
  font-size: var(--app-size-xs); padding: 0 10px; height: 26px;
  border-radius: var(--app-radius-sm); cursor: pointer; font-family: inherit; font-weight: 700;
}
.ctabs button.active { background: var(--c-dashboard); }
.cpanel { display: none; }
.cpanel.active { display: block; }
.cpanel pre {
  margin: 0; padding: 9px 11px; background: var(--paper); border: 2px solid var(--ink);
  border-radius: var(--app-radius-sm); font-family: var(--app-font-mono);
  font-size: var(--app-size-sm); white-space: pre-wrap; word-break: break-all;
}

/* 事件流的「时间 / 类型 / 字段」三列由 .log 统一分配，行内用 subgrid 继承同一套列轨道：
   类型列按最长标签取宽（max-content），标签再长也不许压到右边的字段文本上。 */
.log {
  background: var(--app-bg-card); border: 2.5px solid var(--ink); border-radius: 2px;
  padding: 4px 14px; box-shadow: 4px 4px 0 0 var(--c-report);
  display: grid; grid-template-columns: 92px max-content minmax(0, 1fr); column-gap: 10px;
}
.log-row {
  grid-column: 1 / -1; display: grid;
  grid-template-columns: 92px 78px minmax(0, 1fr); /* 不支持 subgrid 时的退路 */
  grid-template-columns: subgrid;
  column-gap: 10px; padding: 7px 0;
  border-bottom: 1px solid color-mix(in srgb, var(--ink) 12%, transparent);
  font-size: var(--app-size-sm); align-items: start;
}
.log-row:last-child { border-bottom: 0; }
/* 时间列是「时间/日期 = 12」那一档，字段正文才是 14。 */
.log-t { font-size: var(--app-size-xs); color: var(--app-text-secondary); font-family: var(--app-font-mono); text-align: right; }
.log-badge {
  justify-self: start; max-width: 168px;
  padding: 1px 8px; border: 2px solid var(--ink); border-radius: var(--app-radius-pill);
  font-size: var(--app-size-xs); font-weight: 700; text-align: center;
  white-space: normal; overflow-wrap: anywhere;
}
.log-body { display: flex; flex-wrap: wrap; gap: 6px 14px; color: var(--app-text-secondary); word-break: break-all; }
.kv i { font-style: normal; color: var(--app-text-secondary); margin-right: 4px; }
details.kv { width: 100%; }
details.kv summary { cursor: pointer; color: var(--app-text-secondary); }
details.kv pre { margin: 4px 0 0; padding: 8px; background: var(--paper); border: 2px solid var(--ink); border-radius: var(--app-radius-sm); white-space: pre-wrap; word-break: break-all; font-size: var(--app-size-sm); }
.log-model .log-badge { background: var(--c-element); }
.log-tool .log-badge { background: var(--c-device); }
.log-result .log-badge { background: var(--c-workflow); }
.log-think .log-badge { background: var(--c-ai); }
.log-text .log-badge { background: var(--app-bg-subtle); }
.log-start .log-badge, .log-end .log-badge { background: var(--c-dashboard); }
.log-misc .log-badge { background: var(--color-ink-79); }
.raw-box summary { cursor: pointer; color: var(--app-text-secondary); font-size: var(--app-size-xs); margin-bottom: 10px; }
.tip { font-size: var(--app-size-sm); color: var(--app-text-secondary); margin: 0 0 14px; }

.drawer {
  position: fixed; top: 0; right: 0; width: 440px; max-width: 100vw; height: 100vh;
  background: #fff; border-left: 2.5px solid var(--ink); box-shadow: -6px 0 0 0 var(--ink);
  transform: translateX(100%); transition: transform var(--app-duration-slow) var(--app-ease);
  display: flex; flex-direction: column; z-index: 90;
}
.drawer.open { transform: translateX(0); }
.dh { display: flex; align-items: center; gap: 10px; padding: 14px 16px; border-bottom: 2.5px solid var(--ink); background: var(--paper); }
.dh b { font-family: var(--app-font-mono); font-size: var(--app-size-sm); }
.dh span { font-family: var(--app-font-mono); font-size: var(--app-size-xs); color: var(--app-text-secondary); margin-left: auto; }
.dh button {
  border: 2.5px solid var(--ink); background: #fff; width: 28px; height: 28px;
  border-radius: 2px; cursor: pointer; font-size: var(--app-size-md); line-height: 1;
  font-weight: 800; box-shadow: 2px 2px 0 0 var(--ink);
}
.dh button:hover { background: var(--app-highlight); }
.db { padding: 14px 16px; overflow: auto; flex: 1; }

:focus-visible { outline: 3px solid var(--c-element); outline-offset: 2px; }
@media (prefers-reduced-motion: reduce) {
  .btn, .card, .kpi, .drawer, .call-h { transition: none; transform: none; }
  .splitter::before { transition: none; }
  .card:hover, .kpi:hover, .btn:hover { transform: none; }
}
@media (max-width: 900px) {
  .shell { flex-direction: column; }
  .sidebar {
    width: 100%; min-width: 0; max-width: none; height: auto; position: static;
    border-bottom: 2.5px solid var(--ink);
  }
  /* 两栏退化成单栏后没有可拖的分界，手柄不渲染。 */
  .splitter { display: none; }
  .main__body { overflow: visible; }
  .doc-body { padding: 16px; }
  .drawer { width: 100vw; }
}
"""

_SCRIPT = """
function zoomShot(src) {
  document.getElementById("big").src = src;
  document.getElementById("overlay").style.display = "flex";
}
/* 折叠只认一个状态源：折叠盒上的 is-open 类。aria-expanded 与箭头字形跟着它走，
   报告区三层与轨迹区调用行共用这一个函数，避免样式与状态两套写法打架。
   标题行是真 <button>，Enter / Space 由浏览器原生转成 click，不再自己处理按键。 */
function toggleFold(head) {
  const box = head.closest(".fold-box");
  if (!box) { return; }
  const open = box.classList.toggle("is-open");
  head.setAttribute("aria-expanded", open ? "true" : "false");
  const caret = head.querySelector(".caret");
  if (caret) { caret.textContent = open ? "\u25be" : "\u25b8"; }
}
function switchTab(btn) {
  const box = btn.closest(".trace-body") || btn.closest(".db");
  box.querySelectorAll(".ctabs button").forEach(function (item) {
    item.classList.remove("active");
  });
  btn.classList.add("active");
  const name = btn.dataset.tab;
  box.querySelectorAll(".cpanel").forEach(function (panel) {
    panel.classList.toggle("active", panel.dataset.panel === name);
  });
}
function openDrawer(index) {
  const item = document.getElementById("span-" + index);
  if (!item) { return; }
  const drawer = document.getElementById("drawer");
  document.getElementById("d-name").textContent =
    item.querySelector(".call-n").textContent;
  document.getElementById("d-meta").textContent =
    item.querySelector(".call-m").textContent;
  const body = item.querySelector(".trace-body");
  document.getElementById("d-body").innerHTML =
    body ? body.innerHTML : '<div class="cpanel active"><div class="code">该调用没有详情。</div></div>';
  drawer.querySelectorAll(".cpanel").forEach(function (p, i) {
    p.classList.toggle("active", i === 0);
  });
  drawer.querySelectorAll(".ctabs button").forEach(function (b, i) {
    b.classList.toggle("active", i === 0);
  });
  drawer.classList.add("open");
}
function closeDrawer() {
  document.getElementById("drawer").classList.remove("open");
}
/* 侧栏宽度：默认三成，拖手柄改宽。契约照平台 shared/components/SplitHandle.vue——
   下限 220px，上限取 min(760px, 容器宽 - 480px)，右侧正文永不被压没；
   拖拽期间 body 走 col-resize 且不可选；←/→ 16px（按住 Shift 48px）、Home/End 到两端、
   双击回三成。宽度落 localStorage，取不到（file:// 等）就退回默认三成。 */
function initSplitter() {
  const splitter = document.getElementById("splitter");
  const shell = document.querySelector(".shell");
  const sidebar = document.querySelector(".sidebar");
  if (!splitter || !shell || !sidebar) { return; }
  const MIN = 220;
  const MAX = 760;
  const RIGHT_MIN = 480;
  const DEFAULT_RATIO = .3;
  const STORE_KEY = "agent-report-side-w";
  let dragging = false;
  function bounds() {
    const room = shell.getBoundingClientRect().width - RIGHT_MIN;
    return { min: MIN, max: Math.max(MIN, Math.min(MAX, room)) };
  }
  function clamp(value) {
    const limit = bounds();
    return Math.round(Math.min(limit.max, Math.max(limit.min, value)));
  }
  function remember(value) {
    try { window.localStorage.setItem(STORE_KEY, String(value)); } catch (error) { return; }
  }
  function recall() {
    try {
      const saved = Number(window.localStorage.getItem(STORE_KEY));
      return saved > MIN ? saved : 0;
    } catch (error) { return 0; }
  }
  function apply(value, commit) {
    const next = clamp(value);
    const limit = bounds();
    document.documentElement.style.setProperty("--side-w", next + "px");
    splitter.setAttribute("aria-valuenow", String(next));
    splitter.setAttribute("aria-valuemin", String(limit.min));
    splitter.setAttribute("aria-valuemax", String(limit.max));
    if (commit) { remember(next); }
  }
  splitter.addEventListener("mousedown", function (event) {
    if (event.button !== 0) { return; }
    event.preventDefault();
    dragging = true;
    splitter.classList.add("is-dragging");
    document.body.style.cursor = "col-resize";
    document.body.style.userSelect = "none";
  });
  window.addEventListener("mousemove", function (event) {
    if (!dragging) { return; }
    apply(event.clientX - shell.getBoundingClientRect().left, false);
  });
  window.addEventListener("mouseup", function () {
    if (!dragging) { return; }
    dragging = false;
    splitter.classList.remove("is-dragging");
    document.body.style.cursor = "";
    document.body.style.userSelect = "";
    apply(sidebar.getBoundingClientRect().width, true);
  });
  splitter.addEventListener("keydown", function (event) {
    const step = event.shiftKey ? 48 : 16;
    const current = sidebar.getBoundingClientRect().width;
    let next = null;
    if (event.key === "ArrowLeft") { next = current - step; }
    else if (event.key === "ArrowRight") { next = current + step; }
    else if (event.key === "Home") { next = bounds().min; }
    else if (event.key === "End") { next = bounds().max; }
    if (next === null) { return; }
    event.preventDefault();
    apply(next, true);
  });
  splitter.addEventListener("dblclick", function () {
    apply(shell.getBoundingClientRect().width * DEFAULT_RATIO, true);
  });
  window.addEventListener("resize", function () {
    if (window.innerWidth <= 900) { return; }
    apply(sidebar.getBoundingClientRect().width, false);
  });
  apply(recall() || shell.getBoundingClientRect().width * DEFAULT_RATIO, false);
}
document.querySelectorAll(".tabs .btn").forEach(function (link) {
  link.addEventListener("click", function (event) {
    event.preventDefault();
    document.querySelectorAll(".tabs .btn").forEach(function (item) {
      item.classList.remove("active");
    });
    link.classList.add("active");
    document.querySelectorAll(".view").forEach(function (view) { view.classList.remove("active"); });
    document.getElementById("view-" + link.dataset.view).classList.add("active");
    document.querySelector(".main__body").scrollTop = 0;
  });
});
function openListView(name) {
  document.querySelectorAll(".tabs .btn").forEach(function (item) {
    item.classList.toggle("active", item.dataset.view === name);
  });
  document.querySelectorAll(".view").forEach(function (view) { view.classList.remove("active"); });
  document.getElementById("view-" + name).classList.add("active");
}
function loadPlatformFont() {
  let origin = "";
  try { origin = new URL(location.href).origin; } catch (error) { return; }
  if (origin.indexOf("http") !== 0) { return; }
  if (document.getElementById("platform-font")) { return; }
  const style = document.createElement("style");
  style.id = "platform-font";
  style.textContent = '@import url("' + origin + '/fonts/harmonyos-sans/harmonyos-sans.css");';
  document.head.appendChild(style);
}
loadPlatformFont();
initSplitter();
"""


def _thumb_base64(raw: str, long_side: int, quality: int) -> str:
    try:
        import base64

        from io import BytesIO

        from PIL import Image
    except ImportError:
        return raw
    try:
        data = base64.b64decode(raw)
        with Image.open(BytesIO(data)) as opened:
            opened.load()
            image = opened.convert("RGB")
    except (ValueError, OSError):
        return raw
    if max(image.size) > long_side:
        scale = long_side / max(image.size)
        image = image.resize(
            (max(1, round(image.width * scale)), max(1, round(image.height * scale))),
            Image.LANCZOS,
        )
    buffer = BytesIO()
    image.save(buffer, format="JPEG", quality=quality)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


class HtmlReportRenderer:
    def __init__(
        self,
        *,
        thumb_long_side: int = 1600,
        thumb_quality: int = 85,
        step_extras: dict[str, Callable[[StepRecord], str]] | None = None,
    ) -> None:
        self.thumb_long_side = thumb_long_side
        self.thumb_quality = thumb_quality
        self.step_extras = dict(step_extras or {})

    def _brand_mark(self) -> str:
        try:
            data = _BRAND_MARK.read_bytes()
        except OSError:
            return (
                '<svg class="brand-mark" width="32" height="32" viewBox="0 0 32 32" '
                'fill="none" aria-hidden="true"><rect x="2" y="2" width="28" height="28" '
                'rx="8" fill="#fff" stroke="#16aea1" stroke-width="2.5"/>'
                '<text x="16" y="22" text-anchor="middle" font-size="12" '
                'font-weight="800" fill="#16aea1">AI</text></svg>'
            )
        encoded = base64.b64encode(data).decode("ascii")
        return (
            f'<img class="brand-mark" src="data:image/png;base64,{encoded}" '
            'alt="" aria-hidden="true">'
        )

    def _sidebar(self, record: RunRecord) -> str:
        summary = record.summary
        by_tool = "".join(
            f"<li><span>{html.escape(name)}</span><b>{count}</b></li>"
            for name, count in sorted(summary.get("by_tool", {}).items())
        )
        tokens = summary.get("tokens") or {}
        total_tokens = int(tokens.get("input", 0)) + int(tokens.get("output", 0))
        checks = "".join(
            f"<li><b>{html.escape(str(step.get('subject', '')))}</b>"
            f"<span>{html.escape(str(step.get('description', '')))}</span></li>"
            for step in record.sop_steps
        )
        check_block = (
            f'<div class="check-card"><div class="k">验收事项</div><ol>{checks}</ol></div>'
            if checks
            else ""
        )
        return f"""<aside class="sidebar">
    <div class="brand">
      {self._brand_mark()}
      <span class="brand-title"><span class="brand-accent">AGENT</span>可视化报告</span>
    </div>
    <div class="task"><div class="k">任务</div><div class="v">{html.escape(record.task)}</div></div>
    {check_block}
    <div class="stats">
      <div class="kpi" style="--tilt:-.8deg;--kpi:var(--c-dashboard)"><em>耗时</em><strong>{record.cost_s:.2f}s</strong></div>
      <div class="kpi" style="--tilt:.9deg;--kpi:var(--c-element)"><em>工具</em><strong>{summary.get("tool_calls", 0)}</strong></div>
      <div class="kpi" style="--tilt:1.1deg;--kpi:var(--c-device)"><em>失败</em><strong class="bad">{summary.get("failed", 0)}</strong></div>
      <div class="kpi" style="--tilt:-1.2deg;--kpi:var(--c-case)"><em>截图</em><strong>{summary.get("screenshots", 0)}</strong></div>
    </div>
    <div class="token-card">
      <div class="k">Token 消耗</div>
      <div class="row"><span>输入</span><b>{int(tokens.get("input", 0)):,}</b></div>
      <div class="row"><span>输出</span><b>{int(tokens.get("output", 0)):,}</b></div>
      <div class="row"><span>缓存命中</span><b>{int(tokens.get("cache_hit", 0)):,}</b></div>
      <div class="row total"><span>总计</span><b>{total_tokens:,}</b></div>
    </div>
    <div class="label">工具分布</div>
    <ul class="side-list">{by_tool or "<li><span>无</span><b>0</b></li>"}</ul>
  </aside>"""

    def _report(self, record: RunRecord) -> str:
        groups: list[tuple[str, list[StepRecord]]] = []
        for step in record.steps:
            key = step.sop_step or step.phase or "未分组"
            if not groups or groups[-1][0] != key:
                groups.append((key, []))
            groups[-1][1].append(step)

        body: list[str] = [_ORDINAL_DEFS]
        for ordinal, (name, steps) in enumerate(groups, start=1):
            body.append('<div class="phase fold-box">')
            body.append(
                '<div class="phase-h"><h3>'
                '<button type="button" class="fold-h" aria-expanded="false" '
                'onclick="toggleFold(this)">'
                f"{_CARET}{_ordinal_svg(ordinal)}{html.escape(name)}</button></h3>"
                f"<em>{len(steps)} 次调用</em></div>"
            )
            body.append('<div class="phase-b fold-b">')
            blocks: list[tuple[str, list[StepRecord]]] = []
            for step in steps:
                role = step.agent_role or ""
                if not blocks or blocks[-1][0] != role:
                    blocks.append((role, []))
                blocks[-1][1].append(step)

            for role, items in blocks:
                if role:
                    label = "执行者" if role == "executor" else "验收者"
                    accent = "--c-case" if role == "executor" else "--c-device"
                    body.append(
                        f'<div class="role-block fold-box" style="--role-accent:var({accent})">'
                        '<button type="button" class="role-h fold-h" aria-expanded="false" '
                        'onclick="toggleFold(this)">'
                        f'{_CARET}<span class="role-label">{label}</span></button>'
                        '<div class="role-b fold-b">'
                    )
                    for step in items:
                        body.append(self._step(step))
                    body.append("</div></div>")
                else:
                    for step in items:
                        body.append(self._step(step))
            body.append("</div>")
            body.append("</div>")
        if record.final_text:
            body.append(f'<div class="final">{html.escape(record.final_text)}</div>')
        return "\n".join(body)

    def _step(self, step: StepRecord) -> str:
        note = " ".join(step.note.split())
        tilt = _TILTS[(step.index - 1) % len(_TILTS)]
        parts: list[str] = [
            f'<article class="card fold-box" style="--tilt:{tilt};--ac-accent:var(--c-{"element" if step.index % 2 else "device"})">'
        ]
        parts.append(
            '<button type="button" class="card-h fold-h" aria-expanded="false" '
            'onclick="toggleFold(this)">'
            f'{_CARET}<span class="no">{step.index}</span>'
            f'<span class="tool">{html.escape(step.tool)}</span>'
            f'<span class="t ml">{step.span_ms or step.t_ms} ms</span></button>'
        )
        parts.append('<div class="card-b fold-b">')
        if note:
            parts.append(f'<p class="note">{html.escape(note[:400])}</p>')
        if step.input and step.input != "{}":
            parts.append(f'<div class="code"><b>入参</b>{html.escape(step.input)}</div>')

        extra = self.step_extras.get(step.tool)
        if extra is not None:
            parts.append(extra(step))
        elif step.output:
            parts.append(f'<div class="code"><b>结果</b>{html.escape(step.output[:600])}</div>')

        for image in step.images:
            thumb = _thumb_base64(image, self.thumb_long_side, self.thumb_quality)
            parts.append(
                f'<span class="thumb" role="button" tabindex="0" aria-label="放大截图" '
                f"onclick=\"zoomShot(this.querySelector('img').src)\" "
                f"onkeydown=\"if(event.key==='Enter'||event.key===' '){{event.preventDefault();this.click();}}\">"
                f'<img src="data:image/jpeg;base64,{thumb}" alt="第 {step.index} 步截图"></span>'
            )
        parts.append("</div>")
        parts.append("</article>")
        return "\n".join(parts)

    def _trace_detail(self, step: StepRecord, record: RunRecord) -> str:
        schema = record.schemas.get(step.tool)
        note = " ".join(step.note.split())
        overview = (
            f"阶段：{html.escape(step.phase or '未分组')}\n"
            f"轮次：第 {step.round_index} 轮\n"
            f"耗时：{step.span_ms} ms\n"
            f"状态：{html.escape(step.state)}\n"
            f"意图：{html.escape(note[:300]) or '（无）'}"
        )
        schema_text = (
            json.dumps(schema, ensure_ascii=False, indent=2)
            if schema
            else "（该工具没有登记 schema）"
        )
        return f"""<div class="trace-body fold-b">
      <div class="ctabs">
        <button class="active" data-tab="overview" onclick="switchTab(this)">概述</button>
        <button data-tab="input" onclick="switchTab(this)">参数</button>
        <button data-tab="output" onclick="switchTab(this)">结果</button>
        <button data-tab="schema" onclick="switchTab(this)">Schema</button>
      </div>
      <div class="cpanel active" data-panel="overview"><pre>{html.escape(overview)}</pre></div>
      <div class="cpanel" data-panel="input"><pre>{html.escape(step.input or "（无参数）")}</pre></div>
      <div class="cpanel" data-panel="output"><pre>{html.escape(step.output or "（无输出）")}</pre></div>
      <div class="cpanel" data-panel="schema"><pre>{html.escape(schema_text)}</pre></div>
    </div>"""

    def _timeline(self, record: RunRecord) -> str:
        if not record.spans:
            return '<p class="tip">本轮没有可展示的调用。</p>'

        total = max((float(s.get("end_ms") or 0) for s in record.spans), default=0.0)
        if total <= 0:
            return '<p class="tip">本轮没有可展示的调用。</p>'

        rows: dict[str, list[str]] = {"model": [], "tool": []}
        for index, span in enumerate(record.spans):
            start = float(span.get("start_ms") or 0)
            end = float(span.get("end_ms") or 0)
            left = max(min(start / total * 100, 100.0), 0.0)
            width = max((end - start) / total * 100, 0.45)
            kind = "model" if span.get("kind") == "model" else "tool"
            name = html.escape(str(span.get("name", "")))
            duration = round(end - start, 1)
            title = f"{name} · 第 {span.get('round')} 轮 · {duration} ms"
            handler = f' onclick="openDrawer({index})"' if kind == "tool" else ""
            rows[kind].append(
                f'<div class="tl-bar {kind}" style="left:{left:.3f}%;width:{width:.3f}%" '
                f'title="{title}"{handler}></div>'
            )

        step_ms = 5000 if total <= 20000 else 10000 if total <= 60000 else 15000
        ticks: list[str] = []
        tick = 0
        while tick <= total:
            pos = min(tick / total * 100, 100.0)
            ticks.append(
                f'<span class="tl-tick" style="left:{pos:.3f}%">{int(tick // 1000)}s</span>'
            )
            tick += step_ms

        return f"""<div class="timeline">
      <div class="tl-row"><span class="tl-label">模型</span>
        <div class="tl-track">{"".join(rows["model"])}</div></div>
      <div class="tl-row"><span class="tl-label">工具</span>
        <div class="tl-track">{"".join(rows["tool"])}</div></div>
      <div class="tl-axis"><span></span>
        <div class="tl-axis-track">{"".join(ticks)}</div></div>
    </div>"""

    def _trace(self, record: RunRecord) -> str:
        steps = {step.index: step for step in record.steps}
        parts: list[str] = ['<div class="calls">']
        for index, span in enumerate(record.spans):
            kind = span.get("kind")
            is_tool = kind == "tool"
            label = "工具" if is_tool else "模型"
            badge = "t" if is_tool else "m"
            duration = round(span.get("end_ms", 0) - span.get("start_ms", 0), 1)
            meta = f"第 {span.get('round')} 轮"
            if is_tool:
                meta += f" · 第 {span.get('step')} 步"
            meta += f" · {duration} ms"

            parts.append(f'<div class="call fold-box" id="span-{index}">')
            parts.append(
                f'<button type="button" class="call-h fold-h" aria-expanded="false" '
                f'onclick="toggleFold(this)">'
                f'<span class="badge {badge}">{label}</span>'
                f'<span class="call-n">{html.escape(str(span.get("name")))}</span>'
                f'<span class="call-m">{html.escape(meta)}</span></button>'
            )
            if is_tool:
                step = steps.get(span.get("step"))
                if step is not None:
                    parts.append(self._trace_detail(step, record))
            parts.append("</div>")
        parts.append("</div>")
        return "\n".join(parts)

    def _log(self, record: RunRecord) -> str:
        rows: list[str] = []
        for item in record.events:
            kind = str(item.get("event", ""))
            css, label = _EVENT_KIND.get(kind, ("log-misc", kind))
            fields: list[str] = []
            for key, value in item.items():
                if key in {"event", "t_ms"}:
                    continue
                text = "" if value is None else str(value)
                if len(text) > 120:
                    fields.append(
                        f'<details class="kv"><summary>{html.escape(key)}</summary>'
                        f"<pre>{html.escape(text)}</pre></details>"
                    )
                else:
                    fields.append(
                        f'<span class="kv"><i>{html.escape(key)}</i>{html.escape(text)}</span>'
                    )
            stamp = item.get("t_ms", "")
            stamp_text = f"{stamp} ms" if stamp else ""
            rows.append(
                f'<div class="log-row {css}">'
                f'<span class="log-t">{html.escape(str(stamp_text))}</span>'
                f'<span class="log-badge">{html.escape(label)}</span>'
                f'<div class="log-body">{"".join(fields)}</div>'
                f"</div>"
            )
        return "\n".join(rows)

    def render(self, record: RunRecord) -> str:
        ok = record.summary.get("failed", 0) == 0
        verdict = "通过" if ok else f"失败 {record.summary.get('failed', 0)} 次"
        pill_bg = "var(--app-status-success-bg)" if ok else "var(--app-status-danger-bg)"
        pill_fg = "var(--app-status-success-text)" if ok else "var(--app-status-danger-text)"
        font_src = _brand_font_src(_relpath(_BRAND_FONT, record.html_path.parent))
        css = _CSS.replace("__FONT_SRC__", font_src)
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(record.task[:60])} · Agent 执行报告</title>
<style>{css}</style>
</head>
<body>
<div class="shell">
  {self._sidebar(record)}
  <div class="splitter" id="splitter" role="separator" aria-orientation="vertical"
       aria-label="拖动调整左侧栏宽度，双击恢复默认三成"
       aria-valuemin="220" aria-valuemax="760" tabindex="0"></div>
  <div class="main">
    <div class="main__doodles" aria-hidden="true">
      <svg width="100%" height="100%" viewBox="0 0 900 1200" preserveAspectRatio="none" fill="none">
        <path d="M60 120c40-22 80 18 120-6s70 20 110-8" stroke="#d8d2c4" stroke-width="3" stroke-linecap="round"/>
        <path d="M700 240c30 12 62-14 92 4" stroke="#d8d2c4" stroke-width="3" stroke-linecap="round"/>
        <circle cx="820" cy="120" r="26" stroke="#c9cacc" stroke-width="3"/>
        <path d="M40 620c50 8 90-24 130 4" stroke="#d8d2c4" stroke-width="3" stroke-linecap="round"/>
        <path d="M760 760l18-22 20 20" stroke="#d8d2c4" stroke-width="3" stroke-linecap="round"/>
        <path d="M120 1020c60-18 110 16 160-6" stroke="#d8d2c4" stroke-width="3" stroke-linecap="round"/>
        <circle cx="80" cy="880" r="14" stroke="#c9cacc" stroke-width="3"/>
        <path d="M780 460c20-18 46 16 66-4" stroke="#d8d2c4" stroke-width="3" stroke-linecap="round"/>
      </svg>
    </div>
    <div class="main__body">
      <header class="wb-header">
        <h1 class="wb-title"><span class="brand-accent">AGENT</span> 执行报告</h1>
        <span class="pill" style="background:{pill_bg};color:{pill_fg}">{html.escape(verdict)}</span>
        <div class="tabs">
          <button class="btn active" data-view="report">报告</button>
          <button class="btn" data-view="trace">轨迹</button>
          <button class="btn" data-view="log">事件</button>
        </div>
      </header>
      <div class="doc-body">
        <section class="view active" id="view-report">
          <p class="tip">按子目标分组；点标题逐层展开（子目标 → 角色 → 工具卡），截图可点击放大。</p>
          {self._report(record)}
        </section>
        <section class="view" id="view-trace">
          <p class="tip">上为时间轴（按轮次分层，点条形看详情）；下为调用列表，点行展开该次调用的详情。</p>
          <div class="chart-card">
            <h4>时间轴
              <span class="legend">
                <span><i style="background:var(--c-element)"></i>模型</span>
                <span><i style="background:var(--c-device)"></i>工具</span>
              </span>
            </h4>
            {self._timeline(record)}
          </div>
          {self._trace(record)}
        </section>
        <section class="view" id="view-log">
          <p class="tip">同一轮回放的事件流，按类型着色；长字段可展开。</p>
          <div class="log">{self._log(record)}</div>
        </section>
      </div>
    </div>
  </div>
</div>
<div id="overlay" onclick="this.style.display='none'"><img id="big" alt="放大图"></div>
<div class="drawer" id="drawer">
  <div class="dh">
    <b id="d-name"></b>
    <span id="d-meta"></span>
    <button onclick="closeDrawer()" aria-label="关闭">×</button>
  </div>
  <div class="db" id="d-body"></div>
</div>
<script>{_SCRIPT}</script>
</body>
</html>
"""

    def save(self, record: RunRecord, path: Path | None = None) -> Path:
        target = path or record.html_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.render(record), encoding="utf-8")
        return target
