"""设备检查器分层查询 — 集成测试。

覆盖变更 add-layers-api-and-node-index：
  A) 采集落「全量节点索引」（未裁剪、不含 XPath 候选，且不在 dump_json 里重复）；
  B) 分层查询：分组摘要、筛减分页、主定位唯一来源、历史快照降级、归属过滤、参数校验；
  C) HTTP 端点：信封、400/404 语义、响应瘦身（不带候选全量）。

真实写库（django_db）；设备与媒体用替身与临时目录隔离，不连设备。
"""

import json

import pytest

from django.contrib.auth import get_user_model
from django.test import Client

from apps.device_inspector import api as inspector_api
from apps.device_inspector import service
from apps.device_inspector.models import Snapshot
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.integration, pytest.mark.device_inspector]

USER = "u1"

FIXTURE_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<hierarchy rotation="0">\n'
    '  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.demo"'
    ' content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false"'
    ' focused="false" scrollable="false" long-clickable="false" password="false" selected="false"'
    ' visible-to-user="true" bounds="[0,0][1080,2340]" drawing-order="0" hint="" display-id="0">\n'
    '    <node index="0" text="设备" resource-id="com.demo:id/tvTitle" class="android.widget.TextView"'
    ' package="com.demo" content-desc="" checkable="false" checked="false" clickable="true" enabled="true"'
    ' focusable="false" focused="false" scrollable="false" long-clickable="false" password="false"'
    ' selected="false" visible-to-user="true" bounds="[58,59][156,217]" drawing-order="1" hint="" display-id="0"/>\n'
    '    <node index="1" text="" resource-id="" class="android.widget.ImageView" package="com.demo"'
    ' content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false"'
    ' focused="false" scrollable="false" long-clickable="false" password="false" selected="false"'
    ' visible-to-user="true" bounds="[200,300][260,360]" drawing-order="2" hint="" display-id="0"/>\n'
    "  </node>\n"
    "</hierarchy>\n"
)


def index_node(class_name="android.widget.TextView", **overrides) -> dict:
    """全量节点索引里的一条节点（形态与采集端写入一致，不含 XPath 候选）。"""
    node = {
        "depth": 1,
        "class_name": class_name,
        "text": "",
        "content_desc": "",
        "resource_id": "",
        "index": "0",
        "bounds": "[0,0][10,10]",
        "x": 0,
        "y": 0,
        "width": 10,
        "height": 10,
        "clickable": False,
        "enabled": True,
        "scrollable": False,
        "checkable": False,
        "checked": False,
        "focusable": False,
        "long_clickable": False,
        "kept_in_snapshot": True,
    }
    node.update(overrides)
    return node


def make_snapshot(nodes=None, elements=None, user=USER) -> Snapshot:
    return Snapshot.objects.create(
        serial="S1",
        method="dump",
        dump_json={"elements": elements or []},
        nodes_json=nodes or [],
        package="com.demo",
        activity=".Main",
        screen_w=1080,
        screen_h=2340,
        created_by=user,
    )


# ══════════════ A) 采集落全量节点索引 ══════════════


class _FakeEngine:
    device_info = {"displayWidth": 1080, "displayHeight": 2340}

    def dump_hierarchy_xml(self):
        return FIXTURE_XML

    def app_current(self):
        return {"package": "com.demo", "activity": ".Main"}


@pytest.mark.django_db
def test_capture_stores_full_node_index_without_candidates(tmp_path, monkeypatch):
    """采集把未裁剪节点写入独立索引列：不含候选、不在 dump_json 里重复、保留标记与展示集一致。"""
    import engines.device.registry as registry

    monkeypatch.setattr(service, "_shot_dir", lambda: tmp_path)
    monkeypatch.setattr(service, "open_inspector_engine", lambda serial: _FakeEngine())
    monkeypatch.setattr(
        service, "capture_page_screenshot", lambda engine, ts: "inspector/shots/capture_x.png"
    )
    monkeypatch.setattr(registry, "close_engine", lambda engine: None)

    data = inspector_api.capture_snapshot(USER, "S1")
    snapshot = Snapshot.objects.get(id=data["snapshot_id"])

    assert snapshot.nodes_json, "采集必须落全量节点索引"
    assert "nodes" not in snapshot.dump_json, "索引单独成列，MUST NOT 在 dump_json 里再写一遍"
    assert all("xpaths" not in node for node in snapshot.nodes_json), "索引不含 XPath 候选"
    assert (
        sum(1 for node in snapshot.nodes_json if node["kept_in_snapshot"]) == snapshot.element_count
    )
    assert len(snapshot.dump_json["elements"]) == snapshot.element_count
    assert len(snapshot.nodes_json) > snapshot.element_count, "索引必须覆盖被展示裁剪丢弃的节点"


@pytest.mark.django_db
def test_snapshot_delete_removes_index(tmp_path, monkeypatch):
    """快照删除后记录与索引一并消失。"""
    monkeypatch.setattr(service, "_shot_dir", lambda: tmp_path)
    snapshot = make_snapshot(nodes=[index_node(text="设备", resource_id="com.demo:id/tv")])

    assert inspector_api.delete_snapshot(snapshot.id, USER) is True
    assert not Snapshot.objects.filter(id=snapshot.id).exists()


