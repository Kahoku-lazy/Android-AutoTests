from __future__ import annotations

import base64
import hashlib
import html
import json
import re
import urllib.parse

from datetime import datetime
from pathlib import Path
from typing import Any

from .render import (
    _BRAND_FONT,
    _CARET,
    _CSS,
    _EVENT_KIND,
    _ORDINAL_DEFS,
    _SCRIPT,
    _TILTS,
    _brand_font_src,
    _ordinal_svg,
    _relpath,
    _report_heading,
    _thumb_base64,
)
from .render_blocks import clock, facts, json_block, json_value, markdown, pre_text

__all__ = ["AlignedReportRenderer", "load_document", "sections"]

SCHEMA = "agentscope.run/1"
_DEFAULT_SECTIONS = {
    "run": dict,
    "input": dict,
    "replies": list,
    "observations": list,
    "steps": list,
    "summary": dict,
    "events": list,
}
_PHASE_RE = re.compile(r"###\s*目标[：:]\s*([^\n]{1,24})")
_GOAL_LINE = re.compile(r"^[ \t]*###\s*目标[：:][^\n]*(?:\n+|$)", re.MULTILINE)
_STEP_SUFFIX = re.compile(r"\s*·\s*第\s*\d+\s*步\s*$")
_MEDIA_LIMIT = 4 * 1024 * 1024
_THINKING_ACCENT = "--c-element"
_TEXT_ACCENT = "--c-case"
_HINT_ACCENT = "--c-dashboard"
_MISC_ACCENT = "--c-device"
_EXTRA_CSS = """
.role-card { border: 1.5px solid color-mix(in srgb, var(--ink) 22%, transparent);
  border-radius: 14px; padding: 10px 12px 12px; margin: 0 0 14px;
  background: color-mix(in srgb, var(--paper) 55%, #fff);
  box-shadow: 2px 2px 0 0 color-mix(in srgb, var(--ink) 10%, transparent); }
.role-card > .role-h { margin: 0; padding: 4px 6px; border-radius: 10px; }
.role-card > .role-h:hover { background: color-mix(in srgb, var(--ink) 6%, transparent); }
.role-card > .role-b { margin-top: 10px; padding-left: 4px; }
.role-owner { font-family: var(--app-font-mono); font-size: var(--app-size-xs);
  color: var(--app-text-secondary); }
.fold-h[aria-expanded="true"] .caret { transform: rotate(90deg); }
.caret { display: inline-block; transition: transform .15s ease; }

pre { font-family: var(--app-font-mono); font-size: var(--app-size-xs);
  white-space: pre-wrap; word-break: break-word; margin: 4px 0; }
pre.json, pre.text { margin: 0; padding: 8px 10px; background: var(--paper);
  border: 1px solid color-mix(in srgb, var(--ink) 16%, transparent);
  border-radius: var(--app-radius-sm); line-height: 1.6; }
pre.text { font-family: var(--app-font); font-size: var(--app-size-sm); }
.j-key { color: var(--color-blue-27); font-weight: 700; }
.j-str { color: var(--color-green-33); }
.j-num { color: var(--color-red-46); }
.j-lit { color: var(--c-report); font-weight: 700; }
.jfold { margin: 2px 0; }
.jfold > summary { cursor: pointer; font-size: var(--app-size-xs);
  color: var(--app-text-secondary); }
.jfold[open] > summary { margin-bottom: 6px; }

.facts { display: block; }
.fact { display: grid; grid-template-columns: minmax(5.5em, max-content) minmax(0, 1fr);
  gap: 12px; padding: 5px 0; align-items: start;
  border-bottom: 1px solid color-mix(in srgb, var(--ink) 9%, transparent); }
.fact:last-child { border-bottom: 0; }
.fact__k { font-size: var(--app-size-xs); font-weight: 700; color: var(--ink);
  line-height: 2; word-break: break-word; }
.fact__k::after { content: "："; }
.fact__v { min-width: 0; font-size: var(--app-size-sm); line-height: 1.65;
  color: var(--ink); word-break: break-word; }
.fact__v > :first-child { margin-top: 0; }
.fact__v > :last-child { margin-bottom: 0; }
.mono { font-family: var(--app-font-mono); }
.muted { color: var(--app-text-secondary); }

.md { font-size: var(--app-size-sm); line-height: 1.75; word-break: break-word;
  max-width: 900px; }
.md > :first-child { margin-top: 0; }
.md > :last-child { margin-bottom: 0; }
.md p { margin: 0 0 10px; }
.md h1, .md h2, .md h3, .md h4, .md h5, .md h6 {
  margin: 16px 0 8px; font-size: var(--app-size-md); font-weight: 800; line-height: 1.4; }
.md h1, .md h2 { padding-bottom: 4px;
  border-bottom: 1px solid color-mix(in srgb, var(--ink) 12%, transparent); }
.md ul, .md ol { margin: 0 0 10px; padding-left: 22px; }
.md li { margin: 2px 0; }
.md li > p { margin: 0; }
.md code { font-family: var(--app-font-mono); font-size: var(--app-size-xs);
  padding: 0 4px; background: var(--app-bg-subtle);
  border: 1px solid color-mix(in srgb, var(--ink) 12%, transparent);
  border-radius: 2px 4px; }
.md pre { margin: 0 0 10px; padding: 8px 10px; background: var(--paper);
  border: 1px solid color-mix(in srgb, var(--ink) 16%, transparent);
  border-radius: var(--app-radius-sm); overflow-x: auto; }
.md pre code { padding: 0; background: none; border: 0; font-size: var(--app-size-xs); }
.md blockquote { margin: 0 0 10px; padding: 6px 10px;
  border-left: 4px solid var(--c-element); background: var(--app-bg-subtle);
  color: var(--app-text-secondary); }
.md table { display: block; max-width: 100%; overflow-x: auto;
  border-collapse: collapse; margin: 0 0 10px; font-size: var(--app-size-xs); }
.md th, .md td { padding: 4px 8px; text-align: left;
  border: 1px solid color-mix(in srgb, var(--ink) 22%, transparent); }
.md th { background: var(--app-bg-subtle); font-weight: 700; }
.md a { color: var(--color-blue-27); text-decoration: underline; }
.md hr { border: 0; border-top: 1px solid color-mix(in srgb, var(--ink) 14%, transparent);
  margin: 14px 0; }
.md strong { font-weight: 800; }

.overview-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
  gap: var(--app-space-md); align-items: start; }
.overview-card { background: var(--app-bg-card); border: 2.5px solid var(--ink);
  border-radius: var(--app-radius-md); padding: 14px 16px;
  box-shadow: 4px 4px 0 0 var(--ov-accent, var(--c-dashboard));
  transform: rotate(var(--tilt, 0deg));
  transition: transform var(--app-duration) var(--app-ease); }
.overview-card:hover { transform: rotate(0deg) translateY(-1px); }
.overview-card--wide { grid-column: 1 / -1; }
.ov-h { display: flex; align-items: center; gap: 8px; margin: 0 0 10px; }
.ov-h h4 { margin: 0; font-size: var(--app-size-md); font-weight: 800; }
.ov-dot { flex: 0 0 12px; width: 12px; height: 12px; border: 2px solid var(--ink);
  border-radius: 50%; background: var(--ov-accent, var(--c-dashboard)); }
.ov-meta { margin-left: auto; font-family: var(--app-font-mono);
  font-size: var(--app-size-xs); font-weight: 400; color: var(--app-text-secondary); }
.sub-h { display: flex; align-items: baseline; gap: 8px; margin: 14px 0 6px;
  font-size: var(--app-size-xs); font-weight: 800; letter-spacing: .06em;
  color: var(--app-text-secondary); }
.chips { display: flex; flex-wrap: wrap; gap: 6px; }
.chip { display: inline-block; padding: 1px 8px; background: var(--paper);
  border: 1px solid color-mix(in srgb, var(--ink) 22%, transparent);
  border-radius: var(--app-radius-pill); font-family: var(--app-font-mono);
  font-size: var(--app-size-xs); }
.cache-bar { display: flex; height: 10px; margin: 10px 0 4px;
  border: 1px solid color-mix(in srgb, var(--ink) 18%, transparent);
  border-radius: 2px 4px; overflow: hidden; }
.cache-bar span { display: block; height: 100%; }
.cache-bar .hit { background: var(--c-device); }
.cache-bar .miss { background: var(--color-orange-76); }
.table-wrap { overflow-x: auto; }
table.data-table { width: 100%; border-collapse: collapse;
  font-size: var(--app-size-xs); }
table.data-table th { padding: 6px 10px; text-align: left; white-space: nowrap;
  font-size: var(--app-size-xs); font-weight: 800; color: var(--app-text-secondary);
  border-bottom: 2px solid var(--ink); }
table.data-table td { padding: 6px 10px; font-family: var(--app-font-mono);
  border-bottom: 1px solid color-mix(in srgb, var(--ink) 9%, transparent); }
table.data-table tr:last-child td { border-bottom: 0; }
table.data-table tr.total td { font-weight: 800; border-top: 2px solid var(--ink); }

.phase { margin-bottom: var(--app-space-lg); }
.phase-h em { text-align: right; }
.phase-b > .facts:first-child { margin-bottom: 10px; }
.stage { margin-bottom: 12px; padding: 10px 12px; background: #fff;
  border: 2px solid var(--ink); border-radius: var(--app-radius-md);
  box-shadow: 3px 3px 0 0 var(--stage-accent, var(--c-workflow)); }
.stage-h { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.stage-h b { flex: 1 1 auto; min-width: 0; font-size: var(--app-size-md); }
.stage-h em { font-style: normal; font-size: var(--app-size-xs);
  color: var(--app-text-secondary); font-family: var(--app-font-mono); }
.stage-b { padding-top: 8px;
  border-top: 1px solid color-mix(in srgb, var(--ink) 16%, transparent); }
.stage-prep { background: color-mix(in srgb, var(--paper) 65%, #fff); }

.chain { display: flex; flex-direction: column; gap: 8px; margin-top: 12px; }
.chain-item { padding: 8px 10px; background: var(--app-bg-card);
  border: 1.5px solid color-mix(in srgb, var(--ink) 16%, transparent);
  border-left: 4px solid var(--ch-accent, var(--c-element));
  border-radius: var(--app-radius-sm); }
.chain-h { display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  margin-bottom: 2px; }
.chain-n { font-family: var(--app-font-mono); font-size: var(--app-size-xs);
  color: var(--app-text-secondary); }
.chain-phase { padding: 0 6px; font-size: var(--app-size-xs); font-weight: 700;
  border: 1px solid color-mix(in srgb, var(--ink) 30%, transparent);
  border-radius: 2px 4px; }
.chain-t { margin-left: auto; font-family: var(--app-font-mono);
  font-size: var(--app-size-xs); color: var(--app-text-secondary); }
.chain-item.log-model { --ch-accent: var(--c-element); }
.chain-item.log-tool { --ch-accent: var(--c-device); }
.chain-item.log-result { --ch-accent: var(--c-workflow); }
.chain-item.log-think { --ch-accent: var(--c-ai); }
.chain-item.log-start, .chain-item.log-end { --ch-accent: var(--c-dashboard); }
.chain-item.log-misc { --ch-accent: var(--color-ink-79); }

.events { display: flex; flex-direction: column; gap: 8px; }
.event { padding: 8px 10px; background: var(--app-bg-card);
  border: 1px solid color-mix(in srgb, var(--ink) 14%, transparent);
  border-left: 4px solid var(--ev-accent, var(--color-ink-79));
  border-radius: var(--app-radius-sm); }
.event.compact { padding: 4px 10px; }
.event-h { display: flex; align-items: center; gap: 8px; flex-wrap: wrap;
  margin-bottom: 2px; }
.event-t { font-family: var(--app-font-mono); font-size: var(--app-size-xs);
  color: var(--app-text-secondary); }
.event-type { font-family: var(--app-font-mono); font-size: var(--app-size-xs);
  color: var(--app-text-secondary); }
.event.log-model { --ev-accent: var(--c-element); }
.event.log-tool { --ev-accent: var(--c-device); }
.event.log-result { --ev-accent: var(--c-workflow); }
.event.log-think { --ev-accent: var(--c-ai); }
.event.log-start, .event.log-end { --ev-accent: var(--c-dashboard); }
.event.log-misc { --ev-accent: var(--color-ink-79); }

.raw-card { margin-bottom: 12px; padding: 10px 12px; background: var(--app-bg-card);
  border: 2px solid var(--ink); border-radius: var(--app-radius-md);
  box-shadow: 3px 3px 0 0 var(--c-report); }
.raw-card summary { display: flex; align-items: center; gap: 10px; cursor: pointer;
  font-size: var(--app-size-md); font-weight: 800; }
.raw-card summary::-webkit-details-marker { display: none; }
.raw-card details[open] > summary { padding-bottom: 6px; margin-bottom: 8px;
  border-bottom: 1px solid color-mix(in srgb, var(--ink) 14%, transparent); }
.msg { padding: 6px 0;
  border-bottom: 1px solid color-mix(in srgb, var(--ink) 9%, transparent); }
.msg-h { display: flex; align-items: center; gap: 8px; margin-bottom: 4px;
  font-size: var(--app-size-xs); }
@media (prefers-reduced-motion: reduce) {
  .overview-card, .overview-card:hover, .caret { transform: none; transition: none; }
}
@media (max-width: 720px) {
  .wb-header { flex-wrap: wrap; }
  .tabs { width: 100%; margin-left: 0; overflow-x: auto; }
}
"""
_CHAIN_LABEL = {
    "reply": ("log-start", "回复"),
    "reasoning": ("log-model", "推理"),
    "model_call": ("log-model", "请求"),
    "model_call_return": ("log-model", "返回"),
    "compress_context": ("log-end", "压缩"),
    "system_prompt": ("log-text", "提示词"),
    "acting": ("log-tool", "执行"),
    "permission": ("log-result", "权限"),
}

