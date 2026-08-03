"""ChromaDB vector store — Django-managed knowledge base service.

Migrated from agentscope_service/rag/document_store.py + loader.py.
This is now the SINGLE owner of ChromaDB — AgentScope never touches it directly.
"""

import logging
import time

from pathlib import Path

from django.conf import settings

logger = logging.getLogger("ai_assistant.rag")

_chroma_client = None
_collection = None

# Document cache
_cached_docs: list[dict] | None = None
_cache_mtime: float = 0
_cache_fill_time: float = 0
_CACHE_TTL = 60  # seconds


def _get_collection():
    """Get or create the ChromaDB collection (lazy init)."""
    global _chroma_client, _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb

        persist_dir = Path(settings.BASE_DIR) / "data" / "chromadb"
        persist_dir.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(persist_dir))
        _collection = _chroma_client.get_or_create_collection(
            name="project_knowledge",
            metadata={"description": "Android-AutoTests project knowledge base"},
        )
        logger.info("ChromaDB collection loaded: %s documents", _collection.count())
        return _collection
    except Exception as e:
        logger.warning("ChromaDB unavailable: %s", e)
        return None


def add_documents(docs: list[dict]) -> int:
    """Add documents to the vector store. Returns count added."""
    col = _get_collection()
    if col is None:
        return 0
    ids = [d.get("id", str(hash(d["content"]))) for d in docs]
    contents = [d["content"] for d in docs]
    metadatas = [d.get("metadata", {}) for d in docs]
    col.add(ids=ids, documents=contents, metadatas=metadatas)
    logger.info("Added %d documents to knowledge base", len(docs))
    return len(docs)


def search(query: str, top_k: int = 5, sources: list[str] | None = None) -> list[dict]:
    """Search the knowledge base by natural language query.

    Args:
        query: Natural language search query.
        top_k: Number of results to return.
        sources: Optional list of document IDs to restrict search to.

    Returns list of {"content": str, "metadata": dict, "score": float}.
    """
    col = _get_collection()
    if col is None:
        return []
    if col.count() == 0:
        logger.info("Knowledge base is empty, skipping search")
        return []

    where_filter = None
    if sources:
        if len(sources) == 1:
            where_filter = {"source": sources[0]}
        else:
            where_filter = {"source": {"$in": list(sources)}}

    try:
        kwargs = {"query_texts": [query], "n_results": top_k}
        if where_filter:
            kwargs["where"] = where_filter
        results = col.query(**kwargs)
    except Exception as e:
        if where_filter and sources:
            logger.debug("ChromaDB where-filter failed (%s), falling back to post-filter", e)
            try:
                results = col.query(query_texts=[query], n_results=top_k * 3)
            except Exception as e2:
                logger.warning("Knowledge base query failed: %s", e2)
                return []
        else:
            logger.warning("Knowledge base query failed: %s", e)
            return []

    items = []
    if results and results.get("documents") and results["documents"][0]:
        for i, doc in enumerate(results["documents"][0]):
            meta = (
                results["metadatas"][0][i]
                if results.get("metadatas") and results["metadatas"][0]
                else {}
            )
            dist = (
                results["distances"][0][i]
                if results.get("distances") and results["distances"][0]
                else 0
            )

            if sources and where_filter is None:
                doc_source = meta.get("source", "")
                if doc_source not in sources:
                    continue

            items.append({"content": doc, "metadata": meta, "score": float(dist)})
            if len(items) >= top_k:
                break

    return items


def clear_collection():
    """Delete all documents from the collection."""
    global _collection
    col = _get_collection()
    if col:
        try:
            _chroma_client.delete_collection("project_knowledge")
            _collection = None
            logger.info("Knowledge base cleared")
        except Exception:
            logger.exception("Failed to clear knowledge base collection")


# ── Document loading ──


def _get_root() -> Path:
    """Lazy-resolve project root from Django settings or filesystem."""
    try:
        return Path(settings.BASE_DIR)
    except Exception:
        # Fallback: navigate up from this file's location
        return Path(__file__).resolve().parent.parent.parent.parent


def _load_project_docs() -> list[dict]:
    """Scan dev_docs/ for markdown files and load them as knowledge docs."""
    docs = []
    doc_dir = _get_root() / "dev_docs"
    if not doc_dir.exists():
        return docs

    for md_file in doc_dir.rglob("*.md"):
        try:
            content = md_file.read_text(encoding="utf-8", errors="replace")
            if len(content) < 50:
                continue
            rel_path = str(md_file.relative_to(doc_dir))
            docs.append(
                {
                    "id": f"doc:{rel_path}",
                    "content": content[:4000],
                    "metadata": {
                        "source": rel_path,
                        "type": "project_doc",
                        "path": str(md_file),
                    },
                }
            )
        except Exception:
            logger.exception("Failed to load document: %s", md_file)
    return docs


def _load_step_type_reference() -> list[dict]:
    """Generate reference documentation for all step types."""
    from models.step_types import UI_LABELS, StepType

    lines = ["# 测试步骤类型参考\n"]
    for st in StepType:
        lines.append(f"## {st.value}")
        lines.append(f"- 中文名称: {UI_LABELS.get(st, '')}")
        lines.append(f"- 类型标识: `{st.value}`")
        lines.append("")

    lines.append("## 步骤结构字段")
    lines.append("- `type`: 步骤类型（必填）")
    lines.append("- `xpath`: 主要 XPath 定位表达式（必填）")
    lines.append("- `xpath2`: 备用 XPath（保留字段）")
    lines.append("- `timeout`: 超时时间，秒（默认 10）")
    lines.append("- `expected_text`: 期望文本（verify_text / poll_text）")
    lines.append("- `index`: wait / poll_text 的轮询间隔秒数")
    lines.append("- `description`: 步骤描述（必填）")

    content = "\n".join(lines)
    return [
        {
            "id": "ref:step_types",
            "content": content,
            "metadata": {"source": "generated", "type": "reference", "topic": "step_types"},
        }
    ]


def load_all_documents(force: bool = False) -> list[dict]:
    """Load all knowledge base documents with file-mtime-based caching."""
    global _cached_docs, _cache_mtime, _cache_fill_time

    now = time.monotonic()
    if not force and _cached_docs is not None:
        doc_dir = _get_root() / "dev_docs"
        current_mtime = doc_dir.stat().st_mtime if doc_dir.exists() else 0
        if current_mtime <= _cache_mtime and (now - _cache_fill_time) < _CACHE_TTL:
            return _cached_docs

    docs = []
    docs.extend(_load_project_docs())
    docs.extend(_load_step_type_reference())

    _cached_docs = docs
    _cache_fill_time = now
    doc_dir = _get_root() / "dev_docs"
    _cache_mtime = doc_dir.stat().st_mtime if doc_dir.exists() else 0
    return docs
