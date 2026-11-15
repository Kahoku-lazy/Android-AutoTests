"""RAG 本地向量库与上下文格式化单测：不联网、不依赖 rag_data。"""

from __future__ import annotations

import pytest

from agentscope.message import TextBlock
from agentscope.rag import Chunk, VectorRecord

from engines.agents.rag.config import load_rag_config

from engines.agents.rag.store import SQLiteVectorStore

pytestmark = [pytest.mark.unit]


def _record(document_id: str, index: int, text: str, vector: list[float]) -> VectorRecord:
    return VectorRecord(
        vector=vector,
        document_id=document_id,
        chunk=Chunk(
            content=TextBlock(text=text),
            source=f"{document_id}.md",
            chunk_index=index,
            total_chunks=1,
            metadata={"document_id": document_id},
        ),
    )


@pytest.mark.asyncio
async def test_sqlite_store_insert_search_delete(tmp_path):
    """写入、检索、列出、删除文档。"""
    store = SQLiteVectorStore(tmp_path / "rag.sqlite3")
    await store.create_collection("kb", 3)
    await store.insert(
        "kb",
        [
            _record("doc_a", 0, "长按开关按键3秒进入网络待机", [1.0, 0.0, 0.0]),
            _record("doc_b", 0, "红灯长亮表示缺水", [0.0, 1.0, 0.0]),
        ],
    )

    results = await store.search("kb", [0.9, 0.1, 0.0], top_k=1)

    assert len(results) == 1
    assert results[0].document_id == "doc_a"
    assert results[0].chunk.content.text.startswith("长按开关按键")
    assert results[0].score > 0.9

    documents = await store.list_documents("kb")
    assert {doc.document_id for doc in documents} == {"doc_a", "doc_b"}

    await store.delete("kb", "doc_a")
    assert await store.list_documents("kb") == [
        doc for doc in documents if doc.document_id == "doc_b"
    ]
    assert await store.has_collection("kb") is True


@pytest.mark.asyncio
async def test_sqlite_store_rejects_dimension_mismatch(tmp_path):
    """向量维度不符时拒绝写入。"""
    store = SQLiteVectorStore(tmp_path / "rag.sqlite3")
    await store.create_collection("kb", 2)

    with pytest.raises(RuntimeError, match="维度"):
        await store.insert(
            "kb",
            [_record("doc_a", 0, "x", [1.0, 0.0, 0.0])],
        )


def test_rag_config_defaults():
    """检索参数默认阈值为 0.55，资料范围不在这里决定。"""
    config = load_rag_config(
        {"DASHSCOPE_API_KEY": "sk-test"},
    )

    assert config.enabled is True
    assert config.score_threshold == 0.55
    assert config.top_k == 4


def test_sqlite_store_supports_async_context(tmp_path):
    """向量库提供异步上下文，当前不保留长连接。"""

    async def _open() -> None:
        async with SQLiteVectorStore(tmp_path / "rag.sqlite3") as store:
            await store.create_collection("kb", 2)

    import asyncio

    asyncio.run(_open())
    assert (tmp_path / "rag.sqlite3").exists()
