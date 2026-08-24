"""workflow 页面流语义摘要 — 图 → AI 可读结构.

纯函数模块（不写库、不 import 其它 App）。输入 config dict（nodes/links），
输出页面关系 / 跳转入口 / 页面下元素 / 路径摘要。对外出口见 ``api.py`` 的
``get_document_digest`` / ``list_document_summaries``。

字段口径（与前端 types/workflow.ts 对齐）：
  - 节点 type: StartNode/PageNode/PopupNode/ApiNode/EndNode → start/page/popup/api/end
  - 端口 type: entry/navigation/popup_trigger/popup_fixed/popup_close/data
  - 元素来源（不实时 join 元素库，快照为准）:
      snapshot      数字 ID（元素定位库快照）
      web_snapshot  web_ 前缀（Web 元素分组快照）
      builtin_pool  el_/pe_ 前缀（前端静态元素池，无归属页面）
      unknown       无法识别
"""

from __future__ import annotations

import json

from typing import Any

PORT_ENTRY = "entry"
PORT_NAVIGATION = "navigation"
PORT_POPUP_TRIGGER = "popup_trigger"
PORT_POPUP_FIXED = "popup_fixed"
PORT_POPUP_CLOSE = "popup_close"
PORT_DATA = "data"

MAX_PATH_DEPTH = 32
MAX_PATHS = 10

_NODE_TYPE_MAP = {
    "StartNode": "start",
    "PageNode": "page",
    "PopupNode": "popup",
    "ApiNode": "api",
    "EndNode": "end",
}


def _str(v: Any) -> str:
    return "" if v is None else str(v).strip()


def _parse_config(raw: Any) -> dict:
    """容忍 str / None / 非 dict 输入，返回 dict。"""
    if isinstance(raw, str):
        try:
            raw = json.loads(raw)
        except Exception:
            return {}
    return raw if isinstance(raw, dict) else {}


def _name_of(node: dict) -> str:
    """节点名 = widgets_values[0]，缺失回退 node id。"""
    wv = node.get("widgets_values") if isinstance(node, dict) else None
    if isinstance(wv, list) and wv:
        return _str(wv[0]) or _str(node.get("id"))
    return _str(node.get("id"))


def _element_source(el_id: str) -> str:
    """元素 ID 前缀 → 来源标注。"""
    el_id = _str(el_id)
    if el_id.startswith("web_"):
        return "web_snapshot"
    if el_id.startswith("el_") or el_id.startswith("pe_"):
        return "builtin_pool"
    if el_id.isdigit():
        return "snapshot"
    return "unknown"


def _element_domain(el_id: str) -> str:
    return "web" if _str(el_id).startswith("web_") else "android"


def _slot_int(v: Any) -> int | None:
    """槽位归一为 int；不可解析返回 None（手改/第三方 JSON 可能传 str 或垃圾值）。"""
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def _slot_matches(a: Any, b: Any) -> bool:
    ai = _slot_int(a)
    return ai is not None and ai == _slot_int(b)


def _output_port(node: dict | None, slot: Any) -> dict | None:
    if not isinstance(node, dict):
        return None
    for p in node.get("outputs") if isinstance(node.get("outputs"), list) else []:
        if isinstance(p, dict) and _slot_matches(p.get("slot_index"), slot):
            return p
    return None


def _input_port(node: dict | None, slot: Any) -> dict | None:
    if not isinstance(node, dict):
        return None
    for p in node.get("inputs") if isinstance(node.get("inputs"), list) else []:
        if isinstance(p, dict) and _slot_matches(p.get("slot_index"), slot):
            return p
    return None


def _target_desc(target: dict | None, target_id: str) -> dict:
    """连线目标节点的可读描述。"""
    return {
        "node_id": target_id,
        "name": _name_of(target) if target else "",
        "node_type": _NODE_TYPE_MAP.get(_str(target.get("type")), "unknown")
        if target
        else "unknown",
    }


