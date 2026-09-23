"""线路连通两段探测：list 只证密钥；chat 成功才可执行；线路三态聚合。"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from apps.ai_assistant.views_drf import (
    _aggregate_route_status,
    _health_is_stale,
    _test_agent_route,
    _test_model_config,
)


def _resp(status_code: int, payload=None, text: str = ""):
    r = MagicMock()
    r.status_code = status_code
    r.text = text or ("" if payload is None else str(payload))
    r.json.return_value = payload if payload is not None else {}
    return r


@pytest.mark.unit
def test_model_config_list_ok_chat_402_is_unusable_role():
    """list 2xx + chat 402 → connected=False, key_ok=True。"""

    def fake_call(base, api_key, path, method="GET", body=None):
        if path in ("/models", "/v1/models"):
            return _resp(200, {"data": [{"id": "m1"}]}), None
        return _resp(402, text="Insufficient Balance"), None

    with patch("apps.ai_assistant.views_drf._call_config_api", side_effect=fake_call):
        connected, key_ok, models, err = _test_model_config(
            "deepseek", "sk-x", "https://api.deepseek.com/v1", "m1"
        )

    assert connected is False
    assert key_ok is True
    assert "m1" in models
    assert "402" in err or "Insufficient" in err


@pytest.mark.unit
def test_model_config_list_and_chat_ok():
    """list + chat 均 2xx → connected=True, key_ok=True。"""

    def fake_call(base, api_key, path, method="GET", body=None):
        if path in ("/models", "/v1/models"):
            return _resp(200, {"data": [{"id": "m1"}, {"id": "m2"}]}), None
        return _resp(200, {"choices": []}), None

    with patch("apps.ai_assistant.views_drf._call_config_api", side_effect=fake_call):
        connected, key_ok, models, err = _test_model_config(
            "deepseek", "sk-x", "https://api.deepseek.com/v1", "m1"
        )

    assert connected is True
    assert key_ok is True
    assert models[0] == "m1"
    assert err == ""


@pytest.mark.unit
def test_model_config_list_401_chat_401():
    """鉴权失败 → connected=False, key_ok=False。"""

    def fake_call(base, api_key, path, method="GET", body=None):
        return _resp(401, text="Unauthorized"), None

    with patch("apps.ai_assistant.views_drf._call_config_api", side_effect=fake_call):
        connected, key_ok, _models, err = _test_model_config(
            "deepseek", "bad", "https://api.deepseek.com/v1", "m1"
        )

    assert connected is False
    assert key_ok is False
    assert "401" in err


@pytest.mark.unit
def test_model_config_model_missing_from_catalog_still_tries_chat():
    """目录不含配置名时仍发 chat；chat 成功则可用。"""
    calls = []

    def fake_call(base, api_key, path, method="GET", body=None):
        calls.append(path)
        if path in ("/models", "/v1/models"):
            return _resp(200, {"data": [{"id": "other"}]}), None
        return _resp(200, {"choices": []}), None

    with patch("apps.ai_assistant.views_drf._call_config_api", side_effect=fake_call):
        connected, key_ok, _models, err = _test_model_config(
            "deepseek", "sk-x", "https://api.deepseek.com/v1", "m1"
        )

    assert connected is True
    assert key_ok is True
    assert err == ""
    assert "/chat/completions" in calls


@pytest.mark.unit
def test_model_config_catalog_miss_and_chat_fail_keeps_hint():
    """目录不含且 chat 失败时，错误可带回目录提示。"""

    def fake_call(base, api_key, path, method="GET", body=None):
        if path in ("/models", "/v1/models"):
            return _resp(200, {"data": [{"id": "other"}]}), None
        return _resp(404, text="model not found"), None

    with patch("apps.ai_assistant.views_drf._call_config_api", side_effect=fake_call):
        connected, key_ok, _models, err = _test_model_config(
            "deepseek", "sk-x", "https://api.deepseek.com/v1", "m1"
        )

    assert connected is False
    assert key_ok is True
    assert "404" in err or "不在供应商目录" in err


@pytest.mark.unit
def test_aggregate_route_status_matrix():
    assert (
        _aggregate_route_status(
            {
                "planner": {"connected": True, "key_ok": True},
                "executor": {"connected": True, "key_ok": True},
                "verifier": {"connected": True, "key_ok": True},
            }
        )
        == "ready"
    )
    assert (
        _aggregate_route_status(
            {
                "planner": {"connected": False, "key_ok": True},
                "executor": {"connected": True, "key_ok": True},
                "verifier": {"connected": True, "key_ok": True},
            }
        )
        == "unusable"
    )
    assert (
        _aggregate_route_status(
            {
                "planner": {"connected": False, "key_ok": False},
                "executor": {"connected": False, "key_ok": False},
                "verifier": {"connected": False, "key_ok": False},
            }
        )
        == "offline"
    )


@pytest.mark.unit
def test_health_is_stale_without_status():
    assert _health_is_stale({"last_checked_at": "2099-01-01 00:00:00", "is_connected": True})
    assert not _health_is_stale(
        {
            "last_checked_at": "2099-01-01 00:00:00",
            "status": "ready",
            "is_connected": True,
        }
    )


def _agent_with_roles(role_cfg: dict):
    """构造带 route_configs.device_control 三角色的简易 agent。"""
    route = {"device_control": dict(role_cfg)}
    return SimpleNamespace(route_configs=route)


@pytest.mark.unit
def test_agent_route_402_aggregates_unusable():
    """三角色同密钥：list 通、chat 402 → unusable。"""
    role = {
        "provider": "deepseek",
        "model_name": "m1",
        "api_key": "sk-x",
        "base_url": "https://api.deepseek.com/v1",
    }
    agent = _agent_with_roles({"planner": role, "executor": role, "verifier": role})
    list_calls = {"n": 0}

    def fake_call(base, api_key, path, method="GET", body=None):
        if path in ("/models", "/v1/models"):
            list_calls["n"] += 1
            return _resp(200, {"data": [{"id": "m1"}]}), None
        return _resp(402, text="Insufficient Balance"), None

    with (
        patch("apps.ai_assistant.views_drf._call_config_api", side_effect=fake_call),
        patch(
            "apps.ai_assistant.api.get_route_model_config",
            side_effect=lambda a, r, role: (
                dict(role_cfg) if (role_cfg := (a.route_configs.get(r) or {}).get(role)) else {}
            ),
        ),
    ):
        status, results = _test_agent_route(agent, "device_control")

    assert status == "unusable"
    assert all(r["key_ok"] and not r["connected"] for r in results.values())
    # 同密钥只 list 一次（第一个成功的 path 即返回）
    assert list_calls["n"] == 1


@pytest.mark.unit
def test_agent_route_all_chat_ok_ready():
    role = {
        "provider": "deepseek",
        "model_name": "m1",
        "api_key": "sk-x",
        "base_url": "https://api.deepseek.com/v1",
    }
    agent = _agent_with_roles({"planner": role, "executor": role, "verifier": role})

    def fake_call(base, api_key, path, method="GET", body=None):
        if path in ("/models", "/v1/models"):
            return _resp(200, {"data": [{"id": "m1"}]}), None
        return _resp(200, {"choices": []}), None

    with (
        patch("apps.ai_assistant.views_drf._call_config_api", side_effect=fake_call),
        patch(
            "apps.ai_assistant.api.get_route_model_config",
            side_effect=lambda a, r, role: dict((a.route_configs.get(r) or {}).get(role) or {}),
        ),
    ):
        status, results = _test_agent_route(agent, "device_control")

    assert status == "ready"
    assert all(r["connected"] for r in results.values())


@pytest.mark.unit
def test_agent_route_empty_config_offline():
    agent = _agent_with_roles({})
    with patch(
        "apps.ai_assistant.api.get_route_model_config",
        return_value={},
    ):
        status, results = _test_agent_route(agent, "device_control")

    assert status == "offline"
    assert all(not r["key_ok"] and not r["connected"] for r in results.values())


@pytest.mark.unit
def test_agent_route_all_401_offline():
    role = {
        "provider": "deepseek",
        "model_name": "m1",
        "api_key": "bad",
        "base_url": "https://api.deepseek.com/v1",
    }
    agent = _agent_with_roles({"planner": role, "executor": role, "verifier": role})

    def fake_call(base, api_key, path, method="GET", body=None):
        return _resp(401, text="Unauthorized"), None

    with (
        patch("apps.ai_assistant.views_drf._call_config_api", side_effect=fake_call),
        patch(
            "apps.ai_assistant.api.get_route_model_config",
            side_effect=lambda a, r, role: dict((a.route_configs.get(r) or {}).get(role) or {}),
        ),
    ):
        status, results = _test_agent_route(agent, "device_control")

    assert status == "offline"
    assert all(not r["key_ok"] for r in results.values())
