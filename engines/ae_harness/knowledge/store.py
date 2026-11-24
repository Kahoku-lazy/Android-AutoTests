"""
文件名: ➡️ store.py 🏁
路径: ➡️ engines/ae_harness/knowledge/store.py 🏁
模块功能：➡️ 知识库本地 SQLite 向量库：集合与文档的建删查，实现 VectorStoreBase 🏁
Python 调试：➡️ python -m engines.ae_harness.knowledge.store 🏁
时间：➡️ 2026-11-24 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-20 🏁
类型: ➡️ 工具模块 🏁
简介说明：➡️
1. SQLiteVectorStore: AgentScope VectorStoreBase 的本地实现，余弦相似度全表扫描。
2. 支持 create/delete/has_collection、insert/delete、search/list_documents。
3. delete 接受可选 metadata_filter，非空时只删 metadata 全部匹配的块。
3. 提供空的异步上下文，调用方统一用 async with 管理生命周期。
🏁
关联模块：➡️
1. 无 Harness 内依赖：只依赖 agentscope 与标准库。
🏁
测试：➡️
1. 暂无
🏁
"""

from __future__ import annotations

import json
import math
import sqlite3

from contextlib import contextmanager
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

__all__ = ["SQLiteVectorStore"]


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

    async def __aenter__(self) -> "SQLiteVectorStore":
        """进入异步上下文；SQLite 按次连接，这里不保留长连接。"""
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        """退出异步上下文；没有需要关闭的长连接。"""
        return None

    @contextmanager
    def _connect(self):
        """
        打开数据库连接，用完即关。

        sqlite3 的连接作上下文管理器只提交事务，不关闭句柄，所以这里单独包一层。

        Yields:
            已设置行工厂的连接。
        """
        connection = sqlite3.connect(str(self.db_path))
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

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
        建一个集合。

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
                if int(row["dimensions"]) != dimensions:
                    raise RuntimeError(
                        f"集合 {name!r} 维度不一致：已存在 {row['dimensions']}，期望 {dimensions}",
                    )
                return
            connection.execute(
                "INSERT INTO collections (name, dimensions) VALUES (?, ?)",
                (name, dimensions),
            )

    async def delete_collection(self, name: str) -> None:
        """
        删除一个集合及其全部记录。

        Args:
            name: 集合名。
        """
        with self._connect() as connection:
            connection.execute("DELETE FROM records WHERE collection = ?", (name,))
            connection.execute("DELETE FROM collections WHERE name = ?", (name,))

    async def has_collection(self, name: str) -> bool:
        """
        判断集合是否存在。

        Args:
            name: 集合名。

        Returns:
            存在为真。
        """
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM collections WHERE name = ?",
                (name,),
            ).fetchone()
        return row is not None

    async def insert(self, collection: str, records: list[VectorRecord]) -> None:
        """
        写入一批文档块。

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
                raise RuntimeError(f"知识库集合不存在：{collection!r}")
            dimensions = int(row["dimensions"])
            for record in records:
                if not isinstance(record.chunk.content, TextBlock):
                    raise ValueError("SQLiteVectorStore 只支持文本块")
                if len(record.vector) != dimensions:
                    raise RuntimeError(
                        f"向量维度不符：期望 {dimensions}，实际 {len(record.vector)}",
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
                        json.dumps(record.chunk.metadata, ensure_ascii=False, default=str),
                        json.dumps(record.vector),
                    ),
                )

    async def delete(
        self,
        collection: str,
        document_id: str,
        metadata_filter: dict[str, Any] | None = None,
    ) -> None:
        """
        删除一个文档的块。

        Args:
            collection: 集合名。
            document_id: 文档编号。
            metadata_filter: 非空时只删 metadata 全部匹配的块；空则删该文档全部块。
        """
        with self._connect() as connection:
            if not metadata_filter:
                connection.execute(
                    "DELETE FROM records WHERE collection = ? AND document_id = ?",
                    (collection, document_id),
                )
                return
            rows = connection.execute(
                "SELECT chunk_index, metadata FROM records WHERE collection = ? AND document_id = ?",
                (collection, document_id),
            ).fetchall()
            matched = [
                int(row["chunk_index"])
                for row in rows
                if all(
                    json.loads(row["metadata"] or "{}").get(key) == value
                    for key, value in metadata_filter.items()
                )
            ]
            for chunk_index in matched:
                connection.execute(
                    "DELETE FROM records WHERE collection = ? AND document_id = ? AND chunk_index = ?",
                    (collection, document_id, chunk_index),
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
            按相似度降序的结果；查询向量为零向量时为空列表。

        Raises:
            RuntimeError: 查询向量与库存向量维度不同。
        """
        with self._connect() as connection:
            rows = connection.execute(
                "SELECT * FROM records WHERE collection = ?",
                (collection,),
            ).fetchall()

        query_norm = math.sqrt(sum(value * value for value in query_vector))
        if query_norm == 0:
            return []
        results: list[VectorSearchResult] = []
        for row in rows:
            metadata = json.loads(row["metadata"] or "{}")
            if metadata_filter and any(
                metadata.get(key) != value for key, value in metadata_filter.items()
            ):
                continue
            vector = [float(value) for value in json.loads(row["vector"])]
            if len(vector) != len(query_vector):
                raise RuntimeError(
                    f"查询向量维度不符：期望 {len(vector)}，实际 {len(query_vector)}",
                )
            norm = math.sqrt(sum(value * value for value in vector))
            if norm == 0:
                continue
            score = sum(left * right for left, right in zip(query_vector, vector, strict=True)) / (
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
