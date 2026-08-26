"""build_page_flow_document / get_or_create_flow 集成测试（真实 DB）。"""

import pytest

from apps.element_locator import api as el_api
from apps.workflow import api as wf_api

pytestmark = [pytest.mark.integration, pytest.mark.django_db]


@pytest.fixture
def _pages():
    from apps.element_locator.models import Element, Page

    p1 = Page.objects.create(label="首页", is_folder=False, package="com.govee.home")
    el = Element.objects.create(
        page=p1, resource_id="com.govee.home:id/ivTabDevice", bounds="[0,0][10,10]"
    )
    p2 = Page.objects.create(label="设备详情", is_folder=False)
    return {"home": p1, "detail": p2, "el": el}


def test_get_or_create_flow_idempotent(_pages):
    from apps.element_locator.models import PageFlow

    flow, created = el_api.get_or_create_flow(
        _pages["home"].id, _pages["detail"].id, _pages["el"].id
    )
    assert created is True
    flow2, created2 = el_api.get_or_create_flow(
        _pages["home"].id, _pages["detail"].id, _pages["el"].id
    )
    assert created2 is False
    assert flow2.id == flow.id
    assert PageFlow.objects.count() == 1


def test_build_page_flow_document_writes_doc(_pages):
    from apps.workflow.models import WorkflowDocument

    ok, payload, _ = wf_api.build_page_flow_document(
        title="测试页面流",
        start_package="com.govee.home",
        pages=[
            {
                "page_id": _pages["home"].id,
                "label": "首页",
                "elements": [
                    {
                        "element_id": _pages["el"].id,
                        "alias": "设备Tab",
                        "type": "button",
                        "xpath": "//x",
                    }
                ],
            },
            {"page_id": _pages["detail"].id, "label": "设备详情", "elements": []},
        ],
        edges=[
            {
                "from_page_id": _pages["home"].id,
                "to_page_id": _pages["detail"].id,
                "trigger_element_id": _pages["el"].id,
            }
        ],
    )
    assert ok is True
    doc = WorkflowDocument.objects.get(doc_id=payload["doc_id"])
    assert doc.doc_type == "page_flow"
    assert '"nodes"' in doc.config_json and '"links"' in doc.config_json
