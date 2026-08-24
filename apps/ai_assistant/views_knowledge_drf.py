"""ai-assistant DRF views — 知识库（Batch 3 迁移）。

路径与方法保持旧契约不变；成功响应原本即 {status, data} 形状，DRF 信封下形状不变：
  GET  /api/ai/knowledge/status          {status, data:{doc_count, db_size_mb, reindex:{...}}}
  GET  /api/ai/knowledge/documents       {status, data:{documents, total}}
  POST /api/ai/knowledge/reindex         {status, message}（DRF 下为 {status, data:{message}}，前端仅读 status）
  POST /api/ai/knowledge/documents/add   {status, data:{id, source}}

Chromadb / 文件扫描逻辑自 knowledge_views.py 迁入，无 ORM 写。
"""

import threading

from datetime import datetime
from pathlib import Path

from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .views_toolbox_drf import Conflict

_reindex_lock = threading.Lock()
_reindex_status = {"running": False, "last_indexed": None, "doc_count": 0, "message": ""}


def _get_kb_stats():
    """Read current knowledge base stats from ChromaDB and file system."""
    from apps.ai_assistant.agent_scope.rag_service import _get_collection

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
    """Scan dev_docs/ for markdown files that would be indexed. Returns metadata only."""
    from apps.ai_assistant.agent_scope.rag_service import load_all_documents

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


class KnowledgeStatusAPIView(APIView):
    """GET /api/ai/knowledge/status — index stats + reindex status."""

    def get(self, request):
        stats = _get_kb_stats()
        stats["reindex"] = {
            "running": _reindex_status["running"],
            "last_indexed": _reindex_status["last_indexed"],
            "message": _reindex_status.get("error") or _reindex_status["message"],
        }
        return Response(stats)


class KnowledgeDocumentsAPIView(APIView):
    """GET /api/ai/knowledge/documents — list all indexable documents."""

    def get(self, request):
        try:
            docs = _scan_doc_sources()
        except Exception as e:
            raise APIException(detail=str(e), code=500)
        return Response({"documents": docs, "total": len(docs)})


class KnowledgeReindexAPIView(APIView):
    """POST /api/ai/knowledge/reindex — trigger full reindex."""

    def post(self, request):
        if _reindex_status["running"]:
            raise Conflict("索引重建已在进行中")

        def _run_reindex():
            global _reindex_status
            with _reindex_lock:
                try:
                    _reindex_status["running"] = True
                    _reindex_status["error"] = ""

                    from apps.ai_assistant.agent_scope.rag_service import (
                        add_documents,
                        clear_collection,
                        load_all_documents,
                    )

                    clear_collection()
                    docs = load_all_documents(force=True)
                    count = add_documents(docs)
                    _reindex_status["doc_count"] = count
                    _reindex_status["last_indexed"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                except Exception as e:
                    _reindex_status["error"] = str(e)
                finally:
                    _reindex_status["running"] = False

        t = threading.Thread(target=_run_reindex, daemon=True)
        t.start()
        return Response({"message": "索引重建已开始"})


class KnowledgeAddDocAPIView(APIView):
    """POST /api/ai/knowledge/documents/add — manually add a document."""

    def post(self, request):
        content = (request.data.get("content") or "").strip()
        source = request.data.get("source", "manual")
        if not content:
            raise ValidationError("文档内容不能为空")

        from apps.ai_assistant.agent_scope.rag_service import add_documents

        doc_id = f"manual:{source}:{datetime.now().strftime('%Y%m%d%H%M%S')}"
        add_documents(
            [
                {
                    "id": doc_id,
                    "content": content,
                    "metadata": {"source": source, "type": "manual"},
                }
            ]
        )
        return Response({"id": doc_id, "source": source})
