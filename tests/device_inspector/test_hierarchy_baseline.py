"""Step 0 基线（Step 4 显式更新）— dump_hierarchy 解析现状锚定（经 pool→session→FakeEngine 链）。

断言语义与原基线一致（同一行为、mock 注入点迁移到引擎工厂）。
"""

import pytest

from apps.device_pool.pool import DevicePool
from tests.device_pool.fakes import clear_sessions, install_fake_engine

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]

SAMPLE_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>'
    "<hierarchy>"
    '<node class="android.widget.Button" text="确定" content-desc="OK" '
    'resource-id="com.app:id/btn" package="com.app" index="0" '
    'bounds="[10,20][110,80]" clickable="true" enabled="true" scrollable="false" '
    'checkable="false" checked="false" focusable="false" long-clickable="false">'
    '<node class="android.widget.TextView" text="子文本" bounds="[0,0][5,5]"/>'
    "</node>"
    "</hierarchy>"
)


@pytest.fixture
def pool(monkeypatch):
    clear_sessions()
    p = DevicePool()
    p.current_serial = "fake-serial"
    return p


class TestDumpHierarchy:
    def test_parses_nodes_and_bounds(self, pool, monkeypatch):
        engine = install_fake_engine(monkeypatch)
        engine._dump_results = [SAMPLE_XML]

        nodes = pool.dump_hierarchy()

        # 现状行为：根元素 <hierarchy> 自身也被 walk 为 depth=0 的空节点
        assert len(nodes) == 3
        n = nodes[1]
        assert n["class_name"] == "android.widget.Button"
        assert n["text"] == "确定"
        assert n["content_desc"] == "OK"
        assert n["resource_id"] == "com.app:id/btn"
        assert n["package"] == "com.app"
        assert n["index"] == "0"
        assert n["bounds"] == "[10,20][110,80]"
        assert (n["x"], n["y"]) == (10, 20)
        assert (n["width"], n["height"]) == (100, 60)
        assert n["clickable"] is True
        assert n["enabled"] is True
        assert n["scrollable"] is False
        assert "xpaths" not in n  # 兼容转换：空 xpaths 丢弃，inspector 契约不变
        child = nodes[2]
        assert child["text"] == "子文本"
        assert child["depth"] == 2

    def test_fallback_then_success(self, pool, monkeypatch):
        engine = install_fake_engine(monkeypatch)
        engine._dump_results = [RuntimeError("dump failed"), SAMPLE_XML]

        nodes = pool.dump_hierarchy()

        assert len(nodes) == 3

    def test_all_strategies_fail_raises(self, pool, monkeypatch):
        engine = install_fake_engine(monkeypatch)
        engine._dump_results = [RuntimeError("a"), RuntimeError("b")]

        with pytest.raises(RuntimeError, match="all strategies failed"):
            pool.dump_hierarchy()

    def test_missing_xml_prefix_prepended(self, pool, monkeypatch):
        no_prefix = SAMPLE_XML.split("?>", 1)[1]
        engine = install_fake_engine(monkeypatch)
        engine._dump_results = [no_prefix]

        nodes = pool.dump_hierarchy()

        assert len(nodes) == 3
        assert nodes[1]["class_name"] == "android.widget.Button"

    def test_truncated_xml_repaired(self, pool, monkeypatch):
        # 现状行为：完整文档带尾部垃圾 → rfind 截到最后一个 ">"（即 </hierarchy>）后解析成功
        engine = install_fake_engine(monkeypatch)
        engine._dump_results = [SAMPLE_XML + "TRUNCATED-GARBAGE"]

        nodes = pool.dump_hierarchy()

        assert len(nodes) == 3
        assert nodes[1]["text"] == "确定"

    def test_mid_node_truncation_cannot_repair(self, pool, monkeypatch):
        # 现状行为：节点中段截断 → 修复后 hierarchy 仍未闭合 → RuntimeError
        truncated = (
            '<?xml version="1.0" encoding="UTF-8"?><hierarchy>'
            '<node class="android.widget.TextView" text="完整" bounds="[0,0][1,1]"/>'
            '<node class="android.widget.Button" text="被截断"'
        )
        engine = install_fake_engine(monkeypatch)
        engine._dump_results = [truncated]

        with pytest.raises(RuntimeError, match="cannot repair"):
            pool.dump_hierarchy()

    def test_unrepairable_xml_raises(self, pool, monkeypatch):
        broken = '<?xml version="1.0" encoding="UTF-8"?><hierarchy><node'
        engine = install_fake_engine(monkeypatch)
        engine._dump_results = [broken]

        with pytest.raises(RuntimeError, match="cannot repair"):
            pool.dump_hierarchy()
