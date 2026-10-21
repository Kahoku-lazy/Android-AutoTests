"""workflow 页面流语义摘要 — 图 → AI 可读结构.

纯函数模块（不写库、不 import 其它 App）。输入 config dict（nodes/links），
输出**页面与节点关系**：页面身份 / 节点出入关系 / 连线（含触发口名称）/ 路径摘要。
MUST NOT 输出页面元素清单——元素不参与规划，其真相源是元素定位域。
对外出口见 ``api.py`` 的 ``get_document_digest`` / ``list_document_summaries``。

字段口径（与前端 types/workflow.ts 对齐）：
  - 节点 type: StartNode/PageNode/PopupNode/EndNode → start/page/popup/end
  - 端口 type: entry/navigation/popup_trigger/popup_fixed/popup_close/data
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

        if node_type == "start":
            summary["start_kind"] = _str(props.get("start_kind"))
            if props.get("package_name"):
                summary["package_name"] = _str(props["package_name"])
        elif node_type == "api":
            summary["api"] = {
                "endpoint_id": _str(props.get("linked_endpoint_id")),
                "endpoint_name": _str(props.get("linked_endpoint_name")),
                "method": _str(props.get("api_method")),
                "url": _str(props.get("api_url")),
            }

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
        for raw_slot in (l.get("origin_slot"), l.get("target_slot")):
            # 端口槽位"有值但不可解析"：原先由元素收集顺带告警，改在连线处产生（去重，避免与弹窗路径重复）
            if raw_slot is not None and _slot_int(raw_slot) is None:
                msg = f"连线 {l.get('id')} 端口槽位不可解析: {raw_slot!r}"
                if msg not in warnings:
                    warnings.append(msg)
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
