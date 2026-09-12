"""知识库（RAG）服务 — 基于 AgentScope rag 模块 + chromadb 本地向量库。

数据源：data/rag_datas/**/*.md（Markdown 文档）。
嵌入模型：ollama（本地）或 openai 兼容 API，经环境变量切换：
  EMBEDDING_PROVIDER   ollama | openai（默认 ollama）
  EMBEDDING_MODEL      模型名（默认 nomic-embed-text）
  EMBEDDING_API_KEY    openai 兼容 API key（仅 openai）
  EMBEDDING_BASE_URL   openai 兼容 base_url 或 ollama host（可空）
  EMBEDDING_DIMENSIONS 向量维度（可空）

对外出口（同步函数，内部 asyncio.run）：search / kb_doc_count / index_rag_directory。
"""

from __future__ import annotations

import asyncio
import threading

from pathlib import Path

import chromadb

from agentscope.message import TextBlock
from agentscope.rag import (
    Chunk,
    DocumentSummary,
    VectorRecord,
    VectorSearchResult,
    VectorStoreBase,
)

# ── 向量库：chromadb 实现的 VectorStoreBase ──

_VECTOR_DIR = "data/rag_vector"
_COLLECTION = "project_knowledge"  # chromadb collection name 需 ≥3 字符且仅 [a-zA-Z0-9._-]


def _safe_meta(meta: dict) -> dict:
    """chromadb metadata 仅接受 str/int/float/bool，过滤 None 与其他类型。"""
    return {
        k: v
        for k, v in (meta or {}).items()
        if isinstance(v, (str, int, float, bool)) and v is not None
    }


def _chunk_text(chunk: Chunk) -> str:
    content = chunk.content
    return content.text if isinstance(content, TextBlock) else str(content)


