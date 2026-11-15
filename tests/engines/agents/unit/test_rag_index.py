"""按库增量索引：跳过未变化文件，删除已消失文件。"""

from __future__ import annotations

from pathlib import Path

import pytest

from engines.agents.rag.catalog import KnowledgeBaseSpec
from engines.agents.rag.config import load_rag_config
from engines.agents.rag.indexer import RagIndexer

pytestmark = [pytest.mark.unit]


class _Document:
    def __init__(self, document_id: str) -> None:
        self.document_id = document_id


class _Knowledge:
    def __init__(self) -> None:
        self.documents: dict[str, list] = {}
        self.deleted: list[str] = []

    async def list_documents(self):
        return [_Document(document_id) for document_id in self.documents]

    async def delete_document(self, document_id: str) -> None:
        self.deleted.append(document_id)
        self.documents.pop(document_id, None)

    async def insert_document(self, chunks, document_id: str, document_metadata: dict) -> None:
        self.documents[document_id] = chunks


def _base(tmp_path: Path, name: str = "product_manuals") -> KnowledgeBaseSpec:
    return KnowledgeBaseSpec(name, "产品资料", tmp_path / name, True)


@pytest.mark.asyncio
async def test_index_skips_unchanged_file(tmp_path, monkeypatch):
    data = tmp_path / "product_manuals"
    data.mkdir()
    (data / "reset.md").write_text("# 恢复\n\n长按 3 秒。\n", encoding="utf-8")
    config = load_rag_config(
        {"DASHSCOPE_API_KEY": "sk-test", "KNOWLEDGE_ASSISTANT_RAG_INDEX_DIR": str(tmp_path / "index")}
    )
    knowledge = _Knowledge()
    indexer = RagIndexer(config, _base(tmp_path), knowledge)

    assert await indexer.ensure_index() == 1
    assert await indexer.ensure_index() == 0
    assert knowledge.deleted == []


@pytest.mark.asyncio
async def test_index_removes_deleted_file(tmp_path):
    data = tmp_path / "product_manuals"
    data.mkdir()
    path = data / "reset.md"
    path.write_text("# 恢复\n\n长按 3 秒。\n", encoding="utf-8")
    config = load_rag_config(
        {"DASHSCOPE_API_KEY": "sk-test", "KNOWLEDGE_ASSISTANT_RAG_INDEX_DIR": str(tmp_path / "index")}
    )
    knowledge = _Knowledge()
    indexer = RagIndexer(config, _base(tmp_path), knowledge)
    await indexer.ensure_index()
    path.unlink()

    assert await indexer.ensure_index() == 0
    assert knowledge.documents == {}
    assert knowledge.deleted
