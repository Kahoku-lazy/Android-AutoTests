"""workflow 原型接口：router 标准信封 + 前端消费字段守护。

页面流只剩 router 一套端点（变更 converge-workflow-http-endpoints），读写都由
EnvelopeJSONRenderer 产出 `{status, data}`。前端必须读 `data`，不能读平铺的
`prototypes` / `prototype` 键。
"""

from __future__ import annotations

import json
import pathlib
import re

import pytest

from django.contrib.auth import get_user_model
from django.test import Client

from apps.workflow.models import WorkflowPrototype
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
USE_PROTOTYPES = REPO_ROOT / "frontend/src/modules/workflow/composables/usePrototypes.ts"
PROTOTYPES_PATH = "/api/workflow/prototypes/"


@pytest.fixture
def client():
    user = get_user_model().objects.create_user(
        username="wf-envelope-owner",
        password="x",
        email="wf-envelope@example.com",
    )
    return Client(HTTP_AUTHORIZATION=f"Bearer {create_access_token(str(user.pk))}")


def test_prototype_list_envelope_is_status_and_data_array(client):
    WorkflowPrototype.objects.create(name="信封探针原型")

    resp = client.get(PROTOTYPES_PATH)
    assert resp.status_code == 200, resp.content[:200]
    body = json.loads(resp.content)
    assert body.get("status") is True
    assert "prototypes" not in body
    assert isinstance(body.get("data"), list)
    names = {item["name"] for item in body["data"]}
    assert "信封探针原型" in names


def test_use_prototypes_list_reads_envelope_data_not_prototypes():
    text = USE_PROTOTYPES.read_text(encoding="utf-8")
    match = re.search(r"async function loadPrototypes\(\) \{.*?\n  \}", text, re.DOTALL)
    assert match, "找不到 loadPrototypes"
    body = match.group(0)
    assert "data.data" in body
    assert "data.prototypes" not in body


def test_use_prototypes_create_reads_envelope_data_not_prototype():
    """创建走集合路由后同样是标准信封：读 `data.data`，不得读平铺 `data.prototype`。"""
    text = USE_PROTOTYPES.read_text(encoding="utf-8")
    match = re.search(r"async function addPrototype\(.*?\n  \}", text, re.DOTALL)
    assert match, "找不到 addPrototype"
    body = match.group(0)
    assert "data.data" in body
    assert "data.prototype" not in body
