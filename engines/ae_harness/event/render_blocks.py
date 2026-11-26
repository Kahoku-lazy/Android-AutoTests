from __future__ import annotations

import html
import json
import re

from typing import Any, Iterable

from markdown_it import MarkdownIt

__all__ = [
    "clock",
    "fact",
    "fact_html",
    "facts",
    "json_block",
    "json_value",
    "markdown",
    "pre_text",
]

_MD = MarkdownIt("commonmark", {"html": False, "linkify": False, "typographer": False})
_MD.enable("table")
_MD.enable("strikethrough")

_JSON_TOKEN = re.compile(
    r'("(?:\\.|[^"\\])*")(\s*:)?'
    r"|(-?\d+(?:\.\d+)?(?:[eE][+-]?\d+)?)"
    r"|\b(true|false|null)\b"
)

_CLOCK = re.compile(r"(\d{2}:\d{2}:\d{2})(?:\.(\d{1,6}))?")

_INLINE_LIMIT = 96


def _escape(text: str) -> str:
    return html.escape(text, quote=False)


def clock(value: Any) -> str:
    text = str(value or "")
    match = _CLOCK.search(text)
    if not match:
        return text
    fraction = match.group(2) or ""
    return f"{match.group(1)}.{fraction[:3]}" if fraction else match.group(1)


def _highlight(text: str) -> str:
    parts: list[str] = []
    cursor = 0
    for match in _JSON_TOKEN.finditer(text):
        parts.append(_escape(text[cursor : match.start()]))
        if match.group(1) is not None:
            if match.group(2):
                parts.append(
                    f'<span class="j-key">{_escape(match.group(1))}</span>{_escape(match.group(2))}'
                )
            else:
                parts.append(f'<span class="j-str">{_escape(match.group(1))}</span>')
        elif match.group(3) is not None:
            parts.append(f'<span class="j-num">{_escape(match.group(3))}</span>')
        else:
            parts.append(f'<span class="j-lit">{_escape(match.group(0))}</span>')
        cursor = match.end()
    parts.append(_escape(text[cursor:]))
    return "".join(parts)


def _dump(value: Any, indent: int = 1) -> str | None:
    if isinstance(value, str):
        text = value.strip()
        if not text or text[:1] not in {"{", "["}:
            return None
        try:
            value = json.loads(text)
        except (ValueError, TypeError):
            return None
    try:
        return json.dumps(value, ensure_ascii=False, indent=indent, default=str)
    except (TypeError, ValueError):
        return None


def _folded(block: str, summary: str) -> str:
    return f'<details class="jfold"><summary>{_escape(summary)}</summary>{block}</details>'


def _json_lines(text: str) -> int:
    return text.count("\n") + 1


def json_block(value: Any, *, fold: str = "", indent: int = 1, limit: int = 0) -> str:
    text = _dump(value, indent)
    if text is None:
        return pre_text("" if value is None else str(value), fold=fold)
    if limit and len(text) > limit:
        text = text[:limit]
    block = f'<pre class="json">{_highlight(text)}</pre>'
    if fold and _json_lines(text) > 20:
        return _folded(block, f"{fold}（{_json_lines(text)} 行）")
    return block


def pre_text(text: str, *, fold: str = "") -> str:
    body = _escape(str(text or ""))
    block = f'<pre class="text">{body}</pre>'
    if fold and (len(body) > 600 or body.count("\n") > 12):
        return _folded(block, f"{fold}（{len(body)} 字）")
    return block


def json_value(value: Any, *, inline_limit: int = _INLINE_LIMIT, fold: str = "") -> str:
    if value is None:
        return '<span class="muted">—</span>'
    if isinstance(value, bool):
        return f'<span class="mono">{str(value).lower()}</span>'
    if isinstance(value, (int, float)):
        if isinstance(value, int):
            return f'<span class="mono">{value:,}</span>'
        return f'<span class="mono">{value}</span>'
    if isinstance(value, (dict, list, tuple)):
        return json_block(value, fold=fold)
    text = str(value)
    dumped = _dump(text)
    if dumped is not None:
        return json_block(text, fold=fold)
    if "\n" in text or len(text) > inline_limit:
        return pre_text(text, fold=fold)
    return _escape(text)


def markdown(text: str) -> str:
    return f'<div class="md">{_MD.render(str(text or ""))}</div>'


def fact_html(label: str, value_html: str) -> str:
    return (
        f'<div class="fact"><span class="fact__k">{_escape(label)}</span>'
        f'<div class="fact__v">{value_html}</div></div>'
    )


def fact(label: str, value: Any, *, inline_limit: int = _INLINE_LIMIT) -> str:
    return fact_html(label, json_value(value, inline_limit=inline_limit, fold=label))


def facts(rows: Iterable[tuple[str, Any]], *, inline_limit: int = _INLINE_LIMIT) -> str:
    items = [
        fact(label, value, inline_limit=inline_limit)
        for label, value in rows
        if label and value not in (None, "", [], {})
    ]
    if not items:
        return ""
    return f'<div class="facts">{"".join(items)}</div>'
