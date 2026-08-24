"""algorithms/ 包冒烟 — 三模块直导 + re-export 对象同一性（Step 2 验收）。"""

import pytest

from algorithms import hierarchy, xpath
from algorithms.vision import ocr

pytestmark = [pytest.mark.unit, pytest.mark.device_pool]


class TestDirectImports:
    def test_xpath_functions_importable(self):
        assert callable(xpath.gen_xpath_candidates)
        assert callable(xpath.trim_hierarchy)

    def test_hierarchy_parse_importable(self):
        assert callable(hierarchy.parse_hierarchy_xml)

    def test_ocr_importable(self):
        assert callable(ocr.recognize)
        assert callable(ocr._get_engine)
        assert callable(ocr._pil_to_b64)


class TestReExportIdentity:
    def test_service_reexports_xpath(self):
        from apps.device_inspector import service

        assert service.gen_xpath_candidates is xpath.gen_xpath_candidates
        assert service.trim_hierarchy is xpath.trim_hierarchy
        assert service._simple_class is xpath._simple_class
        assert service._has_identity is xpath._has_identity
        assert service._specificity is xpath._specificity
        assert service._LAYOUT_VIEWGROUPS is xpath._LAYOUT_VIEWGROUPS

    def test_ocr_module_reexports(self):
        from apps.device_inspector import ocr as ocr_shim

        assert ocr_shim.recognize is ocr.recognize
        assert ocr_shim._get_engine is ocr._get_engine
        assert ocr_shim._pil_to_b64 is ocr._pil_to_b64


class TestParseHierarchyDirect:
    def test_parse_valid_xml(self):
        raw = (
            '<?xml version="1.0" encoding="UTF-8"?><hierarchy>'
            '<node class="android.widget.Button" text="确定" bounds="[1,2][11,22]"/>'
            "</hierarchy>"
        )
        nodes = hierarchy.parse_hierarchy_xml(raw)
        # 现状行为：根元素计入节点
        assert len(nodes) == 2
        assert nodes[1]["text"] == "确定"
        assert (nodes[1]["x"], nodes[1]["y"]) == (1, 2)
