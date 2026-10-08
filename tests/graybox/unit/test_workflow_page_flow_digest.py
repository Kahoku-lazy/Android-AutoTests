"""灰盒·单元测试 — 页面流语义摘要只给「页面与节点关系」。

守的是本变更的核心口径（此前该摘要零测试覆盖）：
1. 节点不输出元素清单（`elements`）与逐页跳转入口清单（`navigation_entries`）；
2. 仍保留可命名点击目标的信息（连线的触发口名称）与路径；
3. 起点节点仍只输出 `start_kind` / `package_name`（既有规格，不受本变更影响）；
4. 诊断不退化：端口槽位"有值但不可解析"仍进 `parse_warnings`，且同一连线只记一次。

纯函数用例：合成 config，无数据库、无模型调用。
"""

import pytest

from apps.workflow.semantics import build_graph_digest

pytestmark = [pytest.mark.unit, pytest.mark.workflow]


def _config() -> dict:
    """一段最小可用的页面流：启动 App → APP主页 →(设备主页入口)→ 设备主页页面。"""
    return {
        "nodes": [
            {
                "id": "n1",
                "type": "StartNode",
                "widgets_values": ["启动 App"],
                "properties": {
                    "start_kind": "app",
                    "package_name": "com.govee.home",
                    # 历史遗留字段：摘要必须不输出它们（既有规格）
                    "start_url": "https://legacy.example",
                    "start_api": "/legacy/api",
                },
                "outputs": [{"name": "启动", "slot_index": 0, "type": "navigation"}],
            },
            {
                "id": "n2",
                "type": "PageNode",
                "widgets_values": ["APP主页"],
                "properties": {
                    "linked_page_id": "p1",
                    "linked_page_name": "APP主页",
                    "linked_elements": [
                        {"id": "957", "label": "设备主页入口", "type": "button", "xpath": ""}
                    ],
                },
                "inputs": [{"name": "进入", "slot_index": 0, "type": "navigation"}],
                "outputs": [
                    {
                        "name": "设备主页入口",
                        "slot_index": 0,
                        "type": "navigation",
                        "el": {"id": "957", "label": "设备主页入口", "type": "button", "xpath": ""},
                    }
                ],
            },
            {
                "id": "n3",
                "type": "PageNode",
                "widgets_values": ["设备主页页面"],
                "properties": {"linked_page_id": "p2", "linked_page_name": "设备主页页面"},
                "inputs": [{"name": "进入", "slot_index": 0, "type": "navigation"}],
            },
        ],
        "links": [
            {
                "id": 1,
                "type": "navigation",
                "origin_id": "n1",
                "target_id": "n2",
                "origin_slot": 0,
                "target_slot": 0,
            },
            {
                "id": 2,
                "type": "navigation",
                "origin_id": "n2",
                "target_id": "n3",
                "origin_slot": 0,
                "target_slot": 0,
            },
        ],
    }


def test_nodes_have_no_element_inventory():
    """节点条目不得再带 elements / navigation_entries（本变更的核心）。"""
    digest = build_graph_digest(_config())

    assert digest["node_count"] == 3
    for node in digest["nodes"]:
        assert "elements" not in node, f"{node['node_id']} 仍输出元素清单"
        assert "navigation_entries" not in node, f"{node['node_id']} 仍输出跳转入口清单"


def test_links_keep_trigger_names_for_naming_targets():
    """瘦身不得牺牲"能命名点击目标"：连线仍带触发口名称，路径仍产出。"""
    digest = build_graph_digest(_config())

    links = {l["id"]: l for l in digest["links"]}
    assert links[2]["from_port_name"] == "设备主页入口"
    assert links[2]["from_node_name"] == "APP主页"
    assert links[2]["to_node_name"] == "设备主页页面"
    assert digest["paths"], "路径摘要不应为空"


def test_relations_are_kept():
    """页面身份与出入关系仍在（被删的只是元素，不是关系）。"""
    digest = build_graph_digest(_config())

    by_id = {n["node_id"]: n for n in digest["nodes"]}
    assert by_id["n2"]["page"] == {"page_id": "p1", "page_name": "APP主页", "domain": "android"}
    assert by_id["n3"]["entry_points"], "页面节点应保留进入关系"
    assert by_id["n2"]["entry_points"], "页面节点应保留进入关系"


def test_start_node_fields_still_narrowed():
    """既有规格：起点摘要只输出 start_kind 与 package_name。"""
    digest = build_graph_digest(_config())

    start = next(n for n in digest["nodes"] if n["node_id"] == "n1")
    assert start["start_kind"] == "app"
    assert start["package_name"] == "com.govee.home"
    assert "start_url" not in start and "start_api" not in start


def test_unparsable_slot_still_warns_once():
    """诊断不退化：槽位"有值但不可解析"仍进 parse_warnings，且同一连线只记一次。"""
    config = _config()
    config["links"].append(
        {
            "id": 3,
            "type": "navigation",
            "origin_id": "n2",
            "target_id": "n3",
            "origin_slot": "abc",  # 有值但不可解析
            "target_slot": 0,
        }
    )
    digest = build_graph_digest(config)

    hits = [w for w in digest["parse_warnings"] if "端口槽位不可解析" in w]
    assert len(hits) == 1, f"应恰好记录一次，实际：{digest['parse_warnings']}"
    assert "3" in hits[0]


def test_tolerates_broken_config():
    """容忍非 dict / 缺字段输入（既有降级口径不因本变更改变）。"""
    assert build_graph_digest(None)["node_count"] == 0
    assert build_graph_digest("不是 JSON")["node_count"] == 0
    digest = build_graph_digest({"nodes": [{"id": "x", "type": "UnknownNode"}]})
    assert digest["parse_warnings"], "未知节点类型应记告警"
