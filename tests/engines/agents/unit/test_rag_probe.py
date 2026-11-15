"""知识库探针：区分无命中和配置错误。"""

from __future__ import annotations

import pytest

from engines.agents.rag.probe import main

pytestmark = [pytest.mark.unit]


def test_probe_rejects_missing_embedding(monkeypatch, capsys):
    monkeypatch.setattr("engines.agents.rag.probe.load_project_env", lambda: None)
    monkeypatch.delenv("DASHSCOPE_API_KEY", raising=False)
    monkeypatch.delenv("EMBEDDING_API_KEY", raising=False)

    assert main(["retrieve", "product_manuals", "恢复"]) == 1
    assert "嵌入检索未启用" in capsys.readouterr().out


def test_probe_no_hit_exits_zero(monkeypatch, capsys):
    class _Service:
        enabled = True

        @classmethod
        def from_env(cls):
            return cls()

        async def retrieve(self, base, query):
            return []

        def error(self, base):
            return ""

    monkeypatch.setattr("engines.agents.rag.probe.load_project_env", lambda: None)
    monkeypatch.setattr("engines.agents.rag.probe.KnowledgeBaseService", _Service)

    assert main(["retrieve", "product_manuals", "不存在的问题"]) == 0
    output = capsys.readouterr().out
    assert "hits: 0" in output
    assert "source=" not in output