_FIELD_LABEL = {
    "round": "轮次",
    "phase": "阶段",
    "cost_ms": "耗时 ms",
    "context_len": "上下文条数",
    "tool": "工具",
    "state": "状态",
    "model": "模型",
    "model_name": "模型",
    "message_count": "消息条数",
    "messages_chars": "序列化字符",
    "tool_choice": "工具选择",
    "tool_names": "可用工具",
    "chunks": "分片数",
    "input": "入参",
    "output": "输出",
    "text": "文本",
    "thinking": "思考",
    "length": "字数",
    "messages_before": "压缩前条数",
    "messages_after": "压缩后条数",
    "compressed": "是否压缩",
    "trigger_ratio": "触发比例",
    "threshold": "阈值",
    "instructions": "压缩指令",
    "decision": "判定",
    "permission_mode": "权限模式",
    "summary_chars": "压缩摘要字数",
    "tasks": "计划任务",
    "framework_images": "框架图片数",
    "images_sent": "实际发送图片",
    "images_dropped": "丢弃图片",
    "wire": "实际发送 payload",
    "messages": "实际发送的消息",
    "session_id": "会话",
    "input_tokens": "输入 token",
    "output_tokens": "输出 token",
    "cache_input_tokens": "缓存命中 token",
    "cache_creation_input_tokens": "缓存写入 token",
    "reply_id": "reply_id",
    "tool_call_id": "tool_call_id",
    "block_id": "block_id",
    "url": "地址",
    "media_type": "媒体类型",
    "name": "名称",
}


