"""evaluator DRF 写路径：契约兑现 + 写库收敛。

修复前三个问题（实测证据见变更 tasks §1）：

- `DELETE /runs/{id}/` **恒 404**：`EvalRunViewSet.get_queryset()` 对所有非 `retrieve` 动作返回已切片查询集
  （`...order_by("-created_at")[:50]`），DRF 的 `get_object_or_404` 把
  `TypeError: Cannot filter a query once a slice has been taken.` 吞成 `Http404`
  → 删除从未生效（API-评估器.md §4.4 登记为 204）。
- `POST /runs/` **201 但静默丢弃** `agent_id` / `bank_id`：DRF 把 FK 的 `*_id` attname 建成 `ReadOnlyField`，
  于是 `validated_data` 里没有这两个字段，而 §4.2 登记二者为「可写字段」。
- `QuestionBankViewSet` / `EvalRunViewSet` 走 DRF 默认 `perform_destroy`（`instance.delete()`）直写库，
  越过 `api.py`，而 `api.delete_question_bank` / `api.delete_eval_run` 已存在且 legacy 正在用。
"""

from __future__ import annotations

import inspect
import json

import pytest

from django.contrib.auth import get_user_model
from django.test import Client
from rest_framework import viewsets

from apps.ai_assistant.models import AIAgent
from apps.evaluator import api as evaluator_api
from apps.evaluator import views_api
from apps.evaluator.models import EvalRun, QuestionBank
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


@pytest.fixture
def client():
    user = get_user_model().objects.create_user(
        username="ev-drf-writes", password="x", email="ev-drf-writes@example.com"
    )
    return Client(HTTP_AUTHORIZATION=f"Bearer {create_access_token(str(user.pk))}")


def _post(client, path, payload):
    return client.post(path, data=json.dumps(payload), content_type="application/json")


# ── ① DELETE /runs/{id}/ 恒 404 → 现按契约删除 ──


def test_delete_run_removes_record(client):
    """修复前：run 确实存在却返回 404，删除从未生效。"""
    run = EvalRun.objects.create(status="pending")

    resp = client.delete(f"/api/evaluator/runs/{run.id}/")

    assert resp.status_code == 204, resp.content[:300]
    assert not EvalRun.objects.filter(id=run.id).exists()


def test_delete_run_goes_through_api(client, monkeypatch):
    """收敛断言：删除经 api.delete_eval_run，而不是 instance.delete()。"""
    calls = []
    real = evaluator_api.delete_eval_run

    def spy(run_id):
        calls.append(run_id)
        return real(run_id)

    monkeypatch.setattr(evaluator_api, "delete_eval_run", spy)
    run = EvalRun.objects.create(status="pending")

    resp = client.delete(f"/api/evaluator/runs/{run.id}/")

    assert resp.status_code == 204, resp.content[:300]
    assert calls == [run.id], "view 未调用 api.delete_eval_run（越过 api.py 直写库）"


def test_delete_missing_run_returns_404(client):
    """切片只在 list：非切片查询集让「不存在」重新是真的不存在，而不是被切片吞掉的 404。"""
    resp = client.delete("/api/evaluator/runs/999999/")

    assert resp.status_code == 404, resp.content[:300]


# ── ② DELETE /banks/{id}/ 直写库 → 现走 api ──


def test_delete_bank_goes_through_api(client, monkeypatch):
    calls = []
    real = evaluator_api.delete_question_bank

    def spy(bank_id):
        calls.append(bank_id)
        return real(bank_id)

    monkeypatch.setattr(evaluator_api, "delete_question_bank", spy)
    bank = QuestionBank.objects.create(name="试卷待删")

    resp = client.delete(f"/api/evaluator/banks/{bank.id}/")

    assert resp.status_code == 204, resp.content[:300]
    assert calls == [bank.id], "view 未调用 api.delete_question_bank（越过 api.py 直写库）"
    assert not QuestionBank.objects.filter(id=bank.id).exists()


# ── ③ POST /runs/ 静默丢 agent_id/bank_id → 现按 §4.2 契约落库 ──


