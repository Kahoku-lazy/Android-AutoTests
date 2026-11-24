from __future__ import annotations

import json

import pytest

from django.contrib.auth import get_user_model
from django.test import RequestFactory
from django.urls import Resolver404, resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.knowledge_search import retrieval
from backend.apps.knowledge_search.views import (
    KnowledgeModuleDetailAPIView,
    KnowledgeModuleIndexAPIView,
    KnowledgeModuleListAPIView,
    KnowledgeQueryAPIView,
)
from backend.gateway.middleware import JWTAuthenticationMiddleware
from engines.ae_harness.knowledge.service import Retrieval

pytestmark = [pytest.mark.django_db, pytest.mark.api]


@pytest.fixture
def normal_user(db):
    return get_user_model().objects.create_user(username="normal", password="pass")


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_user(
        username="admin", password="pass", is_superuser=True, is_staff=True
    )


@pytest.fixture
def data_dir(tmp_path):
    target = tmp_path / "docs"
    target.mkdir()
    return target


class _FakeRetriever:
    def __init__(self, config):
        self.config = config

    async def retrieve(self, query, *, base=None, top_k=None):
        return Retrieval("no_hit")

    async def ensure_index(self, base):
        return 1

    def error(self, base):
        return ""

    def usage_events(self):
        return []


@pytest.fixture
def fake_retriever(monkeypatch, tmp_path):
    from backend.apps.ai_assistant.models import AIModelConfig
    from backend.apps.knowledge_search.models import RetrievalSettings

    model = AIModelConfig.objects.create(
        provider="dashscope",
        api_key_env="DASHSCOPE_API_KEY",
        model_kind="embedding",
        model_name="text-embedding-v4",
        dimensions=1024,
    )
    RetrievalSettings.objects.create(
        embedding_model_id=model.id,
        top_k=4,
        score_threshold=0.45,
        chunk_size=400,
        chunk_overlap=60,
    )
    monkeypatch.setattr(retrieval, "KnowledgeRetriever", _FakeRetriever)
    monkeypatch.setattr(retrieval, "INDEX_DIR", tmp_path / "index")


def _call(
    view_cls,
    *,
    method="get",
    path="/api/knowledge-search/modules/",
    user=None,
    data=None,
    **url_kwargs,
):
    factory = APIRequestFactory()
    request = getattr(factory, method)(path, data or {}, format="json")
    if user is not None:
        request.user_id = str(user.id)
        force_authenticate(request, user=user)
    return view_cls.as_view()(request, **url_kwargs)


def _create_module(admin_user, data_dir, name="kb_a"):
    return _call(
        KnowledgeModuleListAPIView,
        method="post",
        user=admin_user,
        data={"name": name, "description": "说明", "data_dir": str(data_dir)},
    )


def test_middleware_rejects_missing_token():
    request = RequestFactory().get("/api/knowledge-search/modules/")
    response = JWTAuthenticationMiddleware(lambda _request: None)(request)
    assert response.status_code == 401


def test_routes_resolve_with_trailing_slash():
    for path in (
        "/api/knowledge-search/modules/",
        "/api/knowledge-search/modules/1/",
        "/api/knowledge-search/modules/1/index/",
        "/api/knowledge-search/query/",
    ):
        assert resolve(path).app_name == "knowledge_search"
    with pytest.raises(Resolver404):
        resolve("/api/knowledge-search/modules")


def test_module_list_readable_by_normal_user(normal_user):
    response = _call(KnowledgeModuleListAPIView, user=normal_user)
    assert response.status_code == 200
    assert "modules" in response.data


def test_envelope_wraps_success(normal_user):
    response = _call(KnowledgeModuleListAPIView, user=normal_user)
    response.render()
    payload = json.loads(response.content)
    assert payload["status"] is True
    assert "modules" in payload["data"]


def test_create_module_requires_superuser(normal_user, admin_user, data_dir):
    denied = _call(
        KnowledgeModuleListAPIView,
        method="post",
        user=normal_user,
        data={"name": "kb_a", "description": "说明", "data_dir": str(data_dir)},
    )
    assert denied.status_code == 403
    created = _create_module(admin_user, data_dir)
    assert created.status_code == 201
    assert created.data["name"] == "kb_a"


def test_create_module_validation(admin_user, data_dir):
    bad_name = _call(
        KnowledgeModuleListAPIView,
        method="post",
        user=admin_user,
        data={"name": "Bad-Name", "description": "说明", "data_dir": str(data_dir)},
    )
    assert bad_name.status_code == 400
    _create_module(admin_user, data_dir)
    conflict = _call(
        KnowledgeModuleListAPIView,
        method="post",
        user=admin_user,
        data={"name": "kb_b", "description": "说明", "data_dir": str(data_dir)},
    )
    assert conflict.status_code == 400
    assert "冲突" in str(conflict.data)


def test_patch_and_delete_module(admin_user, normal_user, data_dir, tmp_path):
    created = _create_module(admin_user, data_dir)
    pk = created.data["id"]
    denied = _call(
        KnowledgeModuleDetailAPIView,
        method="patch",
        user=normal_user,
        data={"enabled": False},
        pk=pk,
    )
    assert denied.status_code == 403
    new_dir = tmp_path / "new_docs"
    new_dir.mkdir()
    patched = _call(
        KnowledgeModuleDetailAPIView,
        method="patch",
        user=admin_user,
        data={"data_dir": str(new_dir)},
        pk=pk,
    )
    assert patched.status_code == 200
    assert patched.data["data_dir"] == str(new_dir.resolve())
    missing = _call(
        KnowledgeModuleDetailAPIView,
        method="patch",
        user=admin_user,
        data={"enabled": False},
        pk=999999,
    )
    assert missing.status_code == 404
    deleted = _call(KnowledgeModuleDetailAPIView, method="delete", user=admin_user, pk=pk)
    assert deleted.status_code == 200
    assert deleted.data["deleted"] is True


def test_query_validates_inputs(normal_user, fake_retriever):
    empty_bases = _call(
        KnowledgeQueryAPIView,
        method="post",
        path="/api/knowledge-search/query/",
        user=normal_user,
        data={"question": "问题", "bases": []},
    )
    assert empty_bases.status_code == 400
    blank_question = _call(
        KnowledgeQueryAPIView,
        method="post",
        path="/api/knowledge-search/query/",
        user=normal_user,
        data={"question": "   ", "bases": ["kb_a"]},
    )
    assert blank_question.status_code == 400


def test_query_returns_three_state_payload(normal_user, admin_user, data_dir, fake_retriever):
    _create_module(admin_user, data_dir)
    retrieval.mark_indexed("kb_a", 0)
    response = _call(
        KnowledgeQueryAPIView,
        method="post",
        path="/api/knowledge-search/query/",
        user=normal_user,
        data={"question": "问题", "bases": ["kb_a"]},
    )
    assert response.status_code == 200
    assert response.data["result"] == "no_hit"
    assert response.data["hits"] == []


def test_index_requires_superuser(normal_user, admin_user, data_dir, fake_retriever):
    created = _create_module(admin_user, data_dir)
    pk = created.data["id"]
    denied = _call(KnowledgeModuleIndexAPIView, method="post", user=normal_user, pk=pk)
    assert denied.status_code == 403
    allowed = _call(KnowledgeModuleIndexAPIView, method="post", user=admin_user, pk=pk)
    assert allowed.status_code == 200
    assert allowed.data == {"ok": True, "error": "", "reindexed": 1}