def load_document(path: Path) -> dict:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("对齐记录必须是 JSON 对象")
    return raw


def sections(document: dict) -> dict:
    result: dict = {}
    for key, kind in _DEFAULT_SECTIONS.items():
        value = document.get(key)
        result[key] = value if isinstance(value, kind) else kind()
    return result


def _role_label(agent: str) -> str:
    text = (agent or "").lower()
    return "验收者" if "verif" in text else "执行者"


_ROLE_TEXT = {"executor": "执行者", "verifier": "验收者"}


def _role_text(role: object, agent: str = "") -> str:
    known = _ROLE_TEXT.get(str(role or ""))
    return known if known else _role_label(agent)


def _event_name(kind: str) -> str:
    parts = [part for part in str(kind or "").split("_") if part]
    return "".join(part.title() for part in parts) + "Event" if parts else ""


def _stamp(value: Any) -> datetime | None:
    text = str(value or "")
    for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(text[:26], fmt)
        except ValueError:  # silent-except
            continue
    return None


def _text_of(block: dict) -> str:
    return str(block.get("text") or "")


def _thinking_of(block: dict) -> str:
    return str(block.get("thinking") or "")


def _phase_of(text: str) -> tuple[str, str]:
    match = _PHASE_RE.search(text)
    if not match:
        return "", text
    remainder = _PHASE_RE.sub("", text, count=1).strip()
    return match.group(1).strip(), remainder


def _action_of(step: dict) -> str:
    for line in str(step.get("description") or "").splitlines():
        text = line.strip()
        if text.startswith("动作："):
            return text[len("动作：") :].strip()
    return ""


def _step_goal(step: dict) -> str:
    subject = str(step.get("subject") or "").strip()
    if subject and not _STEP_SUFFIX.search(subject):
        return subject
    action = _action_of(step)
    if action:
        return action
    return _STEP_SUFFIX.sub("", subject).strip()


def _stage_step_title(step: dict, position: int) -> str:
    goal = _step_goal(step)
    return f"第 {position} 步 · {goal}" if goal else f"第 {position} 步"


def _block_items(block: dict) -> list[dict]:
    output = block.get("output")
    if isinstance(output, list):
        return [item for item in output if isinstance(item, dict)]
    if isinstance(output, str):
        return [{"type": "text", "text": output}]
    return []


def _hint_text(block: dict) -> str:
    hint = block.get("hint")
    if isinstance(hint, str):
        return hint
    if isinstance(hint, list):
        return "".join(str(item.get("text") or "") for item in hint if isinstance(item, dict))
    return str(hint or "")


