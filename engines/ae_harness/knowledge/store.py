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
    def __init__(self, db_path: str | Path) -> None:
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    async def __aenter__(self) -> "SQLiteVectorStore":
        return self

    async def __aexit__(self, exc_type: object, exc_val: object, exc_tb: object) -> None:
        return None

    @contextmanager
    def _connect(self):
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
        with self._connect() as connection:
            connection.execute("DELETE FROM records WHERE collection = ?", (name,))
            connection.execute("DELETE FROM collections WHERE name = ?", (name,))

    async def has_collection(self, name: str) -> bool:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT 1 FROM collections WHERE name = ?",
                (name,),
            ).fetchone()
        return row is not None

    async def insert(self, collection: str, records: list[VectorRecord]) -> None:
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
