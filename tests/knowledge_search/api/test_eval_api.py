"""自动评测接口契约：权限、题量上限、409、模型校验与报告读取。"""

from __future__ import annotations

import pytest

from django.contrib.auth import get_user_model
from django.urls import resolve
from rest_framework.test import APIRequestFactory, force_authenticate

from backend.apps.ai_assistant.models import AIModelConfig
from backend.apps.knowledge_search import api, eval_runner
from backend.apps.knowledge_search.views import EvalRunDetailAPIView, EvalRunListAPIView

pytestmark = [pytest.mark.django_db, pytest.mark.api]


@pytest.fixture(autouse=True)
def _no_thread(monkeypatch):
    """接口测试不起后台线程。"""
    monkeypatch.setattr(eval_runner, "start_eval_run", lambda pk: None)


@pytest.fixture
def normal_user(db):
    return get_user_model().objects.create_user(username="normal", password="pass")


@pytest.fixture
def admin_user(db):
    return get_user_model().objects.create_user(
        username="admin", password="pass", is_superuser=True, is_staff=True
    )


@pytest.fixture
def module_row(tmp_path):
    data_dir = tmp_path / "docs"
    data_dir.mkdir()
    return api.create_module(name="kb_eval", description="评测库", data_dir=str(data_dir))


@pytest.fixture
def chat_model(db):
    return AIModelConfig.objects.create(
        provider="dashscope",
        api_key_env="DASHSCOPE_API_KEY",
        model_name="qwen-flash",
        model_kind="chat",
    )


def _call(view_cls, *, method="get", user=None, data=None, **url_kwargs):
    factory = APIRequestFactory()
    request = getattr(factory, method)(
        "/api/knowledge-search/evaluations/", data or {}, format="json"
    )
    if user is not None:
        request.user_id = str(user.id)
        force_authenticate(request, user=user)
    return view_cls.as_view()(request, **url_kwargs)


def _trigger(admin_user, module_row, chat_model, **extra):
    payload = {"module_id": module_row.pk, "model_config_id": chat_model.pk, **extra}
    return _call(EvalRunListAPIView, method="post", user=admin_user, data=payload)


def test_eval_routes_resolve():
    assert resolve("/api/knowledge-search/evaluations/").url_name == "evaluations"
    assert resolve("/api/knowledge-search/evaluations/1/").url_name == "evaluation_detail"


def test_trigger_requires_superuser(normal_user, module_row, chat_model):
    response = _call(
        EvalRunListAPIView,
        method="post",
        user=normal_user,
        data={"module_id": module_row.pk, "model_config_id": chat_model.pk},
    )
    assert response.status_code == 403


def test_trigger_creates_pending_run(admin_user, module_row, chat_model):
    response = _trigger(admin_user, module_row, chat_model)
    assert response.status_code == 201
    assert response.data["status"] == "pending"
    assert response.data["pos_count"] == 30
    assert response.data["neg_count"] == 10
    assert response.data["cost_estimate"]["note"]
    run = api.get_eval_run(response.data["id"])
    assert run.module_snapshot["data_dir"] == module_row.data_dir


def test_trigger_caps_and_validation(admin_user, module_row, chat_model):
    over = _trigger(admin_user, module_row, chat_model, pos_count=90, neg_count=20)
    assert over.status_code == 400
    bad_model = _call(
        EvalRunListAPIView,
        method="post",
        user=admin_user,
        data={"module_id": module_row.pk, "model_config_id": 999999},
    )
    assert bad_model.status_code == 400
    api.update_module(module_row.pk, enabled=False)
    disabled = _trigger(admin_user, module_row, chat_model)
    assert disabled.status_code == 400


def test_second_trigger_conflicts(admin_user, module_row, chat_model):
    first = _trigger(admin_user, module_row, chat_model)
    assert first.status_code == 201
    second = _trigger(admin_user, module_row, chat_model)
    assert second.status_code == 409


def test_list_and_detail_readable_by_normal_user(normal_user, admin_user, module_row, chat_model):
    created = _trigger(admin_user, module_row, chat_model)
    listed = _call(EvalRunListAPIView, user=normal_user)
    assert listed.status_code == 200
    assert len(listed.data["runs"]) == 1
    detail = _call(EvalRunDetailAPIView, user=normal_user, pk=created.data["id"])
    assert detail.status_code == 200
    assert "queries" in detail.data
    missing = _call(EvalRunDetailAPIView, user=normal_user, pk=999999)
    assert missing.status_code == 404
