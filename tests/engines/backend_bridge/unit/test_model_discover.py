"""模型名单查询：厂商密钥必须成对，返回只取 id，失败改手填。"""

from __future__ import annotations

import json

import pytest

from engines.backend_bridge.models.catalog import expected_key, models_url
from engines.backend_bridge.models.discover import discover_models


def test_provider_key_pairs():
    """三家厂商各自只认一个密钥环境变量。"""
    assert expected_key("deepseek") == "DEEPSEEK_API_KEY"
    assert expected_key("dashscope") == "DASHSCOPE_API_KEY"
    assert expected_key("govee") == "GOVEE_API_KEY"


def test_models_url_requires_address():
    """地址必须由调用方传入，空地址不再补默认。"""
    assert models_url("deepseek", "") == ""
    assert models_url("govee", "https://example.test/v1") == "https://example.test/v1/models"


def test_models_url_does_not_duplicate_suffix():
    """地址已经以 /models 结尾时不再追加。"""
    assert models_url("govee", "https://example.test/v1/models") == "https://example.test/v1/models"


def test_discover_rejects_mismatched_key():
    """厂商和密钥环境变量不成对时拒绝查询。"""
    with pytest.raises(ValueError):
        discover_models("deepseek", "GOVEE_API_KEY")


def test_discover_manual_when_secret_missing(monkeypatch):
    """环境变量没配时不发请求，改用手填。"""
    monkeypatch.setattr("engines.backend_bridge.models.discover.load_secret", lambda _name: "")
    found = discover_models("deepseek", "DEEPSEEK_API_KEY")
    assert found["source"] == "manual"
    assert found["models"] == []


def test_discover_reads_ids_without_returning_secret(monkeypatch):
    """只返回模型 id，响应里不出现密钥。"""

    class _Response:
        def read(self):
            return json.dumps(
                {"data": [{"id": "deepseek-flash"}, {"id": "deepseek-flash"}]}
            ).encode()

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return False

    monkeypatch.setattr(
        "engines.backend_bridge.models.discover.load_secret", lambda _name: "secret-value"
    )
    monkeypatch.setattr(
        "engines.backend_bridge.models.discover.urllib.request.urlopen",
        lambda *_args, **_kwargs: _Response(),
    )
    found = discover_models("deepseek", "DEEPSEEK_API_KEY", "https://api.deepseek.com")
    assert found == {"models": ["deepseek-flash"], "source": "remote", "reason": ""}
    assert "secret-value" not in json.dumps(found)