def _resolve_port_targets(
    node: dict, slot: Any, port_type: str, links: list, index: dict, warnings: list
) -> dict:
    """端口类型 → 目标语义分组（navigates_to / triggers_popup / close_returns_to / data_to）。"""
    nid = _str(node.get("id"))
    out: dict[str, list[dict]] = {}
    for l in links:
        if not isinstance(l, dict):
            continue
        if _str(l.get("origin_id")) != nid:
            continue
        l_slot = _slot_int(l.get("origin_slot"))
        if l_slot is None:
            warnings.append(f"连线 {l.get('id')} 端口槽位不可解析: {l.get('origin_slot')!r}")
            continue
        if l_slot != _slot_int(slot):
            continue
        target_id = _str(l.get("target_id"))
        desc = _target_desc(index.get(target_id), target_id)
        if port_type == PORT_POPUP_FIXED:
            out.setdefault("triggers_popup", []).append(desc)
        elif port_type == PORT_POPUP_CLOSE:
            out.setdefault("close_returns_to", []).append(desc)
        elif port_type == PORT_DATA:
            out.setdefault("data_to", []).append(desc)
        else:
            out.setdefault("navigates_to", []).append(desc)
    return out


def _collect_elements(
    node: dict, links: list, index: dict, warnings: list
) -> tuple[list[dict], list[dict]]:
    """页面下元素 = 端口 el ∪ linked_elements 快照（去重）；跳转入口 = 带 el 的输出端口。"""
    props = node.get("properties") if isinstance(node.get("properties"), dict) else {}
    outputs = node.get("outputs") if isinstance(node.get("outputs"), list) else []
    catalog = props.get("linked_elements") if isinstance(props.get("linked_elements"), list) else []

    elements: dict[str, dict] = {}
    port_entries: list[dict] = []

    for p in outputs:
        if not isinstance(p, dict):
            continue
        el = p.get("el")
        if not isinstance(el, dict):
            continue
        el_id = _str(el.get("id"))
        if not el_id:
            continue
        entry = {
            "element_id": el_id,
            "label": _str(el.get("label")) or _str(p.get("name")),
            "type": _str(el.get("type")),
            "xpath": _str(el.get("xpath")),
            "source": _element_source(el_id),
            "on_port": True,
            "port_slot": p.get("slot_index"),
            "port_type": _str(p.get("type")),
        }
        elements[el_id] = entry
        port_entries.append(entry)

    for e in catalog:
        if not isinstance(e, dict):
            continue
        el_id = _str(e.get("id"))
        if not el_id:
            continue
        if el_id in elements:
            base = elements[el_id]
            if not base["xpath"]:
                base["xpath"] = _str(e.get("xpath"))
            base["label"] = base["label"] or _str(e.get("label"))
        else:
            elements[el_id] = {
                "element_id": el_id,
                "label": _str(e.get("label")),
                "type": _str(e.get("type")),
                "xpath": _str(e.get("xpath")),
                "source": _element_source(el_id),
                "on_port": False,
                "port_slot": None,
                "port_type": None,
            }

    entries: list[dict] = []
    for port in port_entries:
        targets = _resolve_port_targets(
            node, port.get("port_slot"), port.get("port_type") or "", links, index, warnings
        )
        entries.append(
            {
                "element_id": port["element_id"],
                "label": port["label"],
                "xpath": port["xpath"],
                "port_slot": port["port_slot"],
                "port_type": port["port_type"],
                **targets,
            }
        )
    return list(elements.values()), entries


def _collect_entry_points(nid: str, links: list, index: dict) -> list[dict]:
    """节点入边（谁跳转到本节点/本页面）。"""
    pts: list[dict] = []
    for l in links:
        if not isinstance(l, dict):
            continue
        if _str(l.get("target_id")) != nid:
            continue
        origin_id = _str(l.get("origin_id"))
        origin = index.get(origin_id)
        item = {
            "from_node_id": origin_id,
            "from_name": _name_of(origin) if origin else "",
            "port_type": _str(l.get("type")),
        }
        op = _output_port(origin, l.get("origin_slot"))
        if isinstance(op, dict) and isinstance(op.get("el"), dict):
            item["trigger_element"] = {
                "element_id": _str(op["el"].get("id")),
                "label": _str(op["el"].get("label")) or _str(op.get("name")),
            }
        pts.append(item)
    return pts


def _popup_close_targets(node: dict, links: list, index: dict, warnings: list) -> list[dict]:
    """弹窗「关闭」输出端口的目标节点。"""
    outputs = node.get("outputs") if isinstance(node.get("outputs"), list) else []
    for p in outputs:
        if isinstance(p, dict) and p.get("type") == PORT_POPUP_CLOSE:
            resolved = _resolve_port_targets(
                node, p.get("slot_index"), PORT_POPUP_CLOSE, links, index, warnings
            )
            return resolved.get("close_returns_to", [])
    return []


