"""灰盒·单元测试 — list_page_flows 的全量与目录层级契约（spec: ai-page-flow-listing）。

零设备、零 HTTP：只造库内数据，断言工具输出与目录树一致。
"""

import json

import pytest

from apps.ai_assistant.tools import list_page_flows
from apps.workflow.models import WorkflowDirectory, WorkflowDocument, WorkflowPrototype

pytestmark = [
    pytest.mark.unit,
    pytest.mark.django_db(transaction=True),
    pytest.mark.workflow,
    pytest.mark.ai_assistant,
]


def _make_flow(prototype, doc_id: str, title: str, directory=None) -> WorkflowDocument:
    return WorkflowDocument.objects.create(
        prototype=prototype,
        doc_id=doc_id,
        title=title,
        doc_type=WorkflowDocument.TYPE_PAGE_FLOW,
        config_json=json.dumps({"nodes": [1, 2], "links": [1]}),
        directory=directory,
    )


def test_page_flow_listing_is_full_and_carries_directory_hierarchy():
    """列全部（不被 20 条截断）；每条带完整目录路径与深度；未归类文档不丢。"""
    proto = WorkflowPrototype.objects.create(name="层级原型")
    root = WorkflowDirectory.objects.create(prototype=proto, name="默认目录")
    child = WorkflowDirectory.objects.create(prototype=proto, name="详情页", parent=root)
    deep = WorkflowDirectory.objects.create(prototype=proto, name="深一层", parent=child)

    _make_flow(proto, "DOC-DEEP", "深层文档", deep)
    _make_flow(proto, "DOC-ROOT", "根层文档", root)
    _make_flow(proto, "DOC-ORPHAN", "未归类文档", None)
    for i in range(22):
        _make_flow(proto, f"DOC-BULK-{i:02d}", f"批量文档{i}", root)

    payload = json.loads(list_page_flows())
    documents = {d["doc_id"]: d for d in payload["documents"]}

    assert payload["total"] == 25
    assert len(documents) == 25

    assert documents["DOC-DEEP"]["directory_path"] == "默认目录/详情页/深一层"
    assert documents["DOC-DEEP"]["directory_depth"] == 3
    assert documents["DOC-ROOT"]["directory_path"] == "默认目录"
    assert documents["DOC-ROOT"]["directory_depth"] == 1

    orphan = documents["DOC-ORPHAN"]
    assert orphan["directory_id"] is None
    assert orphan["directory_path"] == ""
    assert orphan["directory_depth"] == 0


def test_page_flow_listing_narrows_by_query():
    """query 非空时按标题/文档 ID 收窄；不传为全量。"""
    proto = WorkflowPrototype.objects.create(name="收窄原型")
    _make_flow(proto, "DOC-ALPHA", "登录页流程", None)
    _make_flow(proto, "DOC-BETA", "设置页流程", None)

    assert json.loads(list_page_flows())["total"] == 2

    narrowed = json.loads(list_page_flows(query="登录"))
    assert narrowed["total"] == 1
    assert narrowed["documents"][0]["doc_id"] == "DOC-ALPHA"
