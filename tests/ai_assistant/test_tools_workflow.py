"""工作流 AI 工具 — schema / registry / handler 单元测试。

handler 内部动态 import apps.workflow.api，测试用 monkeypatch 替换
api 函数验证参数透传与错误语义，零 DB。
"""

import pytest

from apps.ai_assistant.agent_scope import tool_registry

pytestmark = [pytest.mark.unit, pytest.mark.ai_assistant]

WF_TOOLS = {
    "list_page_flows": ("workflow", "list_page_flows"),
    "get_page_flow": ("workflow", "get_page_flow"),
}


# ── schema / registry ──


def test_workflow_category_registered():
    keys = {c["key"] for c in tool_registry.TOOL_CATEGORIES}
    assert "工作流" in keys


def test_workflow_tool_schemas_registered():
    schemas = {t["name"]: t for t in tool_registry.TOOL_SCHEMAS}
    for name, (module, action) in WF_TOOLS.items():
        s = schemas.get(name)
        assert s is not None, f"{name} 未注册"
        assert s["module"] == module
        assert s["action"] == action
        assert s["read_only"] is True
        assert s["category"] == "工作流"


def test_get_page_flow_schema_requires_doc_id():
    schemas = {t["name"]: t for t in tool_registry.TOOL_SCHEMAS}
    params = {p["name"]: p for p in schemas["get_page_flow"]["params"]}
    assert params["doc_id"]["required"] is True


def test_workflow_handlers_resolvable():
    for module, action in WF_TOOLS.values():
        assert tool_registry.resolve(module, action) is not None


# ── get_page_flow handler ──


def test_get_page_flow_handler_returns_digest(monkeypatch):
    from apps.workflow import api as wf_api

    monkeypatch.setattr(
        wf_api, "get_document_digest", lambda doc_id: (True, {"doc_id": doc_id, "nodes": []})
    )
    out = tool_registry.resolve("workflow", "get_page_flow")("7", doc_id="WF-PF-1")
    assert out == {"doc_id": "WF-PF-1", "nodes": []}


def test_get_page_flow_handler_requires_doc_id():
    with pytest.raises(ValueError, match="doc_id"):
        tool_registry.resolve("workflow", "get_page_flow")("7")


def test_get_page_flow_handler_error_raises(monkeypatch):
    from apps.workflow import api as wf_api

    monkeypatch.setattr(
        wf_api, "get_document_digest", lambda doc_id: (False, f"文档不存在: {doc_id}")
    )
    with pytest.raises(ValueError, match="文档不存在"):
        tool_registry.resolve("workflow", "get_page_flow")("7", doc_id="WF-PF-X")


# ── list_page_flows handler ──


def test_list_page_flows_handler_passes_args(monkeypatch):
    from apps.workflow import api as wf_api

    captured = {}
    monkeypatch.setattr(
        wf_api,
        "list_document_summaries",
        lambda **kw: captured.update(kw) or [{"doc_id": "WF-PF-1"}],
    )
    out = tool_registry.resolve("workflow", "list_page_flows")(
        "7", query="登录", directory_id=3, limit=5
    )
    assert out == [{"doc_id": "WF-PF-1"}]
    assert captured == {"query": "登录", "directory_id": 3, "limit": 5}


def test_list_page_flows_handler_defaults(monkeypatch):
    from apps.workflow import api as wf_api

    captured = {}
    monkeypatch.setattr(
        wf_api,
        "list_document_summaries",
        lambda **kw: captured.update(kw) or [],
    )
    out = tool_registry.resolve("workflow", "list_page_flows")("7")
    assert out == []
    assert captured == {"query": "", "directory_id": None, "limit": 20}
