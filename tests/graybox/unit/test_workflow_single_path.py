"""workflow 写接口收敛契约：只有 router 一套路由、一套信封（变更 converge-workflow-http-endpoints）。

覆盖四件事：

1. 旧平铺写地址已下线 —— `*/create/` 不再由第二套实现应答，也不再出现非数字主键导致的 500；
2. 创建 / 导入走集合与动作路由，返回标准信封 `{status, data}`；
3. 文档 `directory_id` 在创建与更新时真的生效（DRF 默认把 FK 的 attname 当只读，曾静默丢弃）；
4. 更新按提交字段合并 —— 没提交的字段保持原值（曾出现「只改标题被 400」与「保存时描述被清空」）。

规格：`openspec/specs/workflow-http-envelope`。
"""

from __future__ import annotations

import json
import pathlib

import pytest

from django.contrib.auth import get_user_model
from django.test import Client

from apps.workflow.models import WorkflowDocument, WorkflowPrototype
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
API_TS = REPO_ROOT / "frontend/src/modules/workflow/api.ts"
USE_PROTOTYPES_TS = REPO_ROOT / "frontend/src/modules/workflow/composables/usePrototypes.ts"
LIBRARY_STORE_TS = REPO_ROOT / "frontend/src/modules/workflow/stores/libraryStore.ts"

LEGACY_CREATE_PATHS = (
    "/api/workflow/prototypes/create/",
    "/api/workflow/directories/create/",
    "/api/workflow/documents/create/",
)

CONFIG = {
    "name": "契约页面流",
    "version": "1.0",
    "nodes": [{"id": "n1", "type": "page", "properties": {"page": "首页"}}],
    "links": [],
}


@pytest.fixture
def client():
    user = get_user_model().objects.create_user(
        username="wf-single-path",
        password="x",
        email="wf-single-path@example.com",
    )
    return Client(HTTP_AUTHORIZATION="Bearer " + create_access_token(str(user.pk)))


def _json(resp) -> dict:
    return json.loads(resp.content)


def _post(client, path: str, payload: dict):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


def _put(client, path: str, payload: dict):
    return client.put(path, data=json.dumps(payload), content_type="application/json")


def _make_prototype(client, name: str = "契约原型") -> dict:
    resp = _post(client, "/api/workflow/prototypes/", {"name": name})
    assert resp.status_code == 201, resp.content[:200]
    body = _json(resp)
    assert body["status"] is True
    return body["data"]


def _make_directory(client, prototype_id: int, name: str = "契约目录") -> dict:
    resp = _post(client, "/api/workflow/directories/", {"name": name, "prototype_id": prototype_id})
    assert resp.status_code == 201, resp.content[:200]
    return _json(resp)["data"]


def _make_document(
    client, prototype_id: int, *, directory_id=None, description="原描述", config=None
):
    resp = _post(
        client,
        "/api/workflow/documents/",
        {
            "title": "契约文档",
            "doc_type": "page_flow",
            "prototype_id": prototype_id,
            "directory_id": directory_id,
            "description": description,
            "config": CONFIG if config is None else config,
        },
    )
    assert resp.status_code == 201, resp.content[:200]
    return _json(resp)["data"]


# ── 1. 旧地址下线 ──


def test_legacy_create_paths_answer_nothing(client):
    """旧平铺写地址不再有实现应答：4xx、且库中不产生任何资源。"""
    before = WorkflowPrototype.objects.count()
    for path in LEGACY_CREATE_PATHS:
        resp = _post(client, path, {"name": "不该被建出来", "title": "不该被建出来"})
        assert resp.status_code in (404, 405), f"{path} → {resp.status_code} {resp.content[:120]}"
    assert WorkflowPrototype.objects.count() == before
    assert WorkflowDocument.objects.count() == 0


def test_literal_segment_is_not_treated_as_primary_key(client):
    """主键只匹配数字：字面量段不再被详情路由吃掉，也不因非数字主键抛 500。"""
    assert client.get("/api/workflow/prototypes/create/").status_code == 404
    assert client.get("/api/workflow/directories/create/").status_code == 404


# ── 2. 集合 / 动作路由 + 标准信封 ──


def test_prototype_create_returns_standard_envelope(client):
    proto = _make_prototype(client, "信封原型")
    assert proto["name"] == "信封原型"
    assert proto["doc_count"] == 0


def test_directory_and_document_create_return_standard_envelope(client):
    proto = _make_prototype(client)
    directory = _make_directory(client, proto["id"])
    assert directory["prototype_id"] == proto["id"]

    doc = _make_document(client, proto["id"])
    assert doc["doc_id"].startswith("WF-PF-") or doc["doc_id"]
    assert doc["config"] == CONFIG


def test_import_uses_router_action_route(client):
    proto = _make_prototype(client)
    resp = _post(
        client,
        "/api/workflow/documents/import/",
        {
            "doc_id": "IMP-CONTRACT-1",
            "title": "导入文档",
            "doc_type": "page_flow",
            "prototype_id": proto["id"],
            "config": CONFIG,
        },
    )
    assert resp.status_code in (200, 201), resp.content[:200]
    body = _json(resp)
    assert body["status"] is True
    assert body["data"]["doc_id"] == "IMP-CONTRACT-1"
    assert WorkflowDocument.objects.filter(doc_id="IMP-CONTRACT-1").exists()


def test_invalid_doc_type_is_rejected_without_write(client):
    proto = _make_prototype(client)
    before = WorkflowDocument.objects.count()
    resp = _post(
        client,
        "/api/workflow/documents/",
        {"title": "非法类型", "doc_type": "not_supported", "prototype_id": proto["id"]},
    )
    assert resp.status_code == 400, resp.content[:200]
    assert WorkflowDocument.objects.count() == before