class AlignedReportRenderer:
    def __init__(
        self,
        *,
        media_limit: int = _MEDIA_LIMIT,
        thumb_long_side: int = 1600,
        thumb_quality: int = 85,
    ) -> None:
        self.media_limit = int(media_limit)
        self.thumb_long_side = int(thumb_long_side)
        self.thumb_quality = int(thumb_quality)
        self._base: Path | None = None

    def render(self, document: dict) -> str:
        self._seen_media: set[str] = set()
        parts = sections(document)
        run = parts["run"]
        summary = parts["summary"]
        replies = [item for item in parts["replies"] if isinstance(item.get("msg"), dict)]
        caption = str(parts["input"].get("user_message") or run.get("thread_id") or "")
        if not replies:
            body = '<p class="tip">无内容：这份记录里没有可渲染的回复。</p>'
        else:
            body = self._report(replies, self._step_names(document))
        return self._page(
            document=document,
            caption=caption,
            body=body,
            summary=summary,
            replies=replies,
        )

    def save(self, document: dict, path: Path) -> Path:
        target = Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        self._base = target.parent
        target.write_text(self.render(document), encoding="utf-8")
        return target

    def _heading(self, document: dict) -> str:
        title = str(sections(document)["run"].get("report_title") or "").strip()
        return _report_heading(title)

    def _page(
        self,
        *,
        document: dict,
        caption: str,
        body: str,
        summary: dict,
        replies: list,
    ) -> str:
        steps = sections(document)["steps"]
        if steps:
            stage_tip = (
                "按 SOP 步骤分阶段：准备（两个角色的提示词）→ 每步（执行者 / 验收者各自成块）→ 收尾。"
                "点阶段标题展开该步细节。"
            )
        else:
            stage_tip = (
                "按轮次分阶段：准备 → 每一轮（推理 / 请求 / 返回 / 压缩 / 权限 / 执行）→ 收尾。"
                "点阶段标题展开该轮细节。"
            )
        ok = not any(
            block.get("state") not in {"success", None}
            for reply in replies
            for block in (reply.get("msg") or {}).get("content") or []
            if block.get("type") == "tool_result"
        )
        verdict = "通过" if ok else "有失败工具"
        pill_bg = "var(--app-status-success-bg)" if ok else "var(--app-status-danger-bg)"
        pill_fg = "var(--app-status-success-text)" if ok else "var(--app-status-danger-text)"
        font_src = _brand_font_src(_relpath(_BRAND_FONT, self._base or Path(".")))
        css = _CSS.replace("__FONT_SRC__", font_src) + _EXTRA_CSS
        return f"""<!doctype html>
<html lang="zh-CN">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{html.escape(caption[:60])} · Agent 执行报告</title>
<style>{css}</style>
</head>
<body>
<div class="shell">
  {self._sidebar(document, caption, summary, replies)}
  <div class="splitter" id="splitter" role="separator" aria-orientation="vertical"
       aria-label="拖动调整左侧栏宽度，双击恢复默认三成"
       aria-valuemin="220" aria-valuemax="760" tabindex="0"></div>
  <div class="main">
    <div class="main__body">
      <header class="wb-header">
        {self._heading(document)}
        <span class="pill" style="background:{pill_bg};color:{pill_fg}">{html.escape(verdict)}</span>
        <div class="tabs">
          <button class="btn active" data-view="report">报告</button>
          <button class="btn" data-view="overview">概览</button>
          <button class="btn" data-view="stage">阶段</button>
          <button class="btn" data-view="log">事件流</button>
          <button class="btn" data-view="raw">原始记录</button>
        </div>
      </header>
      <div class="doc-body">
        {_ORDINAL_DEFS}
        <section class="view active" id="view-report">
          <p class="tip">按子目标分组；点标题逐层展开（子目标 → 角色 → 内容块），内容顺序与模型产出顺序一致。</p>
          {body}
        </section>
        <section class="view" id="view-overview">
          <p class="tip">这次运行的环境、输入条件、用量与产物。字段一行一条，JSON 折叠后展开看结构。</p>
          {self._overview(document)}
        </section>
        <section class="view" id="view-stage">
          <p class="tip">{stage_tip}</p>
          {self._stage(document)}
        </section>
        <section class="view" id="view-log">
          <p class="tip">事件逐条列出：时刻、类型与字段；增量事件默认折叠，末尾可一次展开。</p>
          <div class="events">{self._events(document)}</div>
        </section>
        <section class="view" id="view-raw">
          <p class="tip">记录原文：run / input / steps / observations / summary 各段与产物路径，可直接复制。</p>
          {self._raw(document)}
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

    def _sidebar(self, document: dict, caption: str, summary: dict, replies: list) -> str:
        tokens = summary.get("tokens") if isinstance(summary.get("tokens"), dict) else None
        known = tokens is not None
        values = tokens or {}
        tool_calls, failed, images = self._counts(replies)
        total_tokens = int(values.get("input", 0)) + int(values.get("output", 0))
        by_tool = self._by_tool(replies)
        tool_list = "".join(
            f"<li><span>{html.escape(name)}</span><b>{count}</b></li>"
            for name, count in sorted(by_tool.items())
        )
        cost = summary.get("cost_s")
        cost_text = f"{float(cost):.2f}s" if isinstance(cost, (int, float)) else "未知"

        def _row(label: str, key: str, total: bool = False) -> str:
            value = f"{int(values.get(key, 0)):,}" if known else "未知"
            css = "row total" if total else "row"
            return f'<div class="{css}"><span>{label}</span><b>{value}</b></div>'

        total_row = _row("总计", "", True)
        if known:
            total_row = f'<div class="row total"><span>总计</span><b>{total_tokens:,}</b></div>'

        return f"""<aside class="sidebar">
    <div class="brand">
      {self._brand_mark()}
      <span class="brand-title"><span class="brand-accent">AGENT</span>可视化报告</span>
    </div>
    <div class="task"><div class="k">任务</div><div class="v">{html.escape(caption)}</div></div>
    <div class="stats">
      <div class="kpi" style="--tilt:-.8deg;--kpi:var(--c-dashboard)"><em>耗时</em><strong>{cost_text}</strong></div>
      <div class="kpi" style="--tilt:.9deg;--kpi:var(--c-element)"><em>回复</em><strong>{len(replies)}</strong></div>
      <div class="kpi" style="--tilt:1.1deg;--kpi:var(--c-device)"><em>工具</em><strong>{tool_calls}</strong></div>
      <div class="kpi" style="--tilt:-1.2deg;--kpi:var(--c-case)"><em>失败</em><strong class="bad">{failed}</strong></div>
    </div>
    <div class="token-card">
      <div class="k">Token 消耗</div>
      {_row("输入", "input")}
      {_row("输出", "output")}
      {_row("缓存命中", "cache_hit")}
      {total_row}
      <div class="row"><span>截图</span><b>{images}</b></div>
    </div>
    <div class="label">工具分布</div>
    <ul class="side-list">{tool_list or "<li><span>无</span><b>0</b></li>"}</ul>
  </aside>"""

    def _brand_mark(self) -> str:
        return (
            '<svg class="brand-mark" width="32" height="32" viewBox="0 0 32 32" '
            'fill="none" aria-hidden="true"><rect x="2" y="2" width="28" height="28" '
            'rx="8" fill="#fff" stroke="#16aea1" stroke-width="2.5"/>'
            '<text x="16" y="22" text-anchor="middle" font-size="12" '
            'font-weight="800" fill="#16aea1">AI</text></svg>'
        )

    def _counts(self, replies: list) -> tuple[int, int, int]:
        tools = failed = images = 0
        for reply in replies:
            for block in (reply.get("msg") or {}).get("content") or []:
                kind = block.get("type")
                if kind == "tool_call":
                    tools += 1
                elif kind == "tool_result":
                    if str(block.get("state")) not in {"success", "ToolResultState.SUCCESS"}:
                        failed += 1
                    images += sum(1 for item in _block_items(block) if item.get("type") == "data")
        return tools, failed, images

    def _by_tool(self, replies: list) -> dict[str, int]:
        counts: dict[str, int] = {}
        for reply in replies:
            for block in (reply.get("msg") or {}).get("content") or []:
                if block.get("type") == "tool_call":
                    name = str(block.get("name") or "")
                    counts[name] = counts.get(name, 0) + 1
        return counts

    def _step_names(self, document: dict) -> dict[str, tuple[str, str]]:
        rows: dict[str, tuple[str, str]] = {}
        for position, step in enumerate(sections(document)["steps"], start=1):
            label = _step_goal(step) or f"第 {position} 步"
            key = f"step:{position}"
            for reply_id in step.get("reply_ids") or []:
                rows[str(reply_id)] = (key, label)
        return rows

    def _report(self, replies: list, step_of: dict[str, tuple[str, str]] | None = None) -> str:
        step_of = step_of or {}
        results: dict[str, dict] = {}
        items: list[tuple[str, str, str, dict]] = []
        key, label = "", ""
        for reply in replies:
            agent = str(reply.get("agent") or "")
            reply_id = str(reply.get("reply_id") or "")
            for block in (reply.get("msg") or {}).get("content") or []:
                if block.get("type") == "tool_result":
                    results[str(block.get("id"))] = block
                    continue
                if reply_id in step_of:
                    key, label = step_of[reply_id]
                    if block.get("type") == "text":
                        remainder = _GOAL_LINE.sub("", _text_of(block), count=1).strip()
                        if not remainder:
                            continue
                        block = {**block, "text": remainder}
                    items.append((key, label, agent, block))
                    continue
                if block.get("type") == "text":
                    phase, remainder = _phase_of(_text_of(block))
                    if phase:
                        key = label = phase
                    block = {**block, "text": remainder} if phase else block
                items.append((key or "未分阶段", label or "未分阶段", agent, block))

        groups: list[tuple[str, str, list[tuple[str, list[dict]]]]] = []
        for group_key, group_label, agent, block in items:
            if not groups or groups[-1][0] != group_key:
                groups.append((group_key, group_label, []))
            roles = groups[-1][2]
            if not roles or roles[-1][0] != agent:
                roles.append((agent, []))
            roles[-1][1].append(block)

        body: list[str] = []
        role_of = {str(reply.get("agent") or ""): str(reply.get("role") or "") for reply in replies}
        for ordinal, (_key, name, roles) in enumerate(groups, start=1):
            calls = sum(
                1 for _, blocks in roles for block in blocks if block.get("type") == "tool_call"
            )
            body.append('<div class="phase fold-box">')
            body.append(
                '<div class="phase-h"><h3>'
                '<button type="button" class="fold-h" aria-expanded="false" '
                'onclick="toggleFold(this)">'
                f"{_CARET}{_ordinal_svg(ordinal)}{html.escape(name)}</button></h3>"
                f"<em>{len(roles)} 角色 · {calls} 次调用</em></div>"
            )
            body.append('<div class="phase-b fold-b">')
            for agent, blocks in roles:
                label = _role_text(role_of.get(agent), agent)
                accent = "--c-case" if label == "执行者" else "--c-device"
                body.append(
                    f'<div class="role-block role-card fold-box" style="--role-accent:var({accent})">'
                    '<button type="button" class="role-h fold-h" aria-expanded="false" '
                    'onclick="toggleFold(this)">'
                    f'{_CARET}<span class="role-label">{html.escape(label)}</span>'
                    f'<span class="role-owner">{html.escape(agent)}</span></button>'
                    '<div class="role-b fold-b">'
                )
                body.append(self._blocks(blocks, results))
                body.append("</div></div>")
            body.append("</div></div>")
        return "\n".join(body)

    def _blocks(self, blocks: list[dict], results: dict[str, dict]) -> str:
        parts: list[str] = []
        for index, block in enumerate(blocks, start=1):
            kind = block.get("type")
            if kind == "tool_call":
                result = results.get(str(block.get("id")))
                parts.append(self._tool_card(index, block, result))
            elif kind == "thinking":
                parts.append(self._text_card(index, "思考", _thinking_of(block), _THINKING_ACCENT))
            elif kind == "text":
                parts.append(self._text_card(index, "文本", _text_of(block), _TEXT_ACCENT))
            elif kind == "hint":
                parts.append(self._text_card(index, "运行时提示", _hint_text(block), _HINT_ACCENT))
            else:
                parts.append(self._misc_card(index, block))
        return "\n".join(parts)

    def _card(self, index: int, title: str, meta: str, accent: str, body: str) -> str:
        tilt = _TILTS[(index - 1) % len(_TILTS)]
        return (
            f'<article class="card fold-box" style="--tilt:{tilt};--ac-accent:var({accent})">'
            '<button type="button" class="card-h fold-h" aria-expanded="false" '
            'onclick="toggleFold(this)">'
            f'{_CARET}<span class="no">{index}</span>'
            f'<span class="tool">{html.escape(title)}</span>'
            f'<span class="t ml">{html.escape(meta)}</span></button>'
            f'<div class="card-b fold-b">{body}</div></article>'
        )

    def _text_card(self, index: int, title: str, text: str, accent: str) -> str:
        body = markdown(text)
        return self._card(index, title, f"{len(text)} 字", accent, body)

    def _misc_card(self, index: int, block: dict) -> str:
        return self._card(
            index,
            str(block.get("type") or "未知块"),
            "未识别的块类型",
            _MISC_ACCENT,
            f'<div class="sub-h">原文</div>{json_block(block)}',
        )

    def _tool_card(self, index: int, call: dict, result: dict | None) -> str:
        state = str((result or {}).get("state") or "结果缺失")
        parts = [f'<div class="sub-h">入参</div>{json_block(call.get("input") or "{}")}']
        if result is None:
            parts.append('<div class="sub-h">结果</div><p class="tip">结果缺失</p>')
        else:
            for item in _block_items(result):
                if item.get("type") == "text":
                    parts.append(f'<div class="sub-h">结果</div>{json_value(_text_of(item))}')
                elif item.get("type") == "data":
                    parts.append(self._image(item))
        return self._card(
            index, str(call.get("name") or "tool"), f"{state}", _MISC_ACCENT, "".join(parts)
        )

    def _image(self, item: dict) -> str:
        source = item.get("source") or {}
        url = str(source.get("url") or "")
        media_type = str(source.get("media_type") or "image/png")
        data = self._read_media(url)
        if data is None:
            return f'<div class="code"><b>截图</b>{html.escape(url or "（无地址）")}</div>'
        digest = hashlib.sha256(data).hexdigest()
        repeat = digest in self._seen_media
        self._seen_media.add(digest)
        note = (
            '<div class="code"><b>提示</b>与前面某张截图完全相同（画面未变）</div>'
            if repeat
            else ""
        )
        raw = base64.b64encode(data).decode("ascii")
        thumb = _thumb_base64(raw, self.thumb_long_side, self.thumb_quality)
        mime = "image/jpeg" if thumb != raw else media_type
        return (
            note + f'<span class="thumb" role="button" tabindex="0" aria-label="放大截图" '
            f"onclick=\"zoomShot(this.querySelector('img').src)\" "
            f"onkeydown=\"if(event.key==='Enter'||event.key===' '){{event.preventDefault();this.click();}}\">"
            f'<img src="data:{mime};base64,{thumb}" alt="截图"></span>'
        )

    def _read_media(self, url: str) -> bytes | None:
        if not url.startswith("file://"):
            return None
        path = Path(urllib.parse.urlparse(url).path.lstrip("/"))
        if not path.exists() or path.stat().st_size > self.media_limit:
            return None
        return path.read_bytes()

    def _spans(self, document: dict) -> list[dict]:
        spans: list[dict] = []
        opened: dict[str, dict] = {}
        rounds = 0
        for event in sections(document)["events"]:
            kind = str(event.get("type") or "")
            when = _stamp(event.get("created_at"))
            reply_id = str(event.get("reply_id") or "")
            if kind == "MODEL_CALL_START":
                rounds += 1
                opened[f"model:{reply_id}"] = {"start": when, "round": rounds}
            elif kind == "MODEL_CALL_END" and f"model:{reply_id}" in opened:
                start = opened.pop(f"model:{reply_id}")
                spans.append(
                    {
                        "kind": "model",
                        "name": str(event.get("model_name") or "model"),
                        "round": start["round"],
                        "start": start["start"],
                        "end": when,
                    }
                )
            elif kind == "TOOL_RESULT_START":
                opened[f"tool:{event.get('tool_call_id')}"] = {
                    "start": when,
                    "round": rounds,
                    "name": str(event.get("tool_call_name") or "tool"),
                }
            elif kind == "TOOL_RESULT_END":
                key = f"tool:{event.get('tool_call_id')}"
                if key in opened:
                    start = opened.pop(key)
                    spans.append(
                        {
                            "kind": "tool",
                            "name": start["name"],
                            "round": start["round"],
                            "start": start["start"],
                            "end": when,
                            "state": str(event.get("state") or ""),
                        }
                    )
        return spans

    def _timeline(self, document: dict) -> str:
        spans = self._spans(document)
        if not spans:
            return '<p class="tip">本轮没有可展示的调用。</p>'
        starts = [span["start"] for span in spans if span["start"]]
        if not starts:
            return '<p class="tip">本轮没有可展示的调用。</p>'
        origin = min(starts)
        rows: dict[str, list[str]] = {"model": [], "tool": []}
        offset = 0.0
        for index, span in enumerate(spans):
            begin = (span["start"] - origin).total_seconds() * 1000 if span["start"] else 0.0
            end = (span["end"] - origin).total_seconds() * 1000 if span["end"] else begin
            offset = max(offset, end)
            kind = "model" if span["kind"] == "model" else "tool"
            rows[kind].append((begin, end, span, index))
        total = max(offset, 1.0)
        bars: dict[str, list[str]] = {"model": [], "tool": []}
        for kind, items in rows.items():
            for begin, end, span, index in items:
                left = max(min(begin / total * 100, 100.0), 0.0)
                width = max((end - begin) / total * 100, 0.45)
                title = f"{span['name']} · 第 {span['round']} 轮 · {round(end - begin, 1)} ms"
                bars[kind].append(
                    f'<div class="tl-bar {kind}" style="left:{left:.3f}%;width:{width:.3f}%" '
                    f'title="{html.escape(title)}"></div>'
                )
        ticks: list[str] = []
        step = 5000 if total <= 20000 else 10000 if total <= 60000 else 15000
        tick = 0.0
        while tick <= total:
            ticks.append(
                f'<span class="tl-tick" style="left:{min(tick / total * 100, 100.0):.3f}%">'
                f"{int(tick // 1000)}s</span>"
            )
            tick += step
        return f"""<div class="timeline">
      <div class="tl-row"><span class="tl-label">模型</span>
        <div class="tl-track">{"".join(bars["model"])}</div></div>
      <div class="tl-row"><span class="tl-label">工具</span>
        <div class="tl-track">{"".join(bars["tool"])}</div></div>
      <div class="tl-axis"><span></span>
        <div class="tl-axis-track">{"".join(ticks)}</div></div>
    </div>"""

    def _trace(self, document: dict) -> str:
        spans = self._spans(document)
        if not spans:
            return '<p class="tip">本轮没有可展示的调用。</p>'
        parts = ['<div class="calls">']
        for index, span in enumerate(spans):
            is_tool = span["kind"] == "tool"
            duration = round(
                (span["end"] - span["start"]).total_seconds() * 1000
                if span["start"] and span["end"]
                else 0.0,
                1,
            )
            meta = f"第 {span['round']} 轮 · {duration} ms"
            parts.append(
                f'<div class="call fold-box"><button type="button" class="call-h fold-h" '
                f'aria-expanded="false" onclick="toggleFold(this)">'
                f'<span class="badge {"t" if is_tool else "m"}">{"工具" if is_tool else "模型"}</span>'
                f'<span class="call-n">{html.escape(span["name"])}</span>'
                f'<span class="call-m">{html.escape(meta)}</span></button></div>'
            )
        parts.append("</div>")
        return "\n".join(parts)

    def _chain_row(self, index: int, observation: dict) -> str:
        kind = str(observation.get("kind") or "")
        css, label = _CHAIN_LABEL.get(kind, ("log-misc", kind))
        phase = str(observation.get("phase") or "")
        phase_text = {"start": "开始", "end": "结束"}.get(phase, phase)
        chip = f'<span class="chain-phase">{html.escape(phase_text)}</span>' if phase_text else ""
        rows = [
            (_FIELD_LABEL.get(str(key), str(key)), value)
            for key, value in observation.items()
            if key not in {"kind", "at", "phase", "reply_id"} and value not in (None, "", [], {})
        ]
        stamp = clock(observation.get("at"))
        return (
            f'<div class="chain-item {css}">'
            f'<div class="chain-h"><span class="log-badge">{html.escape(label)}</span>'
            f'<span class="chain-n">#{index} · {html.escape(_event_name(kind) or kind)}</span>'
            f'{chip}<span class="chain-t">{html.escape(stamp)}</span></div>'
            f"{facts(rows)}</div>"
        )

    def _phase(
        self,
        *,
        ordinal: int | None,
        title: str,
        meta: str,
        body: str,
        note: str = "",
        accent: str = "--c-dashboard",
    ) -> str:
        mark = _ordinal_svg(ordinal, "阶段") if ordinal else ""
        return (
            f'<section class="phase fold-box" style="--phase-accent:var({accent})">'
            '<div class="phase-h"><h3><button type="button" class="fold-h" '
            'aria-expanded="false" onclick="toggleFold(this)">'
            f"{_CARET}{mark}<b>{html.escape(title)}</b></button></h3>"
            f"{note}<em>{html.escape(meta)}</em></div>"
            f'<div class="phase-b fold-b">{body}</div></section>'
        )

    def _stage_card(self, title: str, meta: str, body: str) -> str:
        return (
            '<div class="stage fold-box" style="--stage-accent:var(--c-workflow)">'
            '<div class="stage-h"><button type="button" class="fold-h" aria-expanded="false" '
            'onclick="toggleFold(this)">'
            f"{_CARET}<b>{html.escape(title)}</b><em>{html.escape(meta)}</em>"
            f'</button></div><div class="stage-b fold-b">{body}</div></div>'
        )

    def _role_card(self, label: str, owner: str, body: str, accent: str) -> str:
        return (
            '<div class="role-block role-card fold-box" '
            f'style="--role-accent:var({accent})">'
            '<button type="button" class="role-h fold-h" aria-expanded="false" '
            'onclick="toggleFold(this)">'
            f'{_CARET}<span class="role-label">{html.escape(label)}</span>'
            f'<span class="role-owner">{html.escape(owner)}</span></button>'
            f'<div class="role-b fold-b">{body}</div></div>'
        )

    def _prompt_details(self, prompt: str) -> str:
        return (
            f'<details class="jfold"><summary>system prompt 全文（{len(prompt)} 字）</summary>'
            f"{pre_text(prompt)}</details>"
        )

    def _tool_chips(self, tools: list[dict]) -> str:
        names = [
            str(tool.get("name") or "")
            for tool in tools
            if isinstance(tool, dict) and tool.get("name")
        ]
        if not names:
            return '<span class="muted">—</span>'
        return (
            '<div class="chips">'
            + "".join(f'<span class="chip">{html.escape(name)}</span>' for name in names)
            + "</div>"
        )

    def _tool_details(self, tools: list[dict]) -> str:
        return "".join(
            f'<details class="jfold"><summary>{html.escape(str(tool.get("name") or ""))}</summary>'
            f"{json_block(tool.get('parameters') or {})}</details>"
            for tool in tools
            if isinstance(tool, dict)
        )

    def _stage(self, document: dict) -> str:
        parts = sections(document)
        if parts["steps"]:
            return self._stage_steps(document, parts["steps"], parts["observations"])
        observations = parts["observations"]
        if not observations:
            return '<p class="tip">这份记录里没有观测数据。</p>'
        groups: dict[str, list] = {}
        for observation in observations:
            key = str(observation.get("reply_id") or "")
            groups.setdefault(key, []).append(observation)

        model_ends = [
            event for event in parts["events"] if str(event.get("type")) == "MODEL_CALL_END"
        ]
        blocks: list[str] = [self._stage_prepare(document, 1)]
        round_index = 0
        ordinal = 2
        for reply_id, items in groups.items():
            for item in self._reply_rounds(items):
                usage = model_ends[round_index] if round_index < len(model_ends) else {}
                round_index += 1
                blocks.append(self._stage_round(item, reply_id, usage, ordinal=ordinal))
                ordinal += 1
        blocks.append(self._stage_tail(document, ordinal))
        return "\n".join(blocks)

    def _reply_rounds(self, items: list[dict]) -> list[dict]:
        rounds: list[dict] = []
        for observation in items:
            if observation.get("kind") == "reasoning" and observation.get("phase") == "start":
                rounds.append({"round": observation.get("round"), "items": [observation]})
            elif rounds:
                rounds[-1]["items"].append(observation)
        if not rounds:
            rounds = [{"round": 0, "items": items}]
        return rounds

    def _reply_meta(self, document: dict) -> dict[str, dict]:
        parts = sections(document)
        models = {
            str(item.get("name") or ""): str(item.get("model") or "")
            for item in parts["run"].get("roles") or []
            if isinstance(item, dict)
        }
        rows: dict[str, dict] = {}
        for reply in parts["replies"]:
            reply_id = str(reply.get("reply_id") or "")
            agent = str(reply.get("agent") or "")
            rows[reply_id] = {
                "agent": agent,
                "role": str(reply.get("role") or ""),
                "model": models.get(agent, ""),
            }
        return rows

    def _stage_steps(self, document: dict, steps: list[dict], observations: list[dict]) -> str:
        parts = sections(document)
        groups: dict[str, list] = {}
        for observation in observations:
            groups.setdefault(str(observation.get("reply_id") or ""), []).append(observation)
        model_ends = [
            event for event in parts["events"] if str(event.get("type")) == "MODEL_CALL_END"
        ]
        meta = self._reply_meta(document)
        usage_index = 0
        blocks: list[str] = [self._stage_prepare(document, 1)]
        ordinal = 2
        for position, step in enumerate(steps, start=1):
            rows: list[str] = []
            calls = 0
            for reply_id in step.get("reply_ids") or []:
                items = groups.get(reply_id) or []
                info = meta.get(reply_id, {})
                label = _role_text(info.get("role"), info.get("agent", ""))
                accent = "--c-case" if label == "执行者" else "--c-device"
                owner = " · ".join(
                    text for text in (info.get("agent", ""), info.get("model", "")) if text
                )
                inner: list[str] = []
                for item in self._reply_rounds(items):
                    usage = model_ends[usage_index] if usage_index < len(model_ends) else {}
                    usage_index += 1
                    calls += sum(1 for o in item["items"] if o.get("kind") == "acting")
                    inner.append(self._stage_round(item, reply_id, usage))
                if not inner:
                    inner.append('<p class="tip">这一步没有可展示的回复。</p>')
                rows.append(self._role_card(label, owner, "".join(inner), accent))
            if not rows:
                rows.append('<p class="tip">这一步没有可展示的回复。</p>')
            passed = bool(step.get("passed"))
            pill = (
                '<span class="pill" style="background:var(--app-status-success-bg);'
                'color:var(--app-status-success-text)">通过</span>'
                if passed
                else '<span class="pill" style="background:var(--app-status-danger-bg);'
                'color:var(--app-status-danger-text)">未通过</span>'
            )
            note_rows = [
                (label, step.get(key))
                for key, label in (("expected", "预期"), ("message", "说明"))
                if step.get(key)
            ]
            body = facts(note_rows) + "".join(rows)
            blocks.append(
                self._phase(
                    ordinal=ordinal,
                    title=_stage_step_title(step, position),
                    meta=f"尝试 {int(step.get('attempts') or 0)} 次 · 工具 {calls} 次",
                    body=body,
                    note=pill,
                    accent="--c-device",
                )
            )
            ordinal += 1
        blocks.append(self._stage_tail(document, ordinal))
        return "\n".join(blocks)

    def _stage_prepare(self, document: dict, ordinal: int = 1) -> str:
        parts = sections(document)
        inputs = parts["input"]
        run = parts["run"]
        roles = [item for item in inputs.get("roles") or [] if isinstance(item, dict)]
        run_rows = [
            (str(key), value)
            for key, value in run.items()
            if value not in (None, "") and key != "roles"
        ]
        message = str(inputs.get("user_message") or "")
        if roles:
            cards: list[str] = []
            chars = 0
            tool_total = 0
            for item in roles:
                prompt = str(item.get("system_prompt") or "")
                tools = item.get("tool_schemas") or []
                chars += len(prompt)
                tool_total += len(tools)
                label = _role_text(item.get("role"), str(item.get("name") or ""))
                accent = "--c-case" if label == "执行者" else "--c-device"
                body = facts(
                    [
                        ("角色", label),
                        ("提示词字数", len(prompt)),
                        ("工具数", len(tools)),
                    ]
                )
                body += '<div class="sub-h">工具清单</div>' + self._tool_chips(tools)
                body += self._prompt_details(prompt)
                body += self._tool_details(tools)
                cards.append(self._role_card(label, str(item.get("name") or ""), body, accent))
            head = f"角色 {len(roles)} 个 · 提示词 {chars} 字 · 工具 {tool_total} 个"
        else:
            tools = inputs.get("tool_schemas") or []
            prompt = str(inputs.get("system_prompt") or "")
            head = f"提示词 {len(prompt)} 字 · 工具 {len(tools)} 个"
            cards = [
                self._prompt_details(prompt),
                '<div class="sub-h">工具清单</div>' + self._tool_chips(tools),
                self._tool_details(tools),
            ]
        body = facts(run_rows) + "".join(cards)
        if message:
            body += '<div class="sub-h">用户消息</div>' + markdown(message)
        return self._phase(
            ordinal=ordinal,
            title="准备",
            meta=head,
            body=body,
            accent="--c-dashboard",
        )

    def _stage_round(
        self,
        item: dict,
        reply_id: str,
        usage: dict | None = None,
        ordinal: int | None = None,
    ) -> str:
        items = item["items"]
        tools = sum(1 for o in items if o.get("kind") == "acting")
        cost = sum(
            float(o.get("cost_ms") or 0)
            for o in items
            if o.get("kind") in {"reasoning", "model_call_return"}
        )
        reasoning = next(
            (o for o in items if o.get("kind") == "reasoning" and o.get("phase") == "start"), None
        )
        context_len = (reasoning or {}).get("state", {}).get("context_len") or (
            reasoning or {}
        ).get("context_len")
        usage = usage or {}
        rows = [
            ("上下文条数", context_len),
            ("工具次数", tools),
            ("耗时", f"{cost:.0f} ms"),
        ]
        if usage:
            rows += [
                ("输入 token", usage.get("input_tokens")),
                ("输出 token", usage.get("output_tokens")),
                ("缓存命中 token", usage.get("cache_input_tokens")),
            ]
        if reply_id:
            rows.append(("reply_id", reply_id))
        chain = "".join(
            self._chain_row(index, observation) for index, observation in enumerate(items, 1)
        )
        body = facts(rows) + f'<div class="chain">{chain}</div>'
        meta = (
            f"上下文 {context_len if context_len is not None else '?'} 条 · "
            f"工具 {tools} 次 · 约 {cost:.0f} ms"
        )
        if ordinal is not None:
            return self._phase(
                ordinal=ordinal,
                title=f"第 {item.get('round')} 轮",
                meta=meta,
                body=body,
                accent="--c-element",
            )
        return self._stage_card(f"第 {item.get('round')} 轮", meta, body)

    def _stage_tail(self, document: dict, ordinal: int) -> str:
        summary = sections(document)["summary"]
        final = str(summary.get("final_text") or "")
        cost = summary.get("cost_s")
        body = facts(
            [
                ("耗时", f"{cost} s" if cost is not None else None),
                ("最终文本字数", len(final)),
            ]
        )
        body += markdown(final) if final else '<p class="tip">记录里没有最终文本。</p>'
        return self._phase(
            ordinal=ordinal,
            title="收尾",
            meta=f"耗时 {cost if cost is not None else '?'} s",
            body=body,
            accent="--c-case",
        )

    def _ov_card(
        self,
        title: str,
        meta: str,
        body: str,
        *,
        accent: str,
        tilt: str = "0deg",
        wide: bool = False,
    ) -> str:
        css = "overview-card overview-card--wide" if wide else "overview-card"
        return (
            f'<section class="{css}" style="--ov-accent:var({accent});--tilt:{tilt}">'
            f'<div class="ov-h"><span class="ov-dot"></span><h4>{html.escape(title)}</h4>'
            f'<span class="ov-meta">{html.escape(meta)}</span></div>{body}</section>'
        )

    def _overview(self, document: dict) -> str:
        parts = sections(document)
        run = parts["run"]
        inputs = parts["input"]
        summary = parts["summary"]
        roles = [item for item in inputs.get("roles") or [] if isinstance(item, dict)]
        steps = [item for item in parts["steps"] if isinstance(item, dict)]
        tokens = summary.get("tokens") if isinstance(summary.get("tokens"), dict) else {}
        usages = [item for item in summary.get("usages") or [] if isinstance(item, dict)]
        calls = [o for o in parts["observations"] if o.get("kind") == "model_call"]
        last_images = int(calls[-1].get("framework_images") or 0) if calls else 0
        total_in = int(tokens.get("input", 0) or 0)
        total_out = int(tokens.get("output", 0) or 0)
        cache_hit = int(tokens.get("cache_hit", 0) or 0)
        final = str(summary.get("final_text") or "")
        prompt_chars = (
            sum(len(str(item.get("system_prompt") or "")) for item in roles)
            if roles
            else len(str(inputs.get("system_prompt") or ""))
        )
        tool_total = (
            sum(len(item.get("tool_schemas") or []) for item in roles)
            if roles
            else len(inputs.get("tool_schemas") or [])
        )

        env_rows = [
            (str(key), value)
            for key, value in run.items()
            if key != "roles" and value not in (None, "")
        ]
        env_rows.append(("schema", document.get("schema")))
        env_rows.append(("事件数", document.get("event_count")))

        input_rows: list[tuple[str, object]] = []
        if roles:
            input_rows.append(("角色数", len(roles)))
        input_rows += [("提示词字数", prompt_chars), ("工具数", tool_total)]
        input_body = facts(input_rows)
        if roles:
            for item in roles:
                prompt = str(item.get("system_prompt") or "")
                tools = item.get("tool_schemas") or []
                label = _role_text(item.get("role"), str(item.get("name") or ""))
                accent = "--c-case" if label == "执行者" else "--c-device"
                inner = facts(
                    [("角色", label), ("提示词字数", len(prompt)), ("工具数", len(tools))]
                )
                inner += self._tool_chips(tools)
                inner += self._prompt_details(prompt)
                inner += self._tool_details(tools)
                input_body += self._role_card(label, str(item.get("name") or ""), inner, accent)
        else:
            input_body += self._prompt_details(str(inputs.get("system_prompt") or ""))
            input_body += '<div class="sub-h">工具清单</div>' + self._tool_chips(
                inputs.get("tool_schemas") or []
            )
            input_body += self._tool_details(inputs.get("tool_schemas") or [])
        message = str(inputs.get("user_message") or "")
        if message:
            input_body += '<div class="sub-h">用户消息</div>' + markdown(message)

        cost = summary.get("cost_s")
        usage_rows: list[tuple[str, object]] = [
            (
                "耗时",
                f"{float(cost):.1f} s" if isinstance(cost, (int, float)) else "未知",
            )
        ]
        if tokens:
            usage_rows += [
                ("输入 token", tokens.get("input")),
                ("输出 token", tokens.get("output")),
                ("缓存命中 token", tokens.get("cache_hit")),
                ("缓存写入 token", tokens.get("cache_creation")),
                ("总计", total_in + total_out),
            ]
        else:
            usage_rows.append(("token", "未知"))
        if total_in:
            usage_rows += [
                ("缓存命中率", f"{cache_hit / total_in:.0%}"),
                ("未命中输入", f"{max(total_in - cache_hit, 0):,}"),
            ]
        if last_images:
            usage_rows.append(("末轮保留图片", last_images))
        usage_body = facts(usage_rows)
        if total_in:
            hit = max(0, min(cache_hit, total_in))
            miss = total_in - hit
            usage_body += (
                '<div class="cache-bar" aria-hidden="true">'
                f'<span class="hit" style="width:{hit / total_in * 100:.2f}%"></span>'
                f'<span class="miss" style="width:{miss / total_in * 100:.2f}%"></span></div>'
                '<p class="tip">绿为缓存命中，灰为未命中。</p>'
            )

        if usages:
            body_rows: list[str] = []
            sum_in = sum_out = sum_cache = 0
            for item in usages:
                item_in = int(item.get("input_tokens") or 0)
                item_out = int(item.get("output_tokens") or 0)
                item_cache = int(item.get("cache_input_tokens") or 0)
                sum_in += item_in
                sum_out += item_out
                sum_cache += item_cache
                body_rows.append(
                    "<tr>"
                    f"<td>{html.escape(str(item.get('round') or ''))}</td>"
                    f'<td class="t">{html.escape(str(item.get("model") or ""))}</td>'
                    f"<td>{item_in:,}</td><td>{item_out:,}</td><td>{item_cache:,}</td>"
                    f"<td>{html.escape(clock(item.get('started_at')))}</td>"
                    f"<td>{html.escape(clock(item.get('ended_at')))}</td></tr>"
                )
            usage_table = (
                '<div class="table-wrap"><table class="data-table">'
                "<thead><tr><th>轮次</th><th>模型</th><th>输入</th><th>输出</th><th>缓存</th>"
                "<th>开始</th><th>结束</th></tr></thead><tbody>"
                + "".join(body_rows)
                + '<tr class="total"><td colspan="2">合计</td>'
                f"<td>{sum_in:,}</td><td>{sum_out:,}</td><td>{sum_cache:,}</td>"
                '<td colspan="2"></td></tr></tbody></table></div>'
            )
        else:
            usage_table = '<p class="tip">记录里没有逐次调用用量。</p>'

        step_card = ""
        if steps:
            passed = sum(1 for item in steps if item.get("passed"))
            failed = [item for item in steps if not item.get("passed")]
            step_body = facts(
                [
                    ("步骤数", len(steps)),
                    ("通过", passed),
                    ("未通过", len(failed)),
                    ("阶段", summary.get("phase")),
                ]
            )
            if failed:
                step_body += "".join(
                    facts(
                        [
                            ("步骤", item.get("subject")),
                            ("说明", item.get("message")),
                            ("预期", item.get("expected")),
                        ]
                    )
                    for item in failed
                )
            else:
                step_body += '<p class="tip">每一步都通过了。</p>'
            step_card = self._ov_card(
                "步骤结论",
                f"{len(steps)} 步",
                step_body,
                accent="--c-runner",
                tilt="0.5deg",
            )

        result_body = markdown(final) if final else '<p class="tip">记录里没有最终文本。</p>'
        path_rows = [
            (key, summary.get(key))
            for key in ("log_path", "html_path", "raw_path", "aligned_path")
            if summary.get(key)
        ]
        path_body = facts(path_rows, inline_limit=400) or '<p class="tip">记录里没有路径。</p>'

        cards = [
            self._ov_card(
                "运行环境",
                "run",
                facts(env_rows) or '<p class="tip">记录里没有 run 段。</p>',
                accent="--c-dashboard",
                tilt="-0.5deg",
            ),
            self._ov_card(
                "输入条件",
                f"提示词 {prompt_chars} 字 · 工具 {tool_total} 个",
                input_body,
                accent="--c-element",
                tilt="0.4deg",
            ),
            self._ov_card("用量", "summary", usage_body, accent="--c-device", tilt="-0.35deg"),
            self._ov_card(
                "逐次调用用量",
                f"{len(usages)} 次",
                usage_table,
                accent="--c-workflow",
                tilt="0.3deg",
                wide=True,
            ),
            step_card,
            self._ov_card(
                "结果",
                f"{len(final)} 字",
                result_body,
                accent="--c-case",
                tilt="-0.3deg",
                wide=True,
            ),
            self._ov_card(
                "产物路径",
                f"{len(path_rows)} 条",
                path_body,
                accent="--c-report",
                tilt="0.45deg",
                wide=True,
            ),
        ]
        return '<div class="overview-grid">' + "".join(card for card in cards if card) + "</div>"

    def _events(self, document: dict) -> str:
        events = sections(document)["events"]
        if not events:
            return '<p class="tip">这份记录里没有事件。</p>'
        plain = [event for event in events if not str(event.get("type") or "").endswith("_DELTA")]
        deltas = [event for event in events if str(event.get("type") or "").endswith("_DELTA")]
        rows = "".join(self._log_row(index, event) for index, event in enumerate(plain, 1))
        if deltas:
            rows += (
                f'<details class="jfold"><summary>增量事件 {len(deltas)} 条（默认折叠）</summary>'
                + "".join(
                    self._log_row(index, event, compact=True)
                    for index, event in enumerate(deltas, 1)
                )
                + "</details>"
            )
        return rows

    def _raw(self, document: dict) -> str:
        parts = sections(document)
        blocks: list[str] = []
        for key in ("run", "input", "steps", "observations", "summary"):
            if key == "steps" and not parts["steps"]:
                continue
            text = json.dumps(parts[key], ensure_ascii=False, indent=1)
            cut = len(text) > 20000
            note = '<p class="tip">已截断：仅显示前 20,000 字。</p>' if cut else ""
            opened = " open" if len(text) <= 4000 else ""
            blocks.append(
                f'<section class="raw-card"><details class="jfold"{opened}>'
                f'<summary><b>{key}</b><span class="ov-meta">{len(text):,} 字</span></summary>'
                f"{note}{json_block(parts[key], limit=20000 if cut else 0)}</details></section>"
            )
        return "".join(blocks)

    def _log_row(self, index: int, event: dict, compact: bool = False) -> str:
        kind = str(event.get("type") or "")
        name = _event_name(kind)
        css, label = _EVENT_KIND.get(name, ("log-misc", kind))
        rows: list[tuple[str, object]] = []
        for key, value in event.items():
            if key in {"type", "created_at"}:
                continue
            if compact and isinstance(value, str) and len(value) > 120:
                value = value[:120] + "…"
            rows.append((str(key), value))
        stamp = clock(event.get("created_at"))
        classes = f"event {css}" + (" compact" if compact else "")
        return (
            f'<div class="{classes}">'
            f'<div class="event-h"><span class="event-t">{html.escape(stamp)}</span>'
            f'<span class="log-badge">{html.escape(label)}</span>'
            f'<span class="event-type">#{index} {html.escape(name or kind)}</span></div>'
            f"{facts(rows)}</div>"
        )
