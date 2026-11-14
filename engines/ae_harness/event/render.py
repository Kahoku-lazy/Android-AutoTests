"""
文件名: ➡️ render.py 🏁
路径: ➡️ engines/ae_harness/event/render.py 🏁
模块功能：➡️ 把一轮运行记录渲染成 Doodle Craft 风格的 HTML 报告 🏁
Python 调试：➡️ python -m engines.ae_harness.event.render 🏁
时间：➡️ 2026-11-13 🏁
作者：➡️ kahoku 🏁
版本：➡️ 3.0.0 🏁
修改时间: ➡️ 2026-11-13 🏁
类型: ➡️ Agent 能力模块 🏁
简介说明：➡️
1. 三个区块：报告（按阶段分组）、轨迹（时间轴 + 调用列表）、原始事件。
2. 视觉走 Doodle Craft：暖白纸面、2.5px 墨线、硬偏移阴影、卡片微倾。
3. 令牌抄自 frontend/src/shared/styles/tokens.css，未声明的 var() 不得出现。
4. step_extras: 按工具名注册额外展示片段；echarts_src: 时间轴脚本地址。
🏁
关联模块：➡️
1. engines.ae_harness.event.record: 消费 RunRecord / StepRecord。
2. .agents/skills/doodle-craft: 令牌与组件配方来源。
🏁
测试：➡️
1. 见 engines.ae_harness.assistant.agent_executor。
🏁
"""

from __future__ import annotations

import base64
import html
import json
import os

from collections.abc import Callable
from pathlib import Path

from .record import RunRecord, StepRecord

__all__ = ["HtmlReportRenderer"]

# 仓库根与平台品牌资源；报告直接内联图标、按相对路径引字体。
_REPO_ROOT = Path(__file__).resolve().parents[3]
_BRAND_MARK = _REPO_ROOT / "frontend" / "public" / "brand" / "ai-mark.png"
_BRAND_FONT = _REPO_ROOT / "frontend" / "public" / "fonts" / "ziku-feiyang.ttf"


def _relpath(target: Path, start: Path) -> str:
    """
    算目标相对起点的路径，统一成正斜杠。

    Args:
        target: 目标文件。
        start: 起点目录。

    Returns:
        可放进 HTML 的相对路径。
    """
    try:
        return os.path.relpath(target, start).replace("\\", "/")
    except ValueError:
        return str(target).replace("\\", "/")


