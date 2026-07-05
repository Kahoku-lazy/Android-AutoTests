"""Vector document store backed by ChromaDB — used by KnowledgeBaseSearchTool."""
import os
import logging
from pathlib import Path
from typing import Optional

logger = logging.getLogger('rag')

# Lazy imports — ChromaDB is optional
_chroma_client = None
_collection = None


def _get_collection():
    """Get or create the ChromaDB collection."""
    global _chroma_client, _collection
    if _collection is not None:
        return _collection
    try:
        import chromadb
        persist_dir = Path(__file__).resolve().parent.parent.parent / 'data' / 'chromadb'
        persist_dir.mkdir(parents=True, exist_ok=True)
        _chroma_client = chromadb.PersistentClient(path=str(persist_dir))
        _collection = _chroma_client.get_or_create_collection(
            name="project_knowledge",
            metadata={"description": "Android-AutoTests project knowledge base"},
        )
        logger.info(f'ChromaDB collection loaded: {_collection.count()} documents')
        return _collection
    except Exception as e:
        logger.warning(f'ChromaDB unavailable: {e}')
        return None


def add_documents(docs: list[dict]) -> int:
    """Add documents to the vector store.

    Each doc: {"id": str, "content": str, "metadata": dict}
    Returns the number of documents added.
    """
    col = _get_collection()
    if col is None:
        return 0
    ids = [d.get("id", str(hash(d["content"]))) for d in docs]
    contents = [d["content"] for d in docs]
    metadatas = [d.get("metadata", {}) for d in docs]
    col.add(ids=ids, documents=contents, metadatas=metadatas)
    logger.info(f'Added {len(docs)} documents to knowledge base')
    return len(docs)


def search(query: str, top_k: int = 5) -> list[dict]:
    """Search the knowledge base by natural language query.

    Returns list of {"content": str, "metadata": dict, "score": float}.
    Returns empty list quickly if ChromaDB or its embedding model is unavailable.
    """
    col = _get_collection()
    if col is None:
        return []
    if col.count() == 0:
        logger.info('Knowledge base is empty, skipping search')
        return []
    try:
        results = col.query(query_texts=[query], n_results=top_k)
    except Exception as e:
        logger.warning(f'Knowledge base query failed: {e}')
        return []
    items = []
    if results and results.get('documents') and results['documents'][0]:
        for i, doc in enumerate(results['documents'][0]):
            meta = results['metadatas'][0][i] if results.get('metadatas') and results['metadatas'][0] else {}
            dist = results['distances'][0][i] if results.get('distances') and results['distances'][0] else 0
            items.append({"content": doc, "metadata": meta, "score": float(dist)})
    return items


def clear_collection():
    """Delete all documents from the collection."""
    col = _get_collection()
    if col:
        try:
            _chroma_client.delete_collection("project_knowledge")
            global _collection
            _collection = None
            logger.info('Knowledge base cleared')
        except Exception:
            pass
