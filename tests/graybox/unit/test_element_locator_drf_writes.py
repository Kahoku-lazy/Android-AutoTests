"""element_locator DRF 写路径：契约兑现 + 写库收敛。

修复前两个问题：
- `WebPageFlowSerializer` 的 `from_group_id` / `to_group_id` / `trigger_element_id` **全是只读**
  （DRF 把 FK 的 `*_id` attname 建成 `ReadOnlyField`）→ `POST /web-flows/` 缺 `from_group` → NOT NULL → **500**；
  同函数的「源/目标不能是目录」校验取 `validated_data.get("from_group")` 恒为 None → 死代码。
- `WebElementViewSet.perform_update` / `WebPageFlowViewSet.perform_create` 用 `serializer.save()` 直写库 → 越过 api.py。
"""

from __future__ import annotations

import inspect
import json

import pytest

from django.contrib.auth import get_user_model
from django.test import Client

from apps.element_locator import api as el_api
from apps.element_locator import views_drf
from apps.element_locator.models import WebElement, WebGroup, WebPageFlow
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


@pytest.fixture
def client():
    user = get_user_model().objects.create_user(
        username="el-drf-writes", password="x", email="el-drf-writes@example.com"
    )
    return Client(HTTP_AUTHORIZATION=f"Bearer {create_access_token(str(user.pk))}")


def _post(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def test_web_flow_create_persists(client):
    """修复前必现 500（字段只读 → validated_data 只有 trigger_action）。"""
    a = WebGroup.objects.create(name="源页")
    b = WebGroup.objects.create(name="目标页")

    resp = _post(client, "/api/elements/web-flows/", {"from_group_id": a.id, "to_group_id": b.id})

    assert resp.status_code == 201, resp.content[:300]
    flow = WebPageFlow.objects.get(from_group=a, to_group=b)
    assert flow.trigger_action == "click"
    assert resp.json()["data"]["from_group_id"] == a.id


def test_web_flow_create_rejects_folder_endpoint(client):
    """目录判定现在是可达校验（修复前是死代码）。"""
    folder = WebGroup.objects.create(name="目录", is_folder=True)
    page = WebGroup.objects.create(name="页面")

    resp = _post(
        client, "/api/elements/web-flows/", {"from_group_id": folder.id, "to_group_id": page.id}
    )

    assert resp.status_code == 400, resp.content[:300]
    assert WebPageFlow.objects.count() == 0


def test_web_flow_create_goes_through_api(client, monkeypatch):
    calls = []
    real = el_api.create_web_page_flow

    def spy(*args, **kwargs):
        calls.append((args, kwargs))
        return real(*args, **kwargs)

    monkeypatch.setattr(el_api, "create_web_page_flow", spy)
    a = WebGroup.objects.create(name="A")
    b = WebGroup.objects.create(name="B")

    resp = _post(client, "/api/elements/web-flows/", {"from_group_id": a.id, "to_group_id": b.id})

    assert resp.status_code == 201, resp.content[:300]
    assert calls, "view 未调用 api.create_web_page_flow"


def test_web_element_update_goes_through_api(client, monkeypatch):
    el = WebElement.objects.create(name="el1", locator_type="css_selector", locator_value=".a")
    calls = []
    real = el_api.update_web_element

    def spy(el_id, updates):
        calls.append((el_id, updates))
        return real(el_id, updates)

    monkeypatch.setattr(el_api, "update_web_element", spy)

    resp = client.patch(
        f"/api/elements/web/{el.id}/",
        data=json.dumps({"name": "el1-renamed"}),
        content_type="application/json",
    )

    assert resp.status_code == 200, resp.content[:300]
    assert calls and calls[0][0] == el.id
    el.refresh_from_db()
    assert el.name == "el1-renamed"


def test_drf_views_have_no_serializer_save():
    """收敛断言：DRF 视图不得再出现 `serializer.save()`。"""
    assert "serializer.save()" not in inspect.getsource(views_drf)
