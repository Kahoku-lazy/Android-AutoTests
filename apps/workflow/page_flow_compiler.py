"""workflow 页面流编译器 — 结构化「页面关系」→ VueFlow config_json（纯函数，零 apps 依赖）。

输入 pages/edges，输出与前端 workflowStore/semantics.py 对齐的 {name, nodes, links}。
元素输出口仅给「有跳转边」的元素（navigation 类型）；其余元素只进 linked_elements。
"""

from __future__ import annotations

from datetime import datetime
from typing import Any


def _el_port_name(el: dict, el_id: str) -> str:
    return (el.get("alias") or "").strip() or (el.get("label") or "").strip() or f"元素{el_id}"


def _el_def(el: dict) -> dict:
    el_id = str(el.get("element_id") or "")
    return {
        "id": el_id,
        "label": _el_port_name(el, el_id),
        "type": el.get("type") or "button",
        "xpath": el.get("xpath") or "",
    }


def compile_page_flow_document(
    *, title: str = "", start_package: str = "", pages: list[dict], edges: list[dict]
) -> dict:
    """pages: [{page_id, label, elements:[{element_id, alias, type, xpath}]}]
    edges: [{from_page_id, to_page_id, trigger_element_id}]

    Returns VueFlow config: {name, version, savedAt, nodes, links}.
    首个 page 视为「主页」，StartNode 连向它。
    """
    pages = pages or []
    edges = edges or []

    nodes: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []

    # ── StartNode（启动 App）──
    nodes.append(
        {
            "id": "n1",
            "type": "StartNode",
            "pos": [40, 200],
            "size": [200, 0],
            "category": "start",
            "inputs": [],
            "outputs": [
                {
                    "name": "启动",
                    "type": "navigation",
                    "slot_index": 0,
                    "link": None,
                    "links": [],
                }
            ],
            "widgets_values": ["启动 App", "green"],
            "properties": {"start_kind": "app", "package_name": start_package},
        }
    )

    # ── PageNode ──
    page_node: dict[Any, str] = {}  # page_id -> node_id
    output_slot: dict[tuple, int] = {}  # (from_page_id, trigger_element_id) -> slot

    for idx, page in enumerate(pages):
        page_id = page.get("page_id")
        nid = f"n{idx + 2}"
        page_node[page_id] = nid

        elements = page.get("elements") or []
        el_by_id = {str(e.get("element_id")): e for e in elements}

        # 跳转元素 = 有出边的元素（去重，保持顺序）
        trigger_ids: list[str] = []
        for edge in edges:
            if edge.get("from_page_id") == page_id and edge.get("trigger_element_id") is not None:
                te = str(edge["trigger_element_id"])
                if te not in trigger_ids:
                    trigger_ids.append(te)

        outputs: list[dict[str, Any]] = []
        for te in trigger_ids:
            el = el_by_id.get(te)
            if el is None:
                continue
            slot = len(outputs)
            outputs.append(
                {
                    "name": _el_port_name(el, te),
                    "type": "navigation",
                    "slot_index": slot,
                    "link": None,
                    "links": [],
                    "el": {
                        "id": te,
                        "type": el.get("type") or "button",
                        "xpath": el.get("xpath") or "",
                    },
                }
            )
            output_slot[(page_id, te)] = slot

        label = (page.get("label") or "").strip() or f"页面{page_id}"
        nodes.append(
            {
                "id": nid,
                "type": "PageNode",
                "pos": [40 + idx * 260, 200],
                "size": [180, 0],
                "category": "page",
                "inputs": [
                    {
                        "name": "入口",
                        "type": "entry",
                        "slot_index": 0,
                        "link": None,
                        "links": [],
                    }
                ],
                "outputs": outputs,
                "widgets_values": [label, "teal"],
                "properties": {
                    "linked_page_id": str(page_id),
                    "linked_page_name": label,
                    "linked_page_domain": "android",
                    "linked_elements": [_el_def(e) for e in elements],
                },
            }
        )

    # ── links ──
    link_id = 1
    if pages and pages[0].get("page_id") in page_node:
        links.append(
            {
                "id": link_id,
                "origin_id": "n1",
                "origin_slot": 0,
                "target_id": page_node[pages[0]["page_id"]],
                "target_slot": 0,
                "type": "navigation",
            }
        )
        link_id += 1

    for edge in edges:
        from_id = edge.get("from_page_id")
        to_id = edge.get("to_page_id")
        te = edge.get("trigger_element_id")
        if from_id not in page_node or to_id not in page_node or te is None:
            continue
        slot = output_slot.get((from_id, str(te)))
        if slot is None:
            continue
        links.append(
            {
                "id": link_id,
                "origin_id": page_node[from_id],
                "origin_slot": slot,
                "target_id": page_node[to_id],
                "target_slot": 0,
                "type": "navigation",
            }
        )
        link_id += 1

    return {
        "name": (title or "").strip() or "页面流",
        "version": "1.0",
        "savedAt": datetime.now().isoformat(),
        "nodes": nodes,
        "links": links,
    }