# ── 3. 目录归属真的生效 ──


def test_create_honours_directory_id(client):
    """回归：directory_id 曾是序列化器只读字段，创建时被静默丢弃。"""
    proto = _make_prototype(client)
    directory = _make_directory(client, proto["id"])
    doc = _make_document(client, proto["id"], directory_id=directory["id"])
    assert doc["directory_id"] == directory["id"]
    assert WorkflowDocument.objects.get(doc_id=doc["doc_id"]).directory_id == directory["id"]


def test_update_can_change_and_clear_directory(client):
    proto = _make_prototype(client)
    first = _make_directory(client, proto["id"], "目录一")
    second = _make_directory(client, proto["id"], "目录二")
    doc = _make_document(client, proto["id"], directory_id=first["id"])
    path = f"/api/workflow/documents/{doc['doc_id']}/"

    resp = _put(
        client, path, {"title": "契约文档", "doc_type": "page_flow", "directory_id": second["id"]}
    )
    assert resp.status_code == 200, resp.content[:200]
    assert _json(resp)["data"]["directory_id"] == second["id"]

    resp = _put(client, path, {"title": "契约文档", "doc_type": "page_flow", "directory_id": None})
    assert resp.status_code == 200, resp.content[:200]
    assert _json(resp)["data"]["directory_id"] is None


def test_update_without_directory_id_keeps_it(client):
    proto = _make_prototype(client)
    directory = _make_directory(client, proto["id"])
    doc = _make_document(client, proto["id"], directory_id=directory["id"])
    resp = _put(
        client,
        f"/api/workflow/documents/{doc['doc_id']}/",
        {"title": "改标题不改归属", "doc_type": "page_flow"},
    )
    assert resp.status_code == 200, resp.content[:200]
    assert WorkflowDocument.objects.get(doc_id=doc["doc_id"]).directory_id == directory["id"]


def test_cross_prototype_directory_rejected_without_write(client):
    proto_a = _make_prototype(client, "原型 A")
    proto_b = _make_prototype(client, "原型 B")
    home = _make_directory(client, proto_a["id"], "A 的目录")
    foreign = _make_directory(client, proto_b["id"], "B 的目录")
    doc = _make_document(client, proto_a["id"], directory_id=home["id"])

    resp = _put(
        client,
        f"/api/workflow/documents/{doc['doc_id']}/",
        {"title": "被改名", "doc_type": "page_flow", "directory_id": foreign["id"]},
    )
    assert resp.status_code == 400, resp.content[:200]
    saved = WorkflowDocument.objects.get(doc_id=doc["doc_id"])
    assert saved.title == "契约文档"
    assert saved.directory_id == home["id"]


# ── 4. 更新按提交字段合并 ──


def test_partial_update_keeps_omitted_fields(client):
    """回归：只提交标题曾因 config 必填被 400；提交 config 未提交描述曾把描述清空。"""
    proto = _make_prototype(client)
    directory = _make_directory(client, proto["id"])
    doc = _make_document(client, proto["id"], directory_id=directory["id"])
    path = f"/api/workflow/documents/{doc['doc_id']}/"

    # 只改标题（界面「重命名页面流」的 payload）——必须成功
    resp = _put(client, path, {"title": "重命名后", "doc_type": "page_flow"})
    assert resp.status_code == 200, resp.content[:200]
    saved = WorkflowDocument.objects.get(doc_id=doc["doc_id"])
    assert saved.title == "重命名后"
    assert json.loads(saved.config_json) == CONFIG, "未提交 config 时画布内容被改写了"
    assert saved.description == "原描述", "未提交 description 时描述被清空了"
    assert saved.directory_id == directory["id"]

    # 提交画布内容、不提交描述（界面「保存」的 payload）——描述必须保住
    resp = _put(
        client,
        path,
        {
            "title": "重命名后",
            "doc_type": "page_flow",
            "directory_id": directory["id"],
            "config": CONFIG,
        },
    )
    assert resp.status_code == 200, resp.content[:200]
    saved.refresh_from_db()
    assert saved.description == "原描述", "保存画布时描述被清空了"
    assert json.loads(saved.config_json) == CONFIG


# ── 前端调用面 ──


def test_frontend_api_layer_has_no_legacy_create_paths():
    text = API_TS.read_text(encoding="utf-8")
    assert "/create/" not in text, "前端页面流 API 层仍残留旧平铺写地址"
    assert "'/workflow/prototypes/'" in text
    assert "'/workflow/directories/'" in text
    assert "'/workflow/documents/'" in text
    assert "'/workflow/documents/import/'" in text


def test_frontend_reads_standard_envelope_only():
    """创建 / 导入的读取点必须读信封 data，不得再读平铺的 prototype / directory / document 键。"""
    library = LIBRARY_STORE_TS.read_text(encoding="utf-8")
    prototypes = USE_PROTOTYPES_TS.read_text(encoding="utf-8")
    for name, text in (("libraryStore.ts", library), ("usePrototypes.ts", prototypes)):
        for flat_key in ("res.data.document", "res.data.directory", "res.data.prototype"):
            assert flat_key not in text, f"{name} 仍按平铺键读取：{flat_key}"
        assert "data.prototype" not in text, f"{name} 仍按平铺键读取：data.prototype"
    assert library.count("res.data.data") >= 5, "libraryStore 的信封读取点少于预期，可能漏改"
