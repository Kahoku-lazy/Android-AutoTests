"""page_flow_compiler — 结构化页面关系 → VueFlow config_json 单元测试。"""

import pytest

from apps.workflow.page_flow_compiler import compile_page_flow_document
from apps.workflow.semantics import build_graph_digest

pytestmark = [pytest.mark.unit, pytest.mark.workflow]

_PAGES = [
    {
        "page_id": 12,
        "label": "首页",
        "elements": [
            {"element_id": 123, "alias": "搜索图标", "type": "icon", "xpath": "//*[@rid='s']"},
            {"element_id": 124, "alias": "设备卡片", "type": "card", "xpath": ""},
        ],
    },
    {"page_id": 13, "label": "设备详情", "elements": []},
]
_EDGES = [{"from_page_id": 12, "to_page_id": 13, "trigger_element_id": 124}]


def test_compile_generates_start_and_pages():
    cfg = compile_page_flow_document(
        title="t", start_package="com.govee.home", pages=_PAGES, edges=_EDGES
    )
    types = [n["type"] for n in cfg["nodes"]]
    assert types == ["StartNode", "PageNode", "PageNode"]
    assert cfg["nodes"][0]["properties"]["package_name"] == "com.govee.home"
    assert len(cfg["links"]) == 2  # 启动→主页 + 主页→设备详情


def test_compile_output_port_only_for_trigger_elements():
    cfg = compile_page_flow_document(title="t", start_package="p", pages=_PAGES, edges=_EDGES)
    home = cfg["nodes"][1]
    # 只有「设备卡片」是跳转元素，才有输出口；「搜索图标」没有
    assert [p["el"]["id"] for p in home["outputs"]] == ["124"]


def test_compile_parses_into_semantics():
    cfg = compile_page_flow_document(
        title="t", start_package="com.govee.home", pages=_PAGES, edges=_EDGES
    )
    d = build_graph_digest(cfg)
    home = [n for n in d["nodes"] if n.get("page", {}).get("page_name") == "首页"][0]
    # 设备卡片 → 设备详情
    assert home["navigation_entries"][0]["label"] == "设备卡片"
    assert home["navigation_entries"][0]["navigates_to"][0]["name"] == "设备详情"


def test_compile_no_edges_no_output_ports():
    cfg = compile_page_flow_document(title="t", start_package="p", pages=_PAGES, edges=[])
    home = cfg["nodes"][1]
    assert home["outputs"] == []
    assert len(cfg["links"]) == 1  # 仅 启动→主页