class ChromaVectorStore(VectorStoreBase):
    """chromadb 本地持久化向量库，适配 AgentScope VectorStoreBase。"""

    def __init__(self, path: str = _VECTOR_DIR):
        self._client = chromadb.PersistentClient(path=path)

    def _col(self, name: str):
        return self._client.get_or_create_collection(name)

    async def create_collection(self, name: str, dimensions: int) -> None:
        self._client.get_or_create_collection(name)

    async def delete_collection(self, name: str) -> None:
        try:
            self._client.delete_collection(name)
        except Exception:
            pass

    async def has_collection(self, name: str) -> bool:
        try:
            self._client.get_collection(name)
            return True
        except Exception:
            return False

    async def insert(self, collection: str, records: list[VectorRecord]) -> None:
        if not records:
            return
        col = self._col(collection)
        ids, embeddings, documents, metadatas = [], [], [], []
        for r in records:
            ids.append(f"{r.document_id}:{r.chunk.chunk_index}")
            embeddings.append(r.vector)
            documents.append(_chunk_text(r.chunk))
            metadatas.append(
                _safe_meta(
                    {
                        "document_id": r.document_id,
                        "chunk_index": r.chunk.chunk_index,
                        "source": r.chunk.source,
                        **r.chunk.metadata,
                    }
                )
            )
        col.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)

    async def delete(self, collection: str, document_id: str) -> None:
        col = self._col(collection)
        col.delete(where={"document_id": document_id})

    async def search(
        self,
        collection: str,
        query_vector: list[float],
        top_k: int = 5,
        metadata_filter: dict | None = None,
    ) -> list[VectorSearchResult]:
        col = self._col(collection)
        res = col.query(
            query_embeddings=[query_vector],
            n_results=top_k,
            where=metadata_filter or None,
        )
        ids = (res.get("ids") or [[]])[0]
        docs = (res.get("documents") or [[]])[0]
        metas = (res.get("metadatas") or [[]])[0]
        dists = (res.get("distances") or [[]])[0]
        results: list[VectorSearchResult] = []
        for i, rid in enumerate(ids):
            meta = metas[i] or {}
            doc_id = str(meta.get("document_id", ""))
            chunk_index = int(meta.get("chunk_index", 0))
            source = str(meta.get("source", ""))
            chunk = Chunk(
                content=TextBlock(text=docs[i] or ""),
                source=source,
                chunk_index=chunk_index,
                total_chunks=0,
                metadata={
                    k: v
                    for k, v in meta.items()
                    if k not in ("document_id", "chunk_index", "source")
                },
            )
            # chromadb 距离越小越近；AgentScope score 越大越相关 → 取负
            score = -float(dists[i]) if dists else 0.0
            results.append(VectorSearchResult(score=score, document_id=doc_id, chunk=chunk))
        return results

    async def list_documents(
        self,
        collection: str,
        metadata_filter: dict | None = None,
    ) -> list[DocumentSummary]:
        col = self._col(collection)
        data = col.get(where=metadata_filter or None)
        agg: dict[str, dict] = {}
        for meta in data.get("metadatas") or []:
            meta = meta or {}
            doc_id = str(meta.get("document_id", ""))
            if not doc_id:
                continue
            if doc_id not in agg:
                agg[doc_id] = {"source": str(meta.get("source", "")), "chunk_count": 0, "metadata": meta}
            agg[doc_id]["chunk_count"] += 1
        return [
            DocumentSummary(
                document_id=doc_id,
                source=v["source"],
                chunk_count=v["chunk_count"],
                metadata=v["metadata"],
            )
            for doc_id, v in agg.items()
        ]

    async def list_chunks(
        self,
        collection: str,
        document_id: str,
        *,
        offset: int = 0,
        limit: int = 30,
        metadata_filter: dict | None = None,
    ) -> list[Chunk]:
        col = self._col(collection)
        where = {**(metadata_filter or {}), "document_id": document_id}
        data = col.get(where=where)
        chunks: list[Chunk] = []
        for i, meta in enumerate(data.get("metadatas") or []):
            meta = meta or {}
            if not (offset <= int(meta.get("chunk_index", 0)) < offset + limit):
                continue
            chunks.append(
                Chunk(
                    content=TextBlock(text=(data.get("documents") or [])[i] or ""),
                    source=str(meta.get("source", "")),
                    chunk_index=int(meta.get("chunk_index", 0)),
                    total_chunks=0,
                    metadata={k: v for k, v in meta.items() if k not in ("document_id", "chunk_index", "source")},
                )
            )
        chunks.sort(key=lambda c: c.chunk_index)
        return chunks


# ── 嵌入模型 ──


def _embedding_config() -> dict:
    from django.conf import settings

    dims = settings.EMBEDDING_DIMENSIONS
    return {
        "provider": (settings.EMBEDDING_PROVIDER or "ollama").strip().lower(),
        "model": (settings.EMBEDDING_MODEL or "nomic-embed-text").strip(),
        "api_key": (settings.EMBEDDING_API_KEY or "").strip(),
        "base_url": (settings.EMBEDDING_BASE_URL or "").strip(),
        "dimensions": int(dims) if dims else None,
    }


def build_embedding_model():
    """按 provider 构建嵌入模型（ollama / openai 兼容 / dashscope）。"""
    cfg = _embedding_config()
    if cfg["provider"] == "ollama":
        from agentscope.credential import OllamaCredential
        from agentscope.embedding import OllamaEmbeddingModel

        return OllamaEmbeddingModel(
            credential=OllamaCredential(host=cfg["base_url"] or None),
            model=cfg["model"],
            dimensions=cfg["dimensions"] or 768,  # nomic-embed-text 默认 768 维
        )
    if cfg["provider"] == "dashscope":
        from agentscope.credential import DashScopeCredential
        from agentscope.embedding import DashScopeEmbeddingModel

        return DashScopeEmbeddingModel(
            credential=DashScopeCredential(api_key=cfg["api_key"]),
            model=cfg["model"],
            dimensions=cfg["dimensions"] or 1024,  # text-embedding-v4 默认 1024 维
        )
    from agentscope.credential import OpenAICredential
    from agentscope.embedding import OpenAIEmbeddingModel

    return OpenAIEmbeddingModel(
        credential=OpenAICredential(api_key=cfg["api_key"], base_url=cfg["base_url"] or None),
        model=cfg["model"],
        dimensions=cfg["dimensions"],
    )