def test_post_run_persists_agent_and_bank(client):
    """修复前：201 但 agent_id/bank_id 落库为 NULL。"""
    agent = AIAgent.objects.create(name="被评测 Agent")
    bank = QuestionBank.objects.create(name="评测试卷")

    resp = _post(client, "/api/evaluator/runs/", {"agent_id": agent.id, "bank_id": bank.id})

    assert resp.status_code == 201, resp.content[:300]
    body = resp.json()["data"]
    assert body["agent_id"] == agent.id
    assert body["bank_id"] == bank.id
    run = EvalRun.objects.get(id=body["id"])
    assert run.agent_id == agent.id
    assert run.bank_id == bank.id


def test_post_run_without_ids_is_allowed(client):
    """两字段登记为「非必填」（EvalRun.agent / bank 可空）：缺省即 NULL，不是报错。"""
    resp = _post(client, "/api/evaluator/runs/", {})

    assert resp.status_code == 201, resp.content[:300]
    run = EvalRun.objects.get(id=resp.json()["data"]["id"])
    assert run.agent_id is None
    assert run.bank_id is None


def test_post_run_keeps_documented_defaults(client):
    """§4.2 登记的缺省值不受本次改动影响。"""
    resp = _post(client, "/api/evaluator/runs/", {})

    body = resp.json()["data"]
    assert body["framework"] == "self"
    assert body["status"] == "pending"
    assert body["judge_provider"] == "dashscope"
    assert body["judge_model"] == "qwen-max"


def test_post_run_unknown_agent_returns_404(client):
    """给定但不存在 → 404（与 start 动作同文案），不静默落 NULL。"""
    resp = _post(client, "/api/evaluator/runs/", {"agent_id": 999999})

    assert resp.status_code == 404, resp.content[:300]
    assert resp.json()["message"] == "agent not found"
    assert EvalRun.objects.count() == 0


def test_post_run_unknown_bank_returns_404(client):
    agent = AIAgent.objects.create(name="被评测 Agent")

    resp = _post(client, "/api/evaluator/runs/", {"agent_id": agent.id, "bank_id": 999999})

    assert resp.status_code == 404, resp.content[:300]
    assert resp.json()["message"] == "question bank not found"
    assert EvalRun.objects.count() == 0


def test_post_run_goes_through_api(client, monkeypatch):
    calls = []
    real = evaluator_api.create_eval_run

    def spy(**kwargs):
        calls.append(kwargs)
        return real(**kwargs)

    monkeypatch.setattr(evaluator_api, "create_eval_run", spy)
    agent = AIAgent.objects.create(name="被评测 Agent")
    bank = QuestionBank.objects.create(name="评测试卷")

    resp = _post(client, "/api/evaluator/runs/", {"agent_id": agent.id, "bank_id": bank.id})

    assert resp.status_code == 201, resp.content[:300]
    assert calls, "view 未调用 api.create_eval_run"
    assert calls[0]["agent"].id == agent.id
    assert calls[0]["bank"].id == bank.id


# ── ④ 切片分派未改变既有 list / retrieve 行为 ──


def test_list_still_caps_at_50(client):
    for i in range(55):
        EvalRun.objects.create(status="pending", framework=f"f{i}")

    resp = client.get("/api/evaluator/runs/")

    assert resp.status_code == 200, resp.content[:300]
    assert len(resp.json()["data"]) == 50


def test_retrieve_run_returns_detail_fields(client):
    run = EvalRun.objects.create(status="completed", judge_provider="dashscope")

    resp = client.get(f"/api/evaluator/runs/{run.id}/")

    assert resp.status_code == 200, resp.content[:300]
    body = resp.json()["data"]
    assert body["id"] == run.id
    assert body["status"] == "completed"
    # 详情序列化器独有字段（列表序列化器没有），证明 retrieve 分支仍用 EvalRunSerializer
    assert body["judge_provider"] == "dashscope"
    assert "results" in body


# ── ⑤ 收敛断言 ──


def test_eval_result_viewset_is_read_only():
    """EvalResultSerializer.question_id 只读不是缺陷：结果集无 create 路径。"""
    assert issubclass(views_api.EvalResultViewSet, viewsets.ReadOnlyModelViewSet)


def test_views_api_has_no_implicit_write():
    """收敛断言：DRF 视图不得再出现 `serializer.save()` / `instance.delete()` / `.objects.create(`。"""
    source = inspect.getsource(views_api)
    assert "serializer.save()" not in source
    assert "instance.delete()" not in source
    assert ".objects.create(" not in source