# ══════════════ B) 分层查询 ══════════════


@pytest.mark.django_db
def test_layers_summary_has_two_levels_and_keeps_empty_other_group():
    """摘要含一级四组与内容控件下的二级三组；「其它」计数为 0 也出现。"""
    snapshot = make_snapshot(
        nodes=[
            index_node(
                "android.widget.FrameLayout", bounds="[0,0][1080,2340]", width=1080, height=2340
            ),
            index_node("android.widget.TextView", text="设备", resource_id="com.demo:id/tv"),
            index_node("android.widget.ImageView", y=100, bounds="[0,100][40,140]"),
            index_node("android.view.View", y=200, bounds="[0,200][10,210]"),
        ]
    )
    data = inspector_api.list_layers(snapshot.id, USER)

    assert data["source"] == "index"
    keys = [g["key"] for g in data["summary"]["groups"]]
    assert keys == ["layout_container", "scroll_collection", "content_widget", "unclassified"]
    assert data["summary"]["groups"][3]["count"] == 0
    content = data["summary"]["groups"][2]
    assert [c["key"] for c in content["children"]] == ["text", "icon", "other"]
    assert data["summary"]["total"] == sum(g["count"] for g in data["summary"]["groups"])
    assert data["summary"]["total"] == len(data["elements"])


@pytest.mark.django_db
def test_layers_filters_pagination_and_total():
    """分组 / 二级分组 / 交互标志 / 关键词 / 仅保留 / 仅稳定 可组合，分页与命中总数一致。"""
    snapshot = make_snapshot(
        nodes=[
            index_node(
                "android.widget.TextView", text="设备", resource_id="com.demo:id/tv", clickable=True
            ),
            index_node("android.widget.ImageView", y=100, bounds="[0,100][40,140]"),
            index_node("android.view.View", y=200, bounds="[0,200][10,210]"),
            index_node(
                "android.widget.FrameLayout",
                y=300,
                bounds="[0,300][10,310]",
                kept_in_snapshot=False,
                text="被裁文本",
            ),
        ]
    )

    only_text = inspector_api.list_layers(snapshot.id, USER, group="content_widget", sub="text")
    assert [e["level2"] for e in only_text["elements"]] == ["text"]

    clickable = inspector_api.list_layers(snapshot.id, USER, flags=["clickable"])
    assert clickable["total_matched"] == 1
    assert all(e["flags"]["clickable"] for e in clickable["elements"])

    hit = inspector_api.list_layers(snapshot.id, USER, query="设备")
    assert hit["total_matched"] == 1 and hit["elements"][0]["text"] == "设备"

    dropped = inspector_api.list_layers(snapshot.id, USER)
    assert any(not e["kept_in_snapshot"] for e in dropped["elements"]), "被裁元素必须出现在结果里"

    page = inspector_api.list_layers(snapshot.id, USER, offset=0, limit=1)
    assert len(page["elements"]) == 1
    assert page["total_matched"] == dropped["total_matched"]
    assert page["offset"] == 0 and page["limit"] == 1


@pytest.mark.django_db
def test_layers_default_limit_returns_all_and_matches_summary():
    """条数缺省即不截断：> 100 元素的快照全量返回，分组计数与条目数逐项一致。

    回归缺陷：视图曾按缺省 limit=100 切片，摘要仍是全量，前端因此看到
    「内容控件·文本 19」而表格只有 10 条。
    """
    nodes = [
        index_node(
            "android.widget.TextView",
            text="文本 %d" % i,
            y=i * 10,
            bounds="[0,%d][10,%d]" % (i * 10, i * 10 + 10),
        )
        for i in range(120)
    ] + [
        index_node(
            "android.widget.ImageView",
            y=2000 + i * 10,
            bounds="[0,%d][10,%d]" % (2000 + i * 10, 2000 + i * 10 + 10),
        )
        for i in range(30)
    ]
    snapshot = make_snapshot(nodes=nodes)

    data = inspector_api.list_layers(snapshot.id, USER)

    assert data["summary"]["total"] == 150
    assert data["total_matched"] == 150
    assert len(data["elements"]) == 150, "缺省条数不施加隐式上限"
    assert data["limit"] is None, "未施加上限时如实回 None，不谎报上限"
    content = next(g for g in data["summary"]["groups"] if g["key"] == "content_widget")
    for child in content["children"]:
        rows = [
            e
            for e in data["elements"]
            if e["level1"] == "content_widget" and e["level2"] == child["key"]
        ]
        assert len(rows) == child["count"], "二级分组计数必须等于该分组的返回条目数"