# ── KnowledgeBase 单例 ──

_kb = None
_kb_lock = threading.Lock()


def get_knowledge_base():
    """返回全局唯一的 KnowledgeBase（懒加载，线程安全）。"""
    global _kb
    if _kb is None:
        with _kb_lock:
            if _kb is None:
                from agentscope.rag import KnowledgeBase

                _kb = KnowledgeBase(
                    name="project_knowledge",
                    description="项目业务知识库（data/rag_datas 下的 Markdown 文档，如 GoveeHome APP 功能说明）",
                    embedding_model=build_embedding_model(),
                    vector_store=ChromaVectorStore(),
                    collection=_COLLECTION,
                )
    return _kb


# ── 对外操作 ──


async def _index_rag_directory(dir_path: str = "data/rag_datas") -> dict:
    from agentscope.rag import ApproxTokenChunker, TextParser

    kb = get_knowledge_base()
    parser = TextParser()
    chunker = ApproxTokenChunker(
        parameters=ApproxTokenChunker.Parameters(chunk_size=256, overlap=32)
    )
    indexed, failed = [], []
    for path in Path(dir_path).rglob("*.md"):
        rel = str(path)
        try:
            sections = await parser.parse(file=str(path), filename=path.name)
            chunks = await chunker.chunk(sections)
            doc_id = await kb.insert_document(chunks, document_metadata={"source": rel})
            indexed.append({"doc_id": doc_id, "source": rel})
        except Exception as e:  # noqa: BLE001
            failed.append({"source": rel, "error": str(e)})
    return {"indexed": indexed, "failed": failed}


async def _search(query: str, top_k: int = 5) -> list[dict]:
    kb = get_knowledge_base()
    results = await kb.search(queries=[query], top_k=top_k)
    return [
        {
            "content": _chunk_text(r.chunk),
            "source": r.chunk.source,
            "score": r.score,
            "document_id": r.document_id,
        }
        for r in results
    ]


async def _kb_doc_count() -> int:
    kb = get_knowledge_base()
    return len(await kb.list_documents())


_indexed = False
_index_lock = threading.Lock()


def _ensure_indexed() -> None:
    """首次检索/计数前，若向量库为空则自动索引 data/rag_datas（懒加载，免手动 reindex）。"""
    global _indexed
    if _indexed:
        return
    with _index_lock:
        if _indexed:
            return
        try:
            if asyncio.run(_kb_doc_count()) == 0:
                asyncio.run(_index_rag_directory())
        finally:
            _indexed = True


def search(query: str, top_k: int = 5) -> list[dict]:
    """同步检索入口。"""
    _ensure_indexed()
    return asyncio.run(_search(query, top_k))


def kb_doc_count() -> int:
    """同步文档数入口。"""
    _ensure_indexed()
    return asyncio.run(_kb_doc_count())


def index_rag_directory(dir_path: str = "data/rag_datas") -> dict:
    """同步索引入口。"""
    return asyncio.run(_index_rag_directory(dir_path))


async def _list_documents() -> list[dict]:
    kb = get_knowledge_base()
    summaries = await kb.list_documents()
    return [
        {
            "id": s.document_id,
            "name": s.source,
            "chunk_count": s.chunk_count,
        }
        for s in summaries
    ]


def list_documents() -> list[dict]:
    """同步文档列表入口。"""
    _ensure_indexed()
    return asyncio.run(_list_documents())
