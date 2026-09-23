"""灰盒·单元测试 — 检查器采集编排：引擎只给原始 XML，解析归算法层。

覆盖变更 add-element-layering-core 的调用方改造：编排不再假定引擎返回 Node 列表，
而是取原始 XML 后经 algorithms.hierarchy 解析。零 I/O（媒体目录指向临时目录）、不连设备。
"""

import pytest

from apps.device_inspector import service

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


class _FakeEngine:
    """只实现层级取数与当前应用查询的引擎替身：不解析、不返回 Node。"""

    def dump_hierarchy_xml(self):
        return FIXTURE_XML

    def app_current(self):
        return {"package": "com.demo", "activity": ".Main"}


@pytest.mark.unit
@pytest.mark.device_inspector
def test_capture_dump_payload_uses_algorithm_layer_parsing(tmp_path, monkeypatch):
    """编排取原始 XML 后经算法层解析，产出元素与可交互子集。"""
    monkeypatch.setattr(service, "_shot_dir", lambda: tmp_path)

    data = service.capture_dump_payload(_FakeEngine(), "20260101_000000_000000")

    assert data["package"] == "com.demo"
    assert data["element_count"] == len(data["elements"])
    assert data["actionable_count"] == len(data["actionable"])
    element_ids = {id(e) for e in data["elements"]}
    assert all(id(a) in element_ids for a in data["actionable"]), "可交互子集必须取自同一批元素对象"

    title = next(e for e in data["elements"] if e["resource_id"] == "com.demo:id/tvTitle")
    assert title["text"] == "设备"
    assert title["xpaths"], "有身份的节点应生成 XPath 候选"
    assert title["bounds"] == "[58,59][156,217]"
    assert (title["x"], title["y"], title["width"], title["height"]) == (58, 59, 98, 158)


@pytest.mark.unit
@pytest.mark.device_inspector
def test_capture_dump_payload_propagates_engine_failure(tmp_path, monkeypatch):
    """引擎取数失败时向上抛错，不返回半成品。"""
    monkeypatch.setattr(service, "_shot_dir", lambda: tmp_path)

    class _BrokenEngine:
        def dump_hierarchy_xml(self):
            raise RuntimeError("dump failed")

    with pytest.raises(RuntimeError):
        service.capture_dump_payload(_BrokenEngine(), "20260101_000000_000000")
