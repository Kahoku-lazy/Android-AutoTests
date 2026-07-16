"""Knowledge base management API — ChromaDB status, document list, reindex."""
import json
import threading
from pathlib import Path
from datetime import datetime

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

_reindex_lock = threading.Lock()
_reindex_status = {"running": False, "last_indexed": None, "doc_count": 0, "error": ""}


def _get_kb_stats():
    """Read current knowledge base stats from ChromaDB and file system."""
    from agentscope_service.rag.document_store import _get_collection

    col = _get_collection()
    doc_count = col.count() if col else 0

    chroma_dir = Path(__file__).resolve().parent.parent.parent.parent / "data" / "chromadb"
    db_path = chroma_dir / "chroma.sqlite3"
    db_size = db_path.stat().st_size if db_path.exists() else 0

    return {
        "doc_count": doc_count,
        "db_size_bytes": db_size,
        "db_size_mb": round(db_size / 1024 / 1024, 2),
        "collection_name": "project_knowledge",
    }


def _scan_doc_sources():
    """Scan dev_docs/ for markdown files that would be indexed."""
    from agentscope_service.rag.loader import load_all_documents

    docs = load_all_documents()
    return [
        {
            "id": d["id"],
            "source": d["metadata"].get("source", ""),
            "type": d["metadata"].get("type", ""),
            "size": len(d["content"]),
        }
        for d in docs
    ]


@csrf_exempt
def kb_status(request):
    """GET /api/ai/knowledge/status — index stats + reindex status."""
    stats = _get_kb_stats()
    stats["reindex"] = {
        "running": _reindex_status["running"],
        "last_indexed": _reindex_status["last_indexed"],
        "error": _reindex_status["error"],
    }
    return JsonResponse({"ok": True, "data": stats})


@csrf_exempt
def kb_documents(request):
    """GET /api/ai/knowledge/documents — list all indexable documents."""
    try:
        docs = _scan_doc_sources()
    except Exception as e:
        return JsonResponse({"ok": False, "error": str(e)}, status=500)
    return JsonResponse({"ok": True, "data": {"documents": docs, "total": len(docs)}})


@csrf_exempt
def kb_reindex(request):
    """POST /api/ai/knowledge/reindex — trigger full reindex."""
    if _reindex_status["running"]:
        return JsonResponse({"ok": False, "error": "索引重建已在进行中"}, status=409)

    def _run_reindex():
        global _reindex_status
        with _reindex_lock:
            try:
                _reindex_status["running"] = True
                _reindex_status["error"] = ""

                from agentscope_service.rag.document_store import clear_collection, add_documents
                from agentscope_service.rag.loader import load_all_documents

                clear_collection()
                docs = load_all_documents()
                count = add_documents(docs)
                _reindex_status["doc_count"] = count
                _reindex_status["last_indexed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            except Exception as e:
                _reindex_status["error"] = str(e)
            finally:
                _reindex_status["running"] = False

    t = threading.Thread(target=_run_reindex, daemon=True)
    t.start()
    return JsonResponse({"ok": True, "message": "索引重建已开始"})


@csrf_exempt
def kb_add_document(request):
    """POST /api/ai/knowledge/documents/add — manually add a document."""
    try:
        body = json.loads(request.body) if request.body else {}
    except json.JSONDecodeError:
        return JsonResponse({"ok": False, "error": "无效的 JSON"}, status=400)

    content = body.get("content", "").strip()
    source = body.get("source", "manual")
    if not content:
        return JsonResponse({"ok": False, "error": "文档内容不能为空"}, status=400)

    from agentscope_service.rag.document_store import add_documents

    doc_id = f"manual:{source}:{datetime.now().strftime('%Y%m%d%H%M%S')}"
    add_documents([
        {
            "id": doc_id,
            "content": content,
            "metadata": {"source": source, "type": "manual"},
        }
    ])
    return JsonResponse({"ok": True, "data": {"id": doc_id, "source": source}})
