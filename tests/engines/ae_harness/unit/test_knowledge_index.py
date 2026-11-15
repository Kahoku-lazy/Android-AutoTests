"""知识库增量索引：未变化跳过、删除清理与目录缺失。

用替身 KnowledgeBase 承接写入，不联网、不调嵌入模型。
"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from engines.ae_harness.knowledge.config import KnowledgeBaseSpec
from engines.ae_harness.knowledge.indexer import KnowledgeIndexer

pytestmark = [pytest.mark.unit]


class _FakeKnowledge:
    """只记录写入与删除的 KnowledgeBase 替身。"""

    def __init__(self) -> None:
        self.documents: set[str] = set()
        self.inserted: list[str] = []
        self.deleted: list[str] = []

    async def list_documents(self):
        """返回当前已写入的文档摘要。"""
        return [SimpleNamespace(document_id=name) for name in sorted(self.documents)]

    async def insert_document(self, chunks, document_id=None, document_metadata=None):
        """记录一次写入。"""
        self.inserted.append(str(document_id))
        self.documents.add(str(document_id))
        return document_id

    async def delete_document(self, document_id):
        """记录一次删除。"""
        self.deleted.append(document_id)
        self.documents.discard(document_id)


def _indexer(tmp_path, knowledge: _FakeKnowledge) -> KnowledgeIndexer:
    """造一个指向临时资料目录的索引器。

    Args:
        tmp_path: pytest 临时目录。
        knowledge: KnowledgeBase 替身。

    Returns:
        索引器。
    """
    spec = KnowledgeBaseSpec("kb", "测试库", tmp_path / "docs", True)
    spec.data_dir.mkdir(parents=True, exist_ok=True)
    return KnowledgeIndexer(
        spec,
        knowledge,  # type: ignore[arg-type]
        index_dir=tmp_path / "index",
        chunk_size=400,
        chunk_overlap=60,
    )


async def test_unchanged_file_is_skipped(tmp_path):
    """同一文件第二次索引不再写入。"""
    knowledge = _FakeKnowledge()
    indexer = _indexer(tmp_path, knowledge)
    (indexer.spec.data_dir / "a.md").write_text("# 标题\n\n正文内容。\n", encoding="utf-8")

    assert await indexer.ensure_index() == 1
    assert await indexer.ensure_index() == 0
    assert len(knowledge.inserted) == 1


async def test_removed_file_is_deleted(tmp_path):
    """资料目录里删掉的文件会从索引移除。"""
    knowledge = _FakeKnowledge()
    indexer = _indexer(tmp_path, knowledge)
    path = indexer.spec.data_dir / "a.md"
    path.write_text("# 标题\n\n正文内容。\n", encoding="utf-8")
    await indexer.ensure_index()

    path.unlink()
    assert await indexer.ensure_index() == 0
    assert knowledge.deleted == knowledge.inserted


async def test_non_text_files_are_ignored(tmp_path):
    """只索引 .md 与 .txt。"""
    knowledge = _FakeKnowledge()
    indexer = _indexer(tmp_path, knowledge)
    (indexer.spec.data_dir / "a.pdf").write_bytes(b"%PDF-1.4")
    (indexer.spec.data_dir / "b.txt").write_text("纯文本", encoding="utf-8")

    assert await indexer.ensure_index() == 1


async def test_missing_data_dir_raises(tmp_path):
    """资料目录不存在时报错，供上层降级成「检索不可用」。"""
    knowledge = _FakeKnowledge()
    indexer = _indexer(tmp_path, knowledge)
    indexer.spec.data_dir.rmdir()

    with pytest.raises(RuntimeError, match="资料目录不存在"):
        await indexer.ensure_index()
