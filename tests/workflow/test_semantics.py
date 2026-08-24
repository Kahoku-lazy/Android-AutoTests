"""workflow 语义摘要（build_graph_digest）纯函数单元测试 — 零 I/O、零 DB。

覆盖：节点分类 / 页面归属 / 元素合并与来源标注 / 跳转入口与弹窗语义 /
路径摘要（分支、成环、超深截断）/ 悬空连线与异常输入兜底。
"""

import json

import pytest

from apps.workflow.semantics import build_graph_digest

pytestmark = [pytest.mark.unit, pytest.mark.workflow]


# ── 样本图（对齐前端 initDemo 结构 + 弹窗关闭回边）──


def _port(name, ptype, slot, el=None):
    p = {"name": name, "type": ptype, "slot_index": slot, "link": None, "links": []}
    if el is not None:
        p["el"] = el
    return p


def _node(nid, ntype, name, props=None, inputs=None, outputs=None):
    return {
        "id": nid,
        "type": ntype,
        "pos": [0, 0],
        "size": [180, 0],
        "category": "page",
        "inputs": inputs or [],
        "outputs": outputs or [],
        "widgets_values": [name, "teal"],
        "properties": props or {},
    }


def _link(lid, origin_id, origin_slot, target_id, target_slot, ptype):
    return {
        "id": lid,
        "origin_id": origin_id,
        "origin_slot": origin_slot,
        "target_id": target_id,
        "target_slot": target_slot,
        "type": ptype,
    }


def sample_config() -> dict:
    return {
        "name": "首页流程",
        "version": "1.0",
        "nodes": [
            _node(
                "n1",
                "StartNode",
                "启动 App",
                props={"start_kind": "app", "package_name": "com.example.app"},
                outputs=[_port("启动", "navigation", 0)],
            ),
            _node(
                "n2",
                "PageNode",
                "首页",
                props={
                    "linked_page_id": "5",
                    "linked_page_name": "首页",
                    "linked_page_domain": "android",
                    "linked_elements": [
                        {
                            "id": "12",
                            "label": "搜索图标",
                            "type": "icon",
                            "xpath": '//*[@content-desc="搜索"]',
                        },
                        {
                            "id": "13",
                            "label": "我的按钮",
                            "type": "button",
                            "xpath": '//*[@text="我的"]',
                        },
                    ],
                },
                inputs=[_port("入口", "entry", 0)],
                outputs=[
                    _port(
                        "搜索图标",
                        "navigation",
                        0,
                        {"id": "12", "type": "icon", "xpath": '//*[@content-desc="搜索"]'},
                    ),
                    _port(
                        "设置按钮",
                        "popup_fixed",
                        1,
                        {"id": "14", "type": "button", "xpath": '//*[@text="设置"]'},
                    ),
                ],
            ),
            _node(
                "n3",
                "PageNode",
                "搜索结果页",
                props={"linked_page_id": "6", "linked_page_name": "搜索结果页"},
                inputs=[_port("入口", "entry", 0)],
                outputs=[
                    _port(
                        "商品卡片",
                        "navigation",
                        0,
                        {"id": "20", "type": "card", "xpath": '//*[@resource-id="result_item"]'},
                    )
                ],
            ),
            _node(
                "n5",
                "PopupNode",
                "设置弹窗",
                props={"linked_page_id": "7", "linked_page_name": "设置弹窗"},
                inputs=[_port("触发", "popup_trigger", 0)],
                outputs=[_port("关闭", "popup_close", 0)],
            ),
            _node("n6", "EndNode", "结束", inputs=[_port("入口", "entry", 0)]),
        ],
        "links": [
            _link(1, "n1", 0, "n2", 0, "navigation"),
            _link(2, "n2", 0, "n3", 0, "navigation"),
            _link(3, "n2", 1, "n5", 0, "popup_fixed"),
            _link(4, "n5", 0, "n2", 0, "popup_close"),
            _link(5, "n3", 0, "n6", 0, "navigation"),
        ],
    }


def find_node(digest, node_id):
    return next(n for n in digest["nodes"] if n["node_id"] == node_id)


# ── 节点分类与元信息 ──


def test_node_classification_and_meta():
    d = build_graph_digest(sample_config(), doc=None)
    assert d["node_count"] == 5
    assert d["link_count"] == 5
    assert {n["node_type"] for n in d["nodes"]} == {"start", "page", "popup", "end"}
    start = find_node(d, "n1")
    assert start["start_kind"] == "app"
    assert start["package_name"] == "com.example.app"
    assert "page" not in start