# 事件类型到「样式类 + 中文标签」的映射，用于日志视图着色。
_EVENT_KIND = {
    "reply_start": ("log-start", "开始"),
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

# 卡片微倾角度轮转，按序号取，避免整页都是 0deg。
_TILTS = ("-.6deg", ".8deg", "-1.1deg", "1.2deg", "-.4deg", "1deg")

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

  --app-font:"Cascadia Mono","Noto Sans SC","PingFang SC","Microsoft YaHei",monospace,sans-serif;
  --app-font-mono:"Cascadia Mono","Consolas",monospace;
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
  --app-topbar-h:88px; --side-w:260px;
}
* { box-sizing: border-box; }
body {
  margin: 0; font-family: var(--app-font); font-size: var(--app-size-sm);
  color: var(--ink); background: var(--paper); line-height: 1.6;
}
.shell { display: flex; min-height: 100vh; }
.sidebar {
  width: var(--side-w); flex-shrink: 0; height: 100vh; position: sticky; top: 0;
  background: var(--paper); border-right: 2.5px solid var(--ink);
  padding: 20px 16px; overflow: auto;
}
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
.task .v { font-size: var(--app-size-xs); margin-top: 4px; }
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
.check-card li { font-size: var(--app-size-xs); margin-bottom: 6px; }
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
.token-card .row { display: flex; justify-content: space-between; align-items: baseline; font-size: var(--app-size-xs); padding: 3px 0; }
.token-card .row b { font-family: var(--app-font-mono); font-size: var(--app-size-sm); font-weight: 800; }
.token-card .row.total { border-top: 2px solid var(--ink); margin-top: 4px; padding-top: 6px; }
.token-card .row.total b { font-size: var(--app-size-md); }
.side-list { list-style: none; margin: 0 0 16px; padding: 0; font-size: var(--app-size-xs); }
.side-list li { display: flex; justify-content: space-between; gap: 8px; padding: 4px 0; border-bottom: 1px solid color-mix(in srgb, var(--ink) 12%, transparent); }
.side-list li:last-child { border-bottom: 0; }
.side-list b { font-family: var(--app-font-mono); font-weight: 700; }
.task-box p { margin: 0; font-size: var(--app-size-xs); color: var(--app-text-secondary); word-break: break-word; }

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
.phase { margin-bottom: var(--app-space-lg); }
.phase-h { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
.phase-h h3 { font-size: var(--app-size-md); margin: 0; font-weight: 800; }
.phase-h em { font-style: normal; font-size: var(--app-size-xs); color: var(--app-text-secondary); margin-left: auto; font-family: var(--app-font-mono); }
.role-block {
  border-left: 3px solid var(--role-accent, var(--c-dashboard));
  padding-left: 12px; margin-bottom: 14px;
}
.role-label {
  display: inline-block; font-size: var(--app-size-xs); font-weight: 800;
  letter-spacing: .06em; text-transform: uppercase;
  background: var(--role-accent, var(--c-dashboard));
  border: 2px solid var(--ink); border-radius: var(--app-radius-pill);
  padding: 1px 10px; margin-bottom: 8px;
}

.card {
  position: relative; background: var(--app-bg-card); border: 2.5px solid var(--ink);
  border-radius: 2px; padding: 14px 16px; margin-bottom: 12px;
  box-shadow: 4px 4px 0 0 var(--ac-accent, var(--c-dashboard));
  transform: rotate(var(--tilt, .3deg));
  transition: transform var(--app-duration) var(--app-ease), box-shadow var(--app-duration) var(--app-ease);
}
.card:hover { transform: rotate(0) translate(-1px, -1px); box-shadow: 5px 5px 0 0 var(--ac-accent, var(--c-dashboard)); }
.card-h { display: flex; align-items: center; gap: 10px; cursor: pointer; }
.no {
  width: 26px; height: 26px; flex: 0 0 26px; border: 2.5px solid var(--ink); border-radius: 2px;
  background: var(--app-highlight); font-size: var(--app-size-xs); font-weight: 800;
  display: inline-flex; align-items: center; justify-content: center;
}
.tool { font-family: var(--app-font-mono); font-size: var(--app-size-sm); font-weight: 700; }
.t { font-family: var(--app-font-mono); font-size: var(--app-size-xs); color: var(--app-text-secondary); }
.t.ml { margin-left: auto; }
.note { background: var(--app-bg-subtle); border-left: 4px solid var(--c-element); border-radius: 2px; padding: 8px 10px; margin: 10px 0; font-size: var(--app-size-sm); }
.code {
  background: #fff; border: 2px solid var(--ink); border-radius: var(--app-radius-sm);
  padding: 8px 10px; margin: 6px 0; font-family: var(--app-font-mono);
  font-size: var(--app-size-xs); white-space: pre-wrap; word-break: break-all;
}
.code b { font-family: var(--app-font); font-weight: 800; margin-right: 6px; }
.thumb { display: inline-block; margin-top: 8px; cursor: zoom-in; }
.thumb img { display: block; border: 2px solid var(--ink); border-radius: 2px; box-shadow: 2px 2px 0 0 var(--ink); max-width: 160px; }
table.marks { border-collapse: collapse; font-family: var(--app-font-mono); font-size: var(--app-size-xs); margin: 8px 0; }
table.marks th, table.marks td { border: 2px solid var(--ink); padding: 3px 12px; text-align: center; }
table.marks th { background: var(--app-bg-subtle); font-weight: 800; }
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
.chart-card h4 { margin: 0 0 10px; font-size: var(--app-size-sm); font-weight: 800; display: flex; gap: 8px; align-items: center; }
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
.call-b { padding: 0 14px 12px; display: none; }
.call.open .call-b { display: block; }
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
  font-size: var(--app-size-xs); white-space: pre-wrap; word-break: break-all;
}