@pytest.mark.django_db
def test_layers_legacy_snapshot_degrades_without_faking_dropped_elements():
    """索引缺失的历史快照降级为保留集并标注来源，且不伪造被裁元素。"""
    snapshot = make_snapshot(
        elements=[
            {
                "class_name": "android.widget.TextView",
                "text": "旧快照",
                "resource_id": "",
                "content_desc": "",
                "bounds": "[0,0][10,10]",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "depth": 1,
                "index": "0",
                "clickable": False,
                "enabled": True,
                "scrollable": False,
                "checkable": False,
                "checked": False,
                "focusable": False,
                "long_clickable": False,
                "xpaths": [],
            },
        ]
    )
    data = inspector_api.list_layers(snapshot.id, USER)

    assert data["source"] == "legacy"
    assert data["summary"]["total"] == 1
    assert all(e["kept_in_snapshot"] for e in data["elements"])


@pytest.mark.django_db
def test_layers_rejects_invalid_params_and_other_users():
    """非法分组/二级分组/交互标志抛 ValueError；他人快照返回 None。"""
    snapshot = make_snapshot(nodes=[index_node(text="设备")])

    for kwargs in ({"group": "nope"}, {"sub": "nope"}, {"sub": "icon"}, {"flags": ["nope"]}):
        with pytest.raises(ValueError):
            inspector_api.list_layers(snapshot.id, USER, **kwargs)

    assert inspector_api.list_layers(snapshot.id, "someone-else") is None


@pytest.mark.django_db
def test_layers_payload_is_lean():
    """响应只给主定位，不含候选全量；140 元素量级响应体不超过 100 KB。

    实测 93.2 KB（含 coords/flags/主定位等契约字段）；带候选全量的同规模响应为 134.6 KB 量级，
    阈值留 100 KB 既容得下契约字段，也能在字段无节制膨胀时报警。
    """
    nodes = [
        index_node(
            "android.widget.TextView",
            text="元素 %d" % i,
            resource_id="com.demo:id/tv_%d" % i,
            y=i * 10,
            bounds="[0,%d][100,%d]" % (i * 10, i * 10 + 10),
            clickable=True,
        )
        for i in range(140)
    ]
    snapshot = make_snapshot(nodes=nodes)
    data = inspector_api.list_layers(snapshot.id, USER, limit=500)

    assert len(data["elements"]) == 140
    assert all("xpath_candidates" not in e and "xpaths" not in e for e in data["elements"])
    assert data["elements"][0]["primary"]["stable"] is True
    size = len(json.dumps(data, ensure_ascii=False).encode("utf-8"))
    assert size <= 100 * 1024, "响应体 %d B 超过 100 KB（带候选全量为 134.6 KB 量级）" % size


# ══════════════ C) HTTP 端点 ══════════════


@pytest.mark.django_db
def test_layers_endpoint_envelope_400_and_404():
    """端点遵守信封；非法分组 400、快照不存在 404。"""
    user = get_user_model().objects.create_user(username="layers-user", password="x")
    user_id = str(user.id)
    client = Client()
    headers = {"HTTP_AUTHORIZATION": "Bearer " + create_access_token(user_id)}
    snapshot = make_snapshot(nodes=[index_node(text="设备")], user=user_id)

    ok = client.get(
        "/api/inspector/snapshots/%d/layers/" % snapshot.id, {"group": "content_widget"}, **headers
    )
    assert ok.status_code == 200
    body = ok.json()
    assert body["status"] is True
    assert body["data"]["snapshot_id"] == snapshot.id
    assert body["data"]["elements"]

    bad = client.get(
        "/api/inspector/snapshots/%d/layers/" % snapshot.id, {"group": "nope"}, **headers
    )
    assert bad.status_code == 400
    assert "分组" in bad.json()["message"]

    bad_page = client.get(
        "/api/inspector/snapshots/%d/layers/" % snapshot.id, {"limit": "abc"}, **headers
    )
    assert bad_page.status_code == 400

    zero_page = client.get(
        "/api/inspector/snapshots/%d/layers/" % snapshot.id, {"limit": "0"}, **headers
    )
    assert zero_page.status_code == 400, "显式条数必须为正整数"

    missing = client.get("/api/inspector/snapshots/999999/layers/", **headers)
    assert missing.status_code == 404


@pytest.mark.django_db
def test_layers_endpoint_default_limit_returns_all():
    """端点缺省不改写数据：> 100 元素时不截断，条数字段为 null。"""
    user = get_user_model().objects.create_user(username="layers-all", password="x")
    user_id = str(user.id)
    headers = {"HTTP_AUTHORIZATION": "Bearer " + create_access_token(user_id)}
    nodes = [
        index_node(
            "android.widget.TextView",
            text="文本 %d" % i,
            y=i * 10,
            bounds="[0,%d][10,%d]" % (i * 10, i * 10 + 10),
        )
        for i in range(120)
    ]
    snapshot = make_snapshot(nodes=nodes, user=user_id)
    client = Client()

    body = client.get("/api/inspector/snapshots/%d/layers/" % snapshot.id, **headers).json()

    assert body["status"] is True
    assert body["data"]["total_matched"] == 120
    assert len(body["data"]["elements"]) == 120
    assert body["data"]["limit"] is None
