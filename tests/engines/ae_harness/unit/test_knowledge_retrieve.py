"""知识库检索：命中字段、合并排序与三种降级。

用替身 _search_one 承接单库检索，不联网、不调嵌入模型。
"""

from __future__ import annotations

import pytest

from engines.ae_harness.knowledge.config import load_config
from engines.ae_harness.knowledge.service import KnowledgeHit, KnowledgeRetriever

pytestmark = [pytest.mark.unit]


def _hit(base: str, score: float, index: int = 0) -> KnowledgeHit:
    """造一条命中。

    Args:
        base: 库名。
        score: 相似度。
        index: 片段序号。

    Returns:
        命中对象。
    """
    return KnowledgeHit(
        base=base,
        source="a.md",
        text="正文",
        score=score,
        chunk_index=index,
        document_id=f"doc_{base}",
    )


async def test_unknown_base_is_unavailable():
    """库名不存在时降级为不可用。"""
    result = await KnowledgeRetriever(load_config()).retrieve("问题", base="nope")
    assert result.status == "unavailable"
    assert "知识库不存在" in result.error


async def test_disabled_base_is_unavailable():
    """禁用的库不允许检索。"""
    result = await KnowledgeRetriever(load_config()).retrieve("问题", base="log_keywords")
    assert result.status == "unavailable"
    assert "已禁用" in result.error


async def test_blank_query_is_unavailable():
    """空白问题不触发检索。"""
    result = await KnowledgeRetriever(load_config()).retrieve("   ")
    assert result.status == "unavailable"
    assert "不能为空" in result.error


async def test_hits_are_merged_sorted_and_truncated(monkeypatch):
    """命中按分数降序，并按 top_k 截断。"""
    retriever = KnowledgeRetriever(load_config())

    async def fake_search_one(base: str, query: str, top_k: int):
        """按库返回固定命中。"""
        return [_hit(base, 0.6), _hit(base, 0.9, 1)]

    monkeypatch.setattr(retriever, "_search_one", fake_search_one)
    merged = await retriever.retrieve("问题")
    assert [hit.score for hit in merged.hits] == [0.9, 0.6]

    truncated = await retriever.retrieve("问题", top_k=1)
    assert [hit.score for hit in truncated.hits] == [0.9]


async def test_no_hit_is_not_unavailable(monkeypatch):
    """库可用但没命中时状态是 no_hit。"""
    retriever = KnowledgeRetriever(load_config())

    async def fake_search_one(base: str, query: str, top_k: int):
        """返回空命中。"""
        return []

    monkeypatch.setattr(retriever, "_search_one", fake_search_one)
    result = await retriever.retrieve("问题")
    assert result.status == "no_hit"
    assert result.hits == ()


async def test_hit_dict_carries_acceptance_fields():
    """命中字典包含六个验收字段。"""
    payload = _hit("kb", 0.5123).as_dict()
    assert set(payload) == {"base", "source", "text", "score", "chunk_index", "document_id"}
    assert payload["score"] == 0.5123