.log { background: var(--app-bg-card); border: 2.5px solid var(--ink); border-radius: 2px; padding: 4px 0; box-shadow: 4px 4px 0 0 var(--c-report); }
.log-row { display: grid; grid-template-columns: 92px 78px 1fr; gap: 10px; padding: 7px 14px; border-bottom: 1px solid color-mix(in srgb, var(--ink) 12%, transparent); font-size: var(--app-size-xs); align-items: start; }
.log-row:last-child { border-bottom: 0; }
.log-t { color: var(--app-text-secondary); font-family: var(--app-font-mono); text-align: right; }
.log-badge { display: inline-block; padding: 1px 8px; border: 2px solid var(--ink); border-radius: var(--app-radius-pill); font-size: var(--app-size-xs); font-weight: 700; text-align: center; }
.log-body { display: flex; flex-wrap: wrap; gap: 6px 14px; color: var(--app-text-secondary); word-break: break-all; }
.kv i { font-style: normal; color: var(--app-text-secondary); margin-right: 4px; }
details.kv { width: 100%; }
details.kv summary { cursor: pointer; color: var(--app-text-secondary); }
details.kv pre { margin: 4px 0 0; padding: 8px; background: var(--paper); border: 2px solid var(--ink); border-radius: var(--app-radius-sm); white-space: pre-wrap; word-break: break-all; font-size: var(--app-size-xs); }
.log-model .log-badge { background: var(--c-element); }
.log-tool .log-badge { background: var(--c-device); }
.log-result .log-badge { background: var(--c-workflow); }
.log-think .log-badge { background: var(--c-ai); }
.log-text .log-badge { background: var(--app-bg-subtle); }
.log-start .log-badge, .log-end .log-badge { background: var(--c-dashboard); }
.log-misc .log-badge { background: var(--color-ink-79); }
.raw-box summary { cursor: pointer; color: var(--app-text-secondary); font-size: var(--app-size-xs); margin-bottom: 10px; }
.tip { font-size: var(--app-size-xs); color: var(--app-text-secondary); margin: 0 0 14px; }

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
  .card:hover, .kpi:hover, .btn:hover { transform: none; }
}
@media (max-width: 900px) {
  .shell { flex-direction: column; }
  .sidebar { width: 100%; height: auto; position: static; border-right: 0; border-bottom: 2.5px solid var(--ink); }
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
function toggleTrace(head) {
  const body = head.nextElementSibling;
  if (body) { body.hidden = !body.hidden; }
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
"""


def _thumb_base64(raw: str, long_side: int, quality: int) -> str:
    """
    把 PNG 的 base64 压成 JPEG 缩略图。

    Args:
        raw: 原始 PNG 的 base64 文本。
        long_side: 缩略图长边上限。
        quality: JPEG 质量。

    Returns:
        JPEG 的 base64；缺 Pillow 或解码失败时原样返回。
    """
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
    """
    把 RunRecord 渲染成 Doodle Craft 风格的自包含 HTML。

    工具特有的展示通过 step_extras 注册，本类不认识任何具体工具。
    """

    def __init__(
        self,
        *,
        thumb_long_side: int = 1600,
        thumb_quality: int = 85,
        step_extras: dict[str, Callable[[StepRecord], str]] | None = None,
    ) -> None:
        """
        配置缩略图与步骤扩展。

        Args:
            thumb_long_side: 缩略图长边上限。
            thumb_quality: JPEG 质量。
            step_extras: 工具名到「额外 HTML 片段」的映射；片段已转义。
        """
        self.thumb_long_side = thumb_long_side
        self.thumb_quality = thumb_quality
        self.step_extras = dict(step_extras or {})

    def _brand_mark(self) -> str:
        """
        读平台品牌图并内联成 base64。

        Returns:
            img 标签；缺文件时退回一个占位方块。
        """
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
        """
        渲染左侧导航、统计与 token 消耗。

        Args:
            record: 本轮记录。

        Returns:
            侧边栏 HTML。
        """
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
        """
        渲染报告区：按 SOP 步骤分组，没有步骤时退回阶段分组。

        组内再按执行者 / 验收者分成两个视觉块。

        Args:
            record: 本轮记录。

        Returns:
            报告区 HTML。
        """
        groups: list[tuple[str, list[StepRecord]]] = []
        for step in record.steps:
            key = step.sop_step or step.phase or "未分组"
            if not groups or groups[-1][0] != key:
                groups.append((key, []))
            groups[-1][1].append(step)

        body: list[str] = []
        for name, steps in groups:
            body.append('<div class="phase">')
            body.append(
                f'<div class="phase-h"><h3>{html.escape(name)}</h3>'
                f"<em>{len(steps)} 次调用</em></div>"
            )
            # 组内按角色切块：同一角色的连续步骤合成一块。
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
                        f'<div class="role-block" style="--role-accent:var({accent})">'
                        f'<span class="role-label">{label}</span>'
                    )
                    for step in items:
                        body.append(self._step(step))
                    body.append("</div>")
                else:
                    for step in items:
                        body.append(self._step(step))
            body.append("</div>")
        if record.final_text:
            body.append(f'<div class="final">{html.escape(record.final_text)}</div>')
        return "\n".join(body)

    def _step(self, step: StepRecord) -> str:
        """
        渲染单个步骤卡片，按序号轮转微倾角度。

        Args:
            step: 步骤记录。

        Returns:
            步骤 HTML。
        """
        note = " ".join(step.note.split())
        tilt = _TILTS[(step.index - 1) % len(_TILTS)]
        parts: list[str] = [
            f'<article class="card" style="--tilt:{tilt};--ac-accent:var(--c-{"element" if step.index % 2 else "device"})">'
        ]
        parts.append(
            f'<div class="card-h"><span class="no">{step.index}</span>'
            f'<span class="tool">{html.escape(step.tool)}</span>'
            f'<span class="t ml">{step.span_ms or step.t_ms} ms</span></div>'
        )
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
        parts.append("</article>")
        return "\n".join(parts)

    def _trace_detail(self, step: StepRecord, record: RunRecord) -> str:
        """
        渲染一步的详情面板：概述 / 参数 / 结果 / Schema。

        Args:
            step: 步骤记录。
            record: 本轮记录，用于取 schema。

        Returns:
            详情 HTML。
        """
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
        return f"""<div class="trace-body">
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
        """
        用百分比定位画时间轴：模型与工具各一行，x 轴取事件 t_ms。

        Args:
            record: 本轮记录。

        Returns:
            时间轴 HTML；没有 span 时返回提示。
        """
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
        """
        渲染轨迹列表：每个 span 一行，工具行可展开详情。

        Args:
            record: 本轮记录。

        Returns:
            轨迹列表 HTML。
        """
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

            parts.append(f'<div class="call" id="span-{index}">')
            parts.append(
                f'<div class="call-h" role="button" tabindex="0" aria-expanded="false" '
                f'onclick="toggleTrace(this)" '
                f"onkeydown=\"if(event.key==='Enter'||event.key===' '){{event.preventDefault();this.click();}}\">"
                f'<span class="badge {badge}">{label}</span>'
                f'<span class="call-n">{html.escape(str(span.get("name")))}</span>'
                f'<span class="call-m">{html.escape(meta)}</span></div>'
            )
            if is_tool:
                step = steps.get(span.get("step"))
                if step is not None:
                    parts.append(self._trace_detail(step, record))
            parts.append("</div>")
        parts.append("</div>")
        return "\n".join(parts)

    def _log(self, record: RunRecord) -> str:
        """
        渲染事件日志区。

        Args:
            record: 本轮记录。

        Returns:
            日志区 HTML。
        """
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
        """
        渲染完整页面。

        Args:
            record: 本轮记录。

        Returns:
            完整 HTML 文本。
        """
        ok = record.summary.get("failed", 0) == 0
        verdict = "通过" if ok else f"失败 {record.summary.get('failed', 0)} 次"
        pill_bg = "var(--app-status-success-bg)" if ok else "var(--app-status-danger-bg)"
        pill_fg = "var(--app-status-success-text)" if ok else "var(--app-status-danger-text)"
        font_src = _relpath(_BRAND_FONT, record.html_path.parent)
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
          <p class="tip">按子目标分组；点卡片标题可收起，截图可点击放大。</p>
          {self._report(record)}
        </section>
        <section class="view" id="view-trace">
          <p class="tip">上为时间轴（按轮次分层，点条形看详情）；下为调用列表。</p>
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
        """
        渲染并写入磁盘。

        Args:
            record: 本轮记录。
            path: 目标路径；不传时用记录里的 html_path。

        Returns:
        实际写入的路径。
        """
        target = path or record.html_path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(self.render(record), encoding="utf-8")
        return target
