"""workflow 目录 router 路径的契约：parent_id 语义 + 单写路径（API-工作流.md §3.4）。

修复前：`WorkflowDirectorySerializer.parent_id` 是只读字段，带 `parent_id` 的 PATCH
返回 200 却静默忽略移动；同时 `name` / `sort_order` 由 `serializer.save()` 直写库，
越过 `apps/workflow/api.py`。

覆盖三件事：
1. 失败路径（跨原型移动 + 改名 + 排序）→ 4xx 且**零落库**；
2. 成功路径（同原型换父 + 改名 + 排序）→ 三者都落库；
3. 显式 `parent_id: null` → 移到根；缺省 → 不动父级。
"""

from __future__ import annotations

import json

import pytest

from django.contrib.auth import get_user_model
from django.test import Client

from apps.workflow.models import WorkflowDirectory, WorkflowPrototype
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit]

# 基址：派生路径形如 f"{DIRECTORIES_PATH}/{id}/"，故此处不带尾斜杠
DIRECTORIES_PATH = "/api/workflow/directories"


@pytest.fixture
def client():
    """带真实 JWT 的测试客户端 —— DRF 鉴权要能从 sub 取到 auth.User。"""
    user = get_user_model().objects.create_user(
        username="wf-directory-owner",
        password="x",
        email="wf-directory@example.com",
    )
    return Client(HTTP_AUTHORIZATION=f"Bearer {create_access_token(str(user.pk))}")


def _patch_directory(client, dir_id: int, payload: dict):
    return client.patch(
        f"{DIRECTORIES_PATH}/{dir_id}/",
        data=json.dumps(payload),
        content_type="application/json",
    )


def test_cross_prototype_move_leaves_name_and_sort_order_untouched(client):
    """失败路径：跨原型移动必须 4xx，且同一请求里的改名 / 排序零落库。"""
    proto_a = WorkflowPrototype.objects.create(name="原型 A")
    proto_b = WorkflowPrototype.objects.create(name="原型 B")
    directory = WorkflowDirectory.objects.create(prototype=proto_a, name="原目录", sort_order=1)
    foreign_parent = WorkflowDirectory.objects.create(prototype=proto_b, name="B 的目录")

    resp = _patch_directory(
        client,
        directory.id,
        {"name": "被改名", "sort_order": 9, "parent_id": foreign_parent.id},
    )

    assert resp.status_code == 400, resp.content[:200]
    directory.refresh_from_db()
    assert directory.name == "原目录"
    assert directory.sort_order == 1
    assert directory.parent_id is None


def test_same_prototype_update_persists_name_sort_order_and_parent(client):
    """成功路径：同原型换父 + 改名 + 排序，三者都必须落库并回显。"""
    proto = WorkflowPrototype.objects.create(name="原型 A")
    target_parent = WorkflowDirectory.objects.create(prototype=proto, name="目标父目录")
    directory = WorkflowDirectory.objects.create(prototype=proto, name="原目录")

    resp = _patch_directory(
        client,
        directory.id,
        {"name": "新目录", "sort_order": 7, "parent_id": target_parent.id},
    )

    assert resp.status_code == 200, resp.content[:200]
    directory.refresh_from_db()
    assert directory.name == "新目录"
    assert directory.sort_order == 7
    assert directory.parent_id == target_parent.id
    assert resp.json()["data"]["parent_id"] == target_parent.id


def test_explicit_null_parent_moves_directory_to_root(client):
    """文档 §3.4：显式 parent_id=null 表示移到根。"""
    proto = WorkflowPrototype.objects.create(name="原型 A")
    parent = WorkflowDirectory.objects.create(prototype=proto, name="父目录")
    child = WorkflowDirectory.objects.create(prototype=proto, name="子目录", parent=parent)

    resp = _patch_directory(client, child.id, {"parent_id": None})

    assert resp.status_code == 200, resp.content[:200]
    child.refresh_from_db()
    assert child.parent_id is None


def test_update_without_parent_id_keeps_parent(client):
    """回归：PATCH 未带 parent_id 时不得改动父级。"""
    proto = WorkflowPrototype.objects.create(name="原型 A")
    parent = WorkflowDirectory.objects.create(prototype=proto, name="父目录")
    child = WorkflowDirectory.objects.create(prototype=proto, name="子目录", parent=parent)

    resp = _patch_directory(client, child.id, {"name": "改名不改父"})

    assert resp.status_code == 200, resp.content[:200]
    child.refresh_from_db()
    assert child.name == "改名不改父"
    assert child.parent_id == parent.id
