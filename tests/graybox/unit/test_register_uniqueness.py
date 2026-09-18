"""注册用户名唯一性契约（OpenSpec: fix-register-duplicate-race）。

唯一性以**数据库唯一约束**为权威：写口把 IntegrityError 翻译为 ConflictError，视图映射 409。
输入校验层不做唯一性保证，因此顺序重名与并发重名走同一条路径。
"""

from __future__ import annotations

import inspect
import json

import pytest

from django.contrib.auth.models import User
from django.db import transaction
from django.test import Client

from apps.accounts import api
from apps.accounts.serializers import RegisterSerializer

pytestmark = [pytest.mark.django_db, pytest.mark.unit, pytest.mark.auth]

PASSWORD = "pw123456"


def _register(c, username, **over):
    body = {
        "username": username,
        "password": PASSWORD,
        "password2": PASSWORD,
        "email": f"{username}@test.local",
    }
    body.update(over)
    return c.post("/api/auth/register/", data=json.dumps(body), content_type="application/json")


def test_sequential_duplicate_returns_409():
    """Scenario: 顺序重名注册。"""
    c = Client()
    assert _register(c, "dup_seq").status_code == 200

    r = _register(c, "dup_seq")
    assert r.status_code == 409, r.content
    assert r.json()["message"] == "用户名已存在"


def test_duplicate_appearing_at_write_time_returns_409(monkeypatch):
    """Scenario: 并发重名注册 —— 同名用户在「校验通过之后、写入之前」被别人抢注。

    真实并发无法稳定复现，因此把竞态的那一瞬固定下来：写口在真正插入前先插入一个同名用户。
    修复前这条路径抛出未被捕获的 IntegrityError → 500。
    """
    c = Client()
    original = api.create_user

    def preempted(username, password, email):
        User.objects.create_user(username=username, password="other", email="x@y.z")
        return original(username=username, password=password, email=email)

    monkeypatch.setattr(api, "create_user", preempted)

    r = _register(c, "dup_race")
    assert r.status_code == 409, r.content
    assert r.json()["message"] == "用户名已存在"


def test_write_port_translates_integrity_error():
    """Scenario: 写口不泄漏底层异常。"""
    api.create_user(username="dup_port", password=PASSWORD, email="a@b.c")

    with pytest.raises(api.ConflictError) as ei:
        api.create_user(username="dup_port", password=PASSWORD, email="a@b.c")

    # 因果链保留，但抛给调用方的不再是 IntegrityError
    assert ei.value.__cause__ is not None
    assert ei.value.__cause__.__class__.__name__ == "IntegrityError"


def test_conflict_does_not_break_caller_transaction():
    """Scenario: 冲突不破坏调用方事务（savepoint 隔离）。"""
    api.create_user(username="dup_tx", password=PASSWORD, email="a@b.c")

    with transaction.atomic():
        with pytest.raises(api.ConflictError):
            api.create_user(username="dup_tx", password=PASSWORD, email="a@b.c")
        # 外层事务仍可用：失败被 savepoint 隔离，后续查询与写入都能执行
        assert User.objects.filter(username="dup_tx").count() == 1
        api.create_user(username="after_tx", password=PASSWORD, email="c@d.e")

    assert User.objects.filter(username="after_tx").exists()


def test_serializer_does_not_guarantee_uniqueness():
    """设计约束：唯一性权威在写口，校验层不得再做前置判重。"""
    src = inspect.getsource(RegisterSerializer)
    assert "User.objects" not in src, "校验层重新引入了唯一性前置检查（唯一性应由写口保证）"
