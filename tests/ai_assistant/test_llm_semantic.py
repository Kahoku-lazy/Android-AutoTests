"""llm_semantic — 语义提交校验单测（纯函数，无 LLM）。"""

import pytest

from apps.ai_assistant.agent_scope.llm_semantic import validate_semantic

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]


def _el(resource_id, **kw):
    base = {"resource_id": resource_id}
    base.update(kw)
    return base


class TestValidateSemantic:
    def test_normal(self):
        inputs = [_el("a:b/ivSwitch"), _el("a:b/tvName")]
        semantic = {
            "page_summary": "设备首页",
            "elements": [
                {"resource_id": "a:b/ivSwitch", "func_name": "开关", "metrics": ["可点击"]},
                {"resource_id": "a:b/tvName", "func_name": "设备名", "metrics": []},
            ],
        }
        result = validate_semantic(semantic, inputs)
        assert result["page_summary"] == "设备首页"
        assert result["elements"][0]["func_name"] == "开关"
        assert result["elements"][0]["metrics"] == ["可点击"]

    def test_hallucinated_rid_cleared(self):
        inputs = [_el("a:b/ivSwitch")]
        semantic = {
            "page_summary": "",
            "elements": [
                {"resource_id": "a:b/ivSwitch", "func_name": "开关", "metrics": []},
                {"resource_id": "a:b/btnLogin", "func_name": "登录按钮", "metrics": []},
            ],
        }
        result = validate_semantic(semantic, inputs)
        by_rid = {e["resource_id"]: e["func_name"] for e in result["elements"]}
        assert by_rid["a:b/ivSwitch"] == "开关"
        assert by_rid["a:b/btnLogin"] == ""  # 幻觉 rid 被置空

    def test_invalid_metrics_dropped(self):
        inputs = [_el("a:b/ivSwitch")]
        semantic = {
            "elements": [
                {
                    "resource_id": "a:b/ivSwitch",
                    "func_name": "开关",
                    "metrics": ["可点击", "可编辑", "可滚动"],
                },
            ]
        }
        result = validate_semantic(semantic, inputs)
        assert result["elements"][0]["metrics"] == ["可点击", "可滚动"]  # 非法"可编辑"被剔除

    def test_missing_fields_default(self):
        inputs = [_el("a:b/tvName")]
        result = validate_semantic(None, inputs)
        assert result["page_summary"] == ""
        assert result["sections"] == []
        assert result["elements"] == []
        assert result["cards"] == []


class TestSaveSemanticHandler:
    def _fake_data(self):
        return {
            "package": "com.govee.home",
            "activity": ".MainTabActivity",
            "elements": [
                {
                    "resource_id": "a:b/ivSwitch",
                    "class_name": "android.widget.ImageView",
                    "clickable": True,
                },
                {"resource_id": "a:b/tvName", "class_name": "android.widget.TextView"},
            ],
        }

    def test_valid_semantic_merged(self, monkeypatch):
        from apps.ai_assistant.agent_scope import tool_registry
        from apps.device_inspector import api as di_api

        monkeypatch.setattr(di_api, "analyze_snapshot", lambda sid: self._fake_data())
        handler = tool_registry.resolve("inspector", "save_semantic")
        result = handler(
            "1",
            snapshot_id=1,
            page_summary="设备页",
            elements=[{"resource_id": "a:b/ivSwitch", "func_name": "开关", "metrics": ["可点击"]}],
            cards=[],
        )
        assert result["page_summary"] == "设备页"
        assert result["elements"][0]["func_name"] == "开关"
        assert "func_name" not in result["elements"][1]  # 未提交的元素不背命名

    def test_hallucinated_rid_not_merged(self, monkeypatch):
        from apps.ai_assistant.agent_scope import tool_registry
        from apps.device_inspector import api as di_api

        monkeypatch.setattr(di_api, "analyze_snapshot", lambda sid: self._fake_data())
        handler = tool_registry.resolve("inspector", "save_semantic")
        result = handler(
            "1",
            snapshot_id=1,
            elements=[{"resource_id": "a:b/btnLogin", "func_name": "登录按钮", "metrics": []}],
        )
        # 幻觉 rid 不在快照元素里，不产生任何 func_name 回填
        assert all("func_name" not in el for el in result["elements"])

    def test_missing_snapshot_raises(self, monkeypatch):
        from apps.ai_assistant.agent_scope import tool_registry
        from apps.device_inspector import api as di_api

        monkeypatch.setattr(di_api, "analyze_snapshot", lambda sid: None)
        handler = tool_registry.resolve("inspector", "save_semantic")
        with pytest.raises(ValueError):
            handler("1", snapshot_id=999, elements=[])
