"""灰盒·单元测试 — 引擎层级取数契约（engine-protocol「感知标准化」）。

零外部依赖、不连设备，断言四件事：
1. 协议只声明「返回原始 XML 文本」的层级取数方法，不再声明返回 Node 列表的方法；
2. 引擎实现不 import 算法层（解析不属引擎职责）；
3. 成功时返回原始 XML，且该 XML 可被算法层解析为预期节点（取数与解析分家后口径不变）；
4. 全部策略失败时抛错，MUST NOT 返回空串等假数据。
"""

import inspect

from pathlib import Path

import pytest

from algorithms.hierarchy import parse_hierarchy_xml
from engines.device.android.u2 import U2Engine
from engines.device.base import UiEngine

FIXTURE_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<hierarchy rotation="0">\n'
    '  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.demo"'
    ' content-desc="" checkable="false" checked="false" clickable="false" enabled="true" focusable="false"'
    ' focused="false" scrollable="false" long-clickable="false" password="false" selected="false"'
    ' visible-to-user="true" bounds="[0,0][1080,2340]" drawing-order="0" hint="" display-id="0">\n'
    '    <node index="0" text="设备" resource-id="com.demo:id/tvTitle" class="android.widget.TextView"'
    ' package="com.demo" content-desc="" checkable="false" checked="false" clickable="false" enabled="true"'
    ' focusable="false" focused="false" scrollable="false" long-clickable="false" password="false"'
    ' selected="false" visible-to-user="true" bounds="[58,59][156,217]" drawing-order="1" hint="" display-id="0"/>\n'
    "  </node>\n"
    "</hierarchy>\n"
)


class _FakeU2:
    """最小 u2 替身：只实现层级取数，用于验证引擎不再解析。"""

    def __init__(self, payload=None, error=None):
        self.payload = payload
        self.error = error

    def dump_hierarchy(self, **kwargs):
        if self.error is not None:
            raise self.error
        return self.payload


class _FallbackU2:
    """第一次返回空、第二次返回 XML，用于验证三层 fallback 不返回假数据。"""

    def __init__(self):
        self.calls = []

    def dump_hierarchy(self, **kwargs):
        self.calls.append(kwargs)
        return b"" if len(self.calls) == 1 else FIXTURE_XML


@pytest.mark.unit
@pytest.mark.device_pool
def test_protocol_declares_raw_xml_only():
    """协议只声明返回原始 XML 的层级取数方法，不再声明返回 Node 列表的方法。"""
    assert hasattr(UiEngine, "dump_hierarchy_xml")
    assert not hasattr(UiEngine, "dump_hierarchy")
    assert inspect.signature(UiEngine.dump_hierarchy_xml).return_annotation is str


@pytest.mark.unit
@pytest.mark.device_pool
def test_engine_impl_does_not_import_algorithms():
    """引擎实现不得 import 算法层（只扫 import 语句，注释里提到算法层不算违规）。"""
    src = Path("engines/device/android/u2.py").read_text(encoding="utf-8")
    offenders = [
        line.strip()
        for line in src.splitlines()
        if line.strip().startswith(("from algorithms", "import algorithms"))
    ]
    assert offenders == []


@pytest.mark.unit
@pytest.mark.device_pool
def test_dump_returns_raw_xml_parsed_by_algorithm_layer():
    """取数返回原始 XML；经算法层解析得到的节点与既有口径一致。"""
    engine = U2Engine()
    engine._u2 = _FakeU2(payload=FIXTURE_XML)

    raw = engine.dump_hierarchy_xml()
    assert raw == FIXTURE_XML

    nodes = parse_hierarchy_xml(raw)
    assert len(nodes) == 3  # hierarchy 根 + FrameLayout + 标题节点
    title = nodes[2]
    assert title["class_name"] == "android.widget.TextView"
    assert title["resource_id"] == "com.demo:id/tvTitle"
    assert title["text"] == "设备"
    assert title["bounds"] == "[58,59][156,217]"
    assert (title["x"], title["y"], title["width"], title["height"]) == (58, 59, 98, 158)


@pytest.mark.unit
@pytest.mark.device_pool
def test_dump_falls_back_and_never_returns_falsy():
    """第一层策略返回空时继续退让，最终返回可用 XML（不返回空串）。"""
    engine = U2Engine()
    fake = _FallbackU2()
    engine._u2 = fake

    assert engine.dump_hierarchy_xml() == FIXTURE_XML
    assert len(fake.calls) == 2


@pytest.mark.unit
@pytest.mark.device_pool
def test_dump_raises_when_all_strategies_fail():
    """全部策略失败时抛错，MUST NOT 返回空串等假数据。"""
    engine = U2Engine()
    engine._u2 = _FakeU2(error=RuntimeError("device frozen"))

    with pytest.raises(RuntimeError):
        engine.dump_hierarchy_xml()