def test_page_node_linked_page_block():
    d = build_graph_digest(sample_config())
    page = find_node(d, "n2")
    assert page["page"] == {"page_id": "5", "page_name": "首页", "domain": "android"}


def test_unknown_node_type_warns():
    cfg = sample_config()
    cfg["nodes"].append(_node("n9", "FooNode", "怪节点"))
    d = build_graph_digest(cfg)
    assert find_node(d, "n9")["node_type"] == "unknown"
    assert any("类型未知" in w for w in d["parse_warnings"])


# ── 页面下元素与来源标注 ──


def test_elements_merge_port_and_catalog():
    """端口 el 与 linked_elements 快照合并去重；快照元素无端口标记。"""
    d = build_graph_digest(sample_config())
    els = {e["element_id"]: e for e in find_node(d, "n2")["elements"]}
    assert set(els) == {"12", "13", "14"}
    assert els["12"]["on_port"] is True
    assert els["12"]["source"] == "snapshot"
    assert els["12"]["xpath"] == '//*[@content-desc="搜索"]'
    assert els["13"]["on_port"] is False
    assert els["14"]["on_port"] is True


def test_builtin_pool_elements_have_no_page():
    """未关联页面的节点 + el_/pe_ 前缀元素 → source=builtin_pool，page 块缺失。"""
    cfg = {
        "nodes": [
            _node(
                "p1",
                "PageNode",
                "未关联页",
                outputs=[_port("关闭按钮", "navigation", 0, {"id": "pe_001", "type": "button"})],
            ),
            _node(
                "p2",
                "PageNode",
                "池元素页",
                outputs=[_port("搜索图标", "navigation", 0, {"id": "el_001", "type": "icon"})],
            ),
        ],
        "links": [],
    }
    d = build_graph_digest(cfg)
    n1 = find_node(d, "p1")
    assert "page" not in n1
    assert n1["elements"][0]["source"] == "builtin_pool"
    assert find_node(d, "p2")["elements"][0]["source"] == "builtin_pool"


def test_web_page_domain_and_source():
    cfg = {
        "nodes": [
            _node(
                "w1",
                "PageNode",
                "登录页",
                props={"linked_page_id": "web_12", "linked_page_name": "登录页"},
                outputs=[_port("登录按钮", "navigation", 0, {"id": "web_301", "type": "button"})],
            )
        ],
        "links": [],
    }
    d = build_graph_digest(cfg)
    n = find_node(d, "w1")
    assert n["page"]["domain"] == "web"
    assert n["elements"][0]["source"] == "web_snapshot"


# ── 跳转入口 / 弹窗语义 ──


def test_navigation_entries_with_targets():
    d = build_graph_digest(sample_config())
    entries = find_node(d, "n2")["navigation_entries"]
    by_el = {e["element_id"]: e for e in entries}
    assert by_el["12"]["navigates_to"][0]["node_id"] == "n3"
    assert by_el["12"]["navigates_to"][0]["name"] == "搜索结果页"
    assert by_el["14"]["triggers_popup"][0]["node_id"] == "n5"
    assert by_el["14"]["port_type"] == "popup_fixed"


def test_popup_triggered_by_and_close_returns():
    d = build_graph_digest(sample_config())
    popup = find_node(d, "n5")
    assert popup["triggered_by"][0]["from_node_id"] == "n2"
    assert popup["triggered_by"][0]["trigger_element"]["label"] == "设置按钮"
    assert popup["close_returns_to"][0]["node_id"] == "n2"
    # 弹窗不暴露 navigation_entries
    assert "navigation_entries" not in popup


def test_page_entry_points():
    d = build_graph_digest(sample_config())
    n3 = find_node(d, "n3")
    assert n3["entry_points"][0]["from_node_id"] == "n2"
    assert n3["entry_points"][0]["trigger_element"]["label"] == "搜索图标"


def test_start_page_mode_has_page_and_entries():
    cfg = {
        "nodes": [
            _node(
                "s1",
                "StartNode",
                "起始页面",
                props={"start_kind": "page", "linked_page_id": "9", "linked_page_name": "落地页"},
                outputs=[_port("进入", "navigation", 0, {"id": "30", "type": "button"})],
            ),
            _node("p9", "PageNode", "落地页", inputs=[_port("入口", "entry", 0)]),
        ],
        "links": [_link(1, "s1", 0, "p9", 0, "navigation")],
    }
    d = build_graph_digest(cfg)
    start = find_node(d, "s1")
    assert start["page"]["page_name"] == "落地页"
    assert start["navigation_entries"][0]["navigates_to"][0]["node_id"] == "p9"


