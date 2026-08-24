"""engines 契约单元测试 — Node/EngineCapabilities/UiEngine（Step 3a 验收）。"""

import pytest

from engines.base import EngineCapabilities
from models.ui_nodes import Node

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


class TestNode:
    def test_default_xpaths_empty(self):
        n = Node(
            depth=0,
            class_name="android.widget.Button",
            text="",
            content_desc="",
            resource_id="",
            package="",
            index="",
            bounds="[0,0][1,1]",
            x=0,
            y=0,
            width=1,
            height=1,
            clickable=False,
            enabled=False,
            scrollable=False,
            checkable=False,
            checked=False,
            focusable=False,
            long_clickable=False,
        )
        assert n.xpaths == []

    def test_xpaths_filled_by_caller(self):
        n = Node(
            depth=1,
            class_name="",
            text="",
            content_desc="",
            resource_id="",
            package="",
            index="",
            bounds="",
            x=0,
            y=0,
            width=0,
            height=0,
            clickable=False,
            enabled=False,
            scrollable=False,
            checkable=False,
            checked=False,
            focusable=False,
            long_clickable=False,
            xpaths=["//android.widget.Button[@text='确定']"],
        )
        assert n.xpaths == ["//android.widget.Button[@text='确定']"]


class TestEngineCapabilities:
    def test_defaults_all_false(self):
        caps = EngineCapabilities()
        assert caps.xpath_locate is False
        assert caps.toast_wait is False
        assert caps.ocr is False

    def test_partial_overrides(self):
        caps = EngineCapabilities(xpath_locate=True)
        assert caps.xpath_locate is True
        assert caps.toast_wait is False
