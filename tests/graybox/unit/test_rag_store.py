"""RAG 本地向量库与上下文格式化单测：不联网、不依赖 rag_data。"""

from __future__ import annotations

import pytest

from agentscope.message import TextBlock
from agentscope.rag import Chunk, VectorRecord

from engines.agents.rag.config import load_rag_config
from engines.agents.rag.service import RagHit, format_context
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
    """默认读取 D 盘 rag_data，阈值为 0.55。"""
    config = load_rag_config(
        {"DASHSCOPE_API_KEY": "sk-test"},
    )

    assert config.enabled is True
    assert str(config.data_dir) == r"D:\Govee\data\rag_data"
    assert config.score_threshold == 0.55
    assert config.top_k == 4


@pytest.mark.asyncio
async def test_rag_service_degrades_when_data_dir_missing(tmp_path):
    """数据目录缺失时返回空上下文，不抛异常。"""
    from engines.agents.rag.service import RagService

    rag = RagService.from_env(
        {
            "DASHSCOPE_API_KEY": "sk-test",
            "KNOWLEDGE_ASSISTANT_RAG_DATA_DIR": str(tmp_path / "missing"),
            "KNOWLEDGE_ASSISTANT_RAG_INDEX_DIR": str(tmp_path / "index"),
        },
    )

    assert await rag.ensure_index() == 0
    assert await rag.search("任意问题") == []
    assert await rag.build_context("任意问题") == ""


def test_build_rag_tool_is_read_only():
    """Omni 的 search_knowledge 工具是只读的。"""
    from engines.agents.rag.service import RagService
    from engines.agents.rag.tool import build_rag_tool

    tool = build_rag_tool(
        RagService(
            load_rag_config({"DASHSCOPE_API_KEY": "sk-test"}),
        ),
    )

    assert tool.name == "search_knowledge"
    assert tool.is_read_only is True


def test_format_context_contains_source_and_score():
    """上下文包含来源、片段与相关度，并在长度上限内截断。"""
    hits = [
        RagHit("a.md", "内容一", 0.8, 0, "doc_a"),
        RagHit("b.md", "内容二", 0.7, 1, "doc_b"),
    ]

    context = format_context(hits, 1000)

    assert "【检索资料】" in context
    assert "a.md" in context
    assert "内容一" in context
    assert "0.80" in context
    assert len(context) <= 1000