# ── 连线可读化与悬空 ──


def test_resolved_links_readable():
    d = build_graph_digest(sample_config())
    l2 = next(x for x in d["links"] if x["id"] == 2)
    assert l2["from_node_name"] == "首页"
    assert l2["from_port_name"] == "搜索图标"
    assert l2["to_node_name"] == "搜索结果页"
    assert l2["to_port_name"] == "入口"
    assert l2["type"] == "navigation"


def test_dangling_link_warns_not_crash():
    cfg = {
        "nodes": [_node("a", "PageNode", "A", outputs=[_port("x", "navigation", 0)])],
        "links": [_link(1, "a", 0, "ghost", 0, "navigation")],
    }
    d = build_graph_digest(cfg)
    assert any("不存在的节点" in w for w in d["parse_warnings"])
    assert d["links"][0]["to_node_name"] == ""


# ── 路径摘要 ──


def test_paths_full_chain_text():
    d = build_graph_digest(sample_config())
    texts = [p["text"] for p in d["paths"]]
    assert any("启动 App" in t and "首页" in t and "搜索结果页" in t and "结束" in t for t in texts)
    assert any("(点击「搜索图标」)" in t for t in texts)


def test_paths_cycle_guard():
    cfg = {
        "nodes": [
            _node("s", "StartNode", "起点", outputs=[_port("启动", "navigation", 0)]),
            _node(
                "a",
                "PageNode",
                "A",
                inputs=[_port("入口", "entry", 0)],
                outputs=[_port("去B", "navigation", 0, {"id": "1", "type": "button"})],
            ),
            _node(
                "b",
                "PageNode",
                "B",
                inputs=[_port("入口", "entry", 0)],
                outputs=[_port("回A", "navigation", 0, {"id": "2", "type": "button"})],
            ),
        ],
        "links": [
            _link(1, "s", 0, "a", 0, "navigation"),
            _link(2, "a", 0, "b", 0, "navigation"),
            _link(3, "b", 0, "a", 0, "navigation"),
        ],
    }
    d = build_graph_digest(cfg)
    assert d["paths"], "循环图应产出被截断的路径而非空"
    assert any("(循环)" in p["text"] for p in d["paths"])
    assert all(len(p["steps"]) <= 4 for p in d["paths"])


def test_paths_depth_cap():
    """超深链不无限递归：深度 > MAX_PATH_DEPTH 截断。"""
    n = 40
    nodes = [_node("s", "StartNode", "起点", outputs=[_port("启动", "navigation", 0)])]
    links = [_link(1, "s", 0, "n0", 0, "navigation")]
    for i in range(n):
        nodes.append(
            _node(
                f"n{i}",
                "PageNode",
                f"页{i}",
                inputs=[_port("入口", "entry", 0)],
                outputs=[_port("下一步", "navigation", 0)],
            )
        )
        links.append(
            _link(i + 2, f"n{i}", 0, f"n{i + 1}" if i + 1 < n else "n_end", 0, "navigation")
        )
    nodes.append(_node("n_end", "EndNode", "结束", inputs=[_port("入口", "entry", 0)]))
    d = build_graph_digest({"nodes": nodes, "links": links})
    assert d["paths"]
    assert any("超深截断" in p["text"] for p in d["paths"])


# ── 异常输入兜底 ──


def test_empty_and_invalid_inputs_no_crash():
    for cfg in ({}, None, [], "not-json{", {"name": "x"}, {"nodes": "bad", "links": 1}):
        d = build_graph_digest(cfg)
        assert d["nodes"] == []
        assert d["paths"] == []


def test_config_as_json_string_parsed():
    raw = json.dumps(sample_config(), ensure_ascii=False)
    d = build_graph_digest(raw)
    assert d["node_count"] == 5


def test_doc_meta_propagated():
    class _Doc:
        doc_id = "WF-PF-TEST"
        title = "标题"

    d = build_graph_digest(sample_config(), doc=_Doc())
    assert d["doc_id"] == "WF-PF-TEST"
    assert d["title"] == "标题"


# ── 审查修复回归（P1 槽位类型归一 / 防御分支覆盖）──


