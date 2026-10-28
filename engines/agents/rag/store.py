"""
python -m 调试路径: engines.agents.rag.store

本模块的业务功能如下：
1. SQLiteVectorStore: AgentScope VectorStoreBase 的本地 SQLite 实现。
2. 支持 create/delete/has_collection、insert/delete、search/list_documents。

只用于小规模本地 RAG（当前 rag_data 为 Markdown 文档）；不依赖外部向量库。
"""

from __future__ import annotations

import json
import math
import sqlite3

from pathlib import Path
from typing import Any

from agentscope.message import TextBlock
from agentscope.rag import (
    Chunk,
    DocumentSummary,
    VectorRecord,
    VectorSearchResult,
    VectorStoreBase,
)


class SQLiteVectorStore(VectorStoreBase):
    """
    基于 SQLite 文件的本地向量库。

    Attributes:
        db_path: SQLite 文件路径。
    """

    def __init__(self, db_path: str | Path) -> None:
        """
        初始化本地向量库。

        Args:
            db_path: SQLite 文件路径；父目录不存在时自动创建。
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        """打开数据库连接。"""
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        return connection

    def _init_db(self) -> None:
        """建表；幂等。"""
        with self._connect() as connection:
            connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS collections (
                    name TEXT PRIMARY KEY,
                    dimensions INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS records (
                    collection TEXT NOT NULL,
                    document_id TEXT NOT NULL,
                    chunk_index INTEGER NOT NULL,
                    source TEXT NOT NULL,
                    total_chunks INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    vector TEXT NOT NULL,
                    PRIMARY KEY (collection, document_id, chunk_index)
                );
                """,
            )

    async def create_collection(self, name: str, dimensions: int) -> None:
        """
        创建集合。

        Args:
            name: 集合名。
            dimensions: 向量维度。

        Raises:
            RuntimeError: 同名集合已存在但维度不同。
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT dimensions FROM collections WHERE name = ?",
                (name,),
            ).fetchone()
            if row is not None:
                if int(row["dimensions"]) != int(dimensions):
                    raise RuntimeError(
                        f"RAG 集合 {name!r} 维度不一致："
                        f"已有 {row['dimensions']}，期望 {dimensions}",
                    )
                return
            connection.execute(
                "INSERT INTO collections (name, dimensions) VALUES (?, ?)",
                (name, dimensions),
            )

    async def delete_collection(self, name: str) -> None:
        """删除集合与其中全部记录。"""
        with self._connect() as connection:
            connection.execute("DELETE FROM records WHERE collection = ?", (name,))
            connection.execute("DELETE FROM collections WHERE name = ?", (name,))

    async def has_collection(self, name: str) -> bool:
        """判断集合是否存在。"""
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM collections WHERE name = ?",
                (name,),
            ).fetchone()
        return row is not None

    async def insert(
        self,
        collection: str,
        records: list[VectorRecord],
    ) -> None:
        """
        插入或覆盖记录。

        Args:
            collection: 集合名。
            records: 带向量的文档块。

        Raises:
            RuntimeError: 集合不存在或向量维度不符。
            ValueError: 非文本块。
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT dimensions FROM collections WHERE name = ?",
                (collection,),
            ).fetchone()
            if row is None:
                raise RuntimeError(f"RAG 集合不存在：{collection!r}")
            dimensions = int(row["dimensions"])
            for record in records:
                if not isinstance(record.chunk.content, TextBlock):
                    raise ValueError("SQLiteVectorStore 只支持文本 chunk")
                if len(record.vector) != dimensions:
                    raise RuntimeError(
                        f"RAG 向量维度不符：期望 {dimensions}，实际 {len(record.vector)}",
                    )
                connection.execute(
                    """
                    INSERT INTO records (
                        collection, document_id, chunk_index, source,
                        total_chunks, content, metadata, vector
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(collection, document_id, chunk_index)
                    DO UPDATE SET
                        source = excluded.source,
                        total_chunks = excluded.total_chunks,
                        content = excluded.content,
                        metadata = excluded.metadata,
                        vector = excluded.vector
                    """,
                    (
                        collection,
                        record.document_id,
                        record.chunk.chunk_index,
                        record.chunk.source,
                        record.chunk.total_chunks,
                        record.chunk.content.text,
                        json.dumps(
                            record.chunk.metadata,
                            ensure_ascii=False,
                            default=str,
                        ),
                        json.dumps(record.vector),
                    ),
                )

    async def delete(self, collection: str, document_id: str) -> None:
        """删除一个文档的全部块。"""
        with self._connect() as connection:
            connection.execute(
                "DELETE FROM records WHERE collection = ? AND document_id = ?",
                (collection, document_id),
            )

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        top_k: int = 5,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[VectorSearchResult]:
        """
        余弦相似度检索。

        Args:
            collection: 集合名。
            query_vector: 查询向量。
            top_k: 返回条数。
            metadata_filter: 必须全部匹配的 metadata 条件。

        Returns:
            按相似度降序的结果。
        """
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM records WHERE collection = ?",
                (collection,),
            ).fetchall()

        results: list[VectorSearchResult] = []
        query_norm = math.sqrt(sum(value * value for value in query_vector))
        if query_norm == 0:
            return []
        for row in rows:
            metadata = json.loads(row["metadata"] or "{}")
            if metadata_filter and any(
                metadata.get(key) != value for key, value in metadata_filter.items()
            ):
                continue
            vector = [float(value) for value in json.loads(row["vector"])]
            norm = math.sqrt(sum(value * value for value in vector))
            if norm == 0:
                continue
            score = sum(left * right for left, right in zip(query_vector, vector, strict=False)) / (
                query_norm * norm
            )
            results.append(
                VectorSearchResult(
                    score=score,
                    document_id=row["document_id"],
                    chunk=Chunk(
                        content=TextBlock(text=row["content"]),
                        source=row["source"],
                        chunk_index=int(row["chunk_index"]),
                        total_chunks=int(row["total_chunks"]),
                        metadata=metadata,
                    ),
                ),
            )
        results.sort(key=lambda item: item.score, reverse=True)
        return results[: max(1, top_k)]

    async def list_documents(
        self,
        collection: str,
        metadata_filter: dict[str, Any] | None = None,
    ) -> list[DocumentSummary]:
        """
        列出一个集合内的文档。

        Args:
            collection: 集合名。
            metadata_filter: 可选的 metadata 过滤。

        Returns:
            每个 document_id 一条摘要。
        """
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM records WHERE collection = ?",
                (collection,),
            ).fetchall()

        documents: dict[str, DocumentSummary] = {}
        for row in rows:
            metadata = json.loads(row["metadata"] or "{}")
            if metadata_filter and any(
                metadata.get(key) != value for key, value in metadata_filter.items()
            ):
                continue
            document_id = row["document_id"]
            existing = documents.get(document_id)
            if existing is None:
                documents[document_id] = DocumentSummary(
                    document_id=document_id,
                    source=row["source"],
                    chunk_count=1,
                    metadata=metadata,
                )
            else:
                existing.chunk_count += 1
        return list(documents.values())