def build_graph_digest(config: Any, doc: Any = None) -> dict:
    """config（nodes/links）→ 语义摘要 dict。

    ``doc`` 可选，提供 doc_id/title 元信息（WorkflowDocument 实例）。
    任何字段缺失均安全降级；悬空连线等异常写入 parse_warnings，绝不抛错。
    """
    cfg = _parse_config(config)
    raw_nodes = cfg.get("nodes")
    raw_links = cfg.get("links")
    nodes = raw_nodes if isinstance(raw_nodes, list) else []
    links = raw_links if isinstance(raw_links, list) else []
    warnings: list[str] = []

    index: dict[str, dict] = {}
    for n in nodes:
        if isinstance(n, dict) and n.get("id"):
            index[_str(n.get("id"))] = n

    summary_nodes: list[dict] = []
    for n in nodes:
        if not isinstance(n, dict):
            warnings.append("存在非对象节点，已跳过")
            continue
        nid = _str(n.get("id"))
        raw_type = _str(n.get("type"))
        node_type = _NODE_TYPE_MAP.get(raw_type, "unknown")
        if raw_type not in _NODE_TYPE_MAP:
            warnings.append(f"节点 {nid} 类型未知: {raw_type or '(空)'}")
        props = n.get("properties") if isinstance(n.get("properties"), dict) else {}

        summary: dict[str, Any] = {"node_id": nid, "node_type": node_type, "name": _name_of(n)}

        # 页面归属（页面/弹窗/页面模式起点）
        page_id = _str(props.get("linked_page_id"))
        page_name = _str(props.get("linked_page_name"))
        if page_id or page_name:
            summary["page"] = {
                "page_id": page_id or None,
                "page_name": page_name or None,
                "domain": _str(props.get("linked_page_domain")) or _element_domain(page_id),
            }

        if node_type == "start":
            summary["start_kind"] = _str(props.get("start_kind"))
            for key in ("package_name", "start_url", "start_api"):
                if props.get(key):
                    summary[key] = _str(props[key])
        elif node_type == "api":
            summary["api"] = {
                "endpoint_id": _str(props.get("linked_endpoint_id")),
                "endpoint_name": _str(props.get("linked_endpoint_name")),
                "method": _str(props.get("api_method")),
                "url": _str(props.get("api_url")),
            }

        if node_type in ("page", "popup") or (node_type == "start" and summary.get("page")):
            elements, entries = _collect_elements(n, links, index, warnings)
            summary["elements"] = elements
            if node_type != "popup":
                summary["navigation_entries"] = entries

        if node_type == "page" or node_type == "end":
            summary["entry_points"] = _collect_entry_points(nid, links, index)
        elif node_type == "popup":
            summary["triggered_by"] = _collect_entry_points(nid, links, index)
            summary["close_returns_to"] = _popup_close_targets(n, links, index, warnings)

        summary_nodes.append(summary)

    resolved_links: list[dict] = []
    for l in links:
        if not isinstance(l, dict):
            continue
        origin_id = _str(l.get("origin_id"))
        target_id = _str(l.get("target_id"))
        origin = index.get(origin_id)
        target = index.get(target_id)
        if origin is None or target is None:
            warnings.append(f"连线 {l.get('id')} 引用了不存在的节点: {origin_id} → {target_id}")
        op = _output_port(origin, l.get("origin_slot"))
        tp = _input_port(target, l.get("target_slot"))
        resolved_links.append(
            {
                "id": l.get("id"),
                "type": _str(l.get("type")),
                "from_node_id": origin_id,
                "from_node_name": _name_of(origin) if origin else "",
                "from_port_name": _str(op.get("name")) if op else "",
                "to_node_id": target_id,
                "to_node_name": _name_of(target) if target else "",
                "to_port_name": _str(tp.get("name")) if tp else "",
            }
        )

    from .semantics_paths import build_paths  # 延迟 import：semantics_paths 依赖本模块

    return {
        "doc_id": _str(getattr(doc, "doc_id", "")),
        "title": _str(getattr(doc, "title", "")),
        "node_count": len(summary_nodes),
        "link_count": len(resolved_links),
        "nodes": summary_nodes,
        "links": resolved_links,
        "paths": build_paths(nodes, links, index),
        "parse_warnings": warnings,
    }
