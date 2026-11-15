"""知识库工具返回契约：三种文案、只读标记与不向上抛异常。

用替身检索器承接查询，不联网、不写索引。
"""

from __future__ import annotations

import json

import pytest

from engines.ae_harness.knowledge.service import KnowledgeHit, Retrieval
from engines.ae_harness.knowledge.tool import build_knowledge_tools

pytestmark = [pytest.mark.unit]

_HIT = KnowledgeHit(
    base="kb",
    source="a.md",
    text="正文",
    score=0.75,
    chunk_index=0,
    document_id="doc_a",
)


class _FakeRetriever:
    """按构造时给定的结果返回固定检索结论。"""

    def __init__(self, result: Retrieval | Exception) -> None:
        self.result = result
        self.calls: list[tuple[str, str | None, int | None]] = []

    async def retrieve(self, query: str, *, base=None, top_k=None) -> Retrieval:
        """记录入参并返回预设结果。"""
        self.calls.append((query, base, top_k))
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def _tool(retriever: _FakeRetriever):
    """取唯一那个工具。"""
    return build_knowledge_tools(retriever)[0]  # type: ignore[arg-type]


def _payload(chunk) -> dict:
    """从 ToolChunk 里取回 JSON 载荷。"""
    return json.loads(chunk.content[0].text)


async def test_tool_is_read_only_and_named():
    """工具名固定为 search_knowledge 且只读。"""
    tool = _tool(_FakeRetriever(Retrieval("no_hit")))
    assert tool.name == "search_knowledge"
    assert tool.is_read_only is True


async def test_ok_payload_carries_hits():
    """有命中时返回 status=true 与 hits。"""
    retriever = _FakeRetriever(Retrieval("ok", hits=(_HIT,)))
    payload = _payload(await _tool(retriever).call(query="指示灯", base="", top_k=2))

    assert payload["status"] is True
    assert payload["count"] == 1
    assert payload["hits"][0]["source"] == "a.md"
    assert payload["hits"][0]["score"] == 0.75
    assert retriever.calls == [("指示灯", None, 2)]


async def test_no_hit_has_distinct_note():
    """无命中仍是 status=true，但带独立说明。"""
    payload = _payload(await _tool(_FakeRetriever(Retrieval("no_hit"))).call(query="x"))
    assert payload["status"] is True
    assert payload["hits"] == []
    assert "没有命中" in payload["note"]


async def test_unavailable_is_failure_with_reason():
    """检索不可用时 status=false 并给出原因。"""
    retriever = _FakeRetriever(Retrieval("unavailable", error="没有启用的知识库"))
    payload = _payload(await _tool(retriever).call(query="x"))
    assert payload["status"] is False
    assert "检索不可用" in payload["error"]


async def test_exception_is_converted_not_raised():
    """检索器抛异常时工具不向上抛，转成可读失败。"""
    payload = _payload(await _tool(_FakeRetriever(RuntimeError("boom"))).call(query="x"))
    assert payload["status"] is False
    assert "boom" in payload["error"]


async def test_mounting_does_not_load_config(monkeypatch):
    """挂载阶段不读配置：配置坏了只在调用时降级，不炸掉入口。"""

    def _broken(**kwargs):
        """模拟配置装载失败。"""
        raise ValueError("配置坏了")

    monkeypatch.setattr(
        "engines.ae_harness.knowledge.service.load_config",
        _broken,
    )
    tool = build_knowledge_tools()[0]
    payload = _payload(await tool.call(query="x"))
    assert payload["status"] is False
    assert "配置坏了" in payload["error"]
