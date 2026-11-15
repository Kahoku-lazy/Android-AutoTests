"""知识库本地向量库：集合、写入、删除与余弦检索。

只写临时 SQLite，不联网、不调嵌入模型。
"""

from __future__ import annotations

import pytest

from agentscope.message import TextBlock
from agentscope.rag import Chunk, VectorRecord

from engines.ae_harness.knowledge.store import SQLiteVectorStore

pytestmark = [pytest.mark.unit]


def _record(document_id: str, index: int, text: str, vector: list[float]) -> VectorRecord:
    """造一条带向量的文档块。

    Args:
        document_id: 文档编号。
        index: 片段序号。
        text: 片段正文。
        vector: 向量。

    Returns:
        向量记录。
    """
    return VectorRecord(
        vector=vector,
        document_id=document_id,
        chunk=Chunk(
            content=TextBlock(text=text),
            source=f"{document_id}.md",
            chunk_index=index,
            total_chunks=1,
            metadata={},
        ),
    )


async def test_collection_and_search_roundtrip(tmp_path):
    """建集合、写入两条、按相似度检索并命中更近的一条。"""
    store = SQLiteVectorStore(tmp_path / "rag.sqlite3")
    async with store:
        assert await store.has_collection("kb") is False
        await store.create_collection("kb", 2)
        assert await store.has_collection("kb") is True
        await store.insert(
            "kb",
            [
                _record("doc_a", 0, "开门指示", [1.0, 0.0]),
                _record("doc_b", 0, "缺水提醒", [0.0, 1.0]),
            ],
        )
        results = await store.search("kb", [0.9, 0.1], top_k=2)
    assert [result.document_id for result in results] == ["doc_a", "doc_b"]
    assert results[0].score > results[1].score


async def test_delete_document_removes_all_chunks(tmp_path):
    """按文档删除后，该文档的块不再出现在检索与列表里。"""
    store = SQLiteVectorStore(tmp_path / "rag.sqlite3")
    async with store:
        await store.create_collection("kb", 2)
        await store.insert(
            "kb",
            [
                _record("doc_a", 0, "一", [1.0, 0.0]),
                _record("doc_a", 1, "二", [1.0, 0.0]),
                _record("doc_b", 0, "三", [0.0, 1.0]),
            ],
        )
        await store.delete("kb", "doc_a")
        results = await store.search("kb", [1.0, 0.0], top_k=5)
        documents = await store.list_documents("kb")
    assert [result.document_id for result in results] == ["doc_b"]
    assert [item.document_id for item in documents] == ["doc_b"]


async def test_dimension_mismatch_and_missing_collection(tmp_path):
    """维度不符或集合不存在时报错，不静默写入。"""
    store = SQLiteVectorStore(tmp_path / "rag.sqlite3")
    async with store:
        await store.create_collection("kb", 2)
        with pytest.raises(RuntimeError, match="维度"):
            await store.insert("kb", [_record("doc_a", 0, "x", [1.0, 0.0, 0.0])])
        with pytest.raises(RuntimeError, match="集合不存在"):
            await store.insert("other", [_record("doc_a", 0, "x", [1.0, 0.0])])
        with pytest.raises(RuntimeError, match="维度不一致"):
            await store.create_collection("kb", 3)


async def test_metadata_filter_limits_results(tmp_path):
    """metadata_filter 只返回匹配的记录。"""
    store = SQLiteVectorStore(tmp_path / "rag.sqlite3")
    async with store:
        await store.create_collection("kb", 2)
        record = _record("doc_a", 0, "一", [1.0, 0.0])
        other = _record("doc_b", 0, "二", [1.0, 0.0])
        other.chunk.metadata = {"tenant_id": "b"}
        await store.insert("kb", [record, other])
        results = await store.search("kb", [1.0, 0.0], top_k=5, metadata_filter={"tenant_id": "b"})
    assert [result.document_id for result in results] == ["doc_b"]