def test_mixed_slot_types_still_resolve():
    """槽位 int/str 混合（手改/第三方 JSON）不静默丢连线（P1 回归）。"""
    cfg = {
        "nodes": [
            _node(
                "a",
                "PageNode",
                "A",
                outputs=[_port("去B", "navigation", "0", {"id": "1", "type": "button"})],
            ),
            _node("b", "PageNode", "B", inputs=[_port("入口", "entry", "0")]),
        ],
        "links": [_link(1, "a", 0, "b", "0", "navigation")],
    }
    d = build_graph_digest(cfg)
    entries = find_node(d, "a")["navigation_entries"]
    assert entries[0]["navigates_to"][0]["node_id"] == "b"
    assert find_node(d, "b")["entry_points"][0]["from_node_id"] == "a"
    assert d["parse_warnings"] == []


def test_unparseable_slot_warns():
    """端口槽位为垃圾值 → 连线被跳过但必须显式警告，不静默。"""
    cfg = {
        "nodes": [
            _node(
                "a",
                "PageNode",
                "A",
                outputs=[_port("x", "navigation", "xx", {"id": "1", "type": "button"})],
            ),
            _node("b", "PageNode", "B", inputs=[_port("入口", "entry", 0)]),
        ],
        "links": [_link(1, "a", "xx", "b", 0, "navigation")],
    }
    d = build_graph_digest(cfg)
    assert any("槽位不可解析" in w for w in d["parse_warnings"])


def test_dangling_link_warns_once():
    """悬空连线全局只警告一次（不因端口解析重复）。"""
    cfg = {
        "nodes": [
            _node(
                "a",
                "PageNode",
                "A",
                outputs=[_port("x", "navigation", 0, {"id": "1", "type": "button"})],
            )
        ],
        "links": [_link(1, "a", 0, "ghost", 0, "navigation")],
    }
    d = build_graph_digest(cfg)
    assert sum(1 for w in d["parse_warnings"] if "不存在的节点" in w) == 1


def test_non_dict_node_skipped_with_warning():
    cfg = {
        "nodes": [_node("ok", "PageNode", "OK"), "junk"],
        "links": [],
    }
    d = build_graph_digest(cfg)
    assert d["node_count"] == 1
    assert any("非对象节点" in w for w in d["parse_warnings"])


def test_origin_dangling_link_warns():
    cfg = {
        "nodes": [_node("b", "PageNode", "B", inputs=[_port("入口", "entry", 0)])],
        "links": [_link(1, "ghost", 0, "b", 0, "navigation")],
    }
    d = build_graph_digest(cfg)
    assert any("不存在的节点" in w for w in d["parse_warnings"])
    assert d["links"][0]["from_node_name"] == ""


def test_popup_without_inbound():
    cfg = {
        "nodes": [
            _node(
                "p",
                "PopupNode",
                "孤弹窗",
                inputs=[_port("触发", "popup_trigger", 0)],
                outputs=[_port("关闭", "popup_close", 0)],
            )
        ],
        "links": [],
    }
    d = build_graph_digest(cfg)
    popup = find_node(d, "p")
    assert popup["triggered_by"] == []
    assert popup["close_returns_to"] == []


def test_no_start_node_paths_empty():
    cfg = {
        "nodes": [
            _node("a", "PageNode", "A"),
            _node("b", "EndNode", "B", inputs=[_port("入口", "entry", 0)]),
        ],
        "links": [],
    }
    assert build_graph_digest(cfg)["paths"] == []


def test_max_paths_cap():
    """分支爆炸图最多产出 MAX_PATHS 条路径。"""
    fanout = 20
    nodes = [_node("s", "StartNode", "起点", outputs=[_port("启动", "navigation", 0)])]
    nodes.append(
        _node(
            "c",
            "PageNode",
            "中心页",
            inputs=[_port("入口", "entry", 0)],
            outputs=[_port(f"出口{i}", "navigation", i) for i in range(fanout)],
        )
    )
    links = [_link(1, "s", 0, "c", 0, "navigation")]
    for i in range(fanout):
        nodes.append(_node(f"p{i}", "PageNode", f"页{i}", inputs=[_port("入口", "entry", 0)]))
        links.append(_link(2 + i, "c", i, f"p{i}", 0, "navigation"))
    nodes.append(_node("e", "EndNode", "结束", inputs=[_port("入口", "entry", 0)]))
    for i in range(fanout):
        links.append(_link(2 + fanout + i, f"p{i}", 0, "e", 0, "navigation"))
    d = build_graph_digest({"nodes": nodes, "links": links})
    assert len(d["paths"]) == 10
