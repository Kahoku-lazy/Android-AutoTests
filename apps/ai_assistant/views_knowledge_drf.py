"""ai-assistant DRF views — 知识库（磁盘目录 data/rag_datas + RAG 索引）。

GET  /api/ai/knowledge/status            知识库状态（已索引文档数/集合名）
GET  /api/ai/knowledge/documents         data/rag_datas 文件列表
GET  /api/ai/knowledge/documents/preview 预览（md/txt 原文；docx/pdf 旁路转 md）
POST /api/ai/knowledge/reindex           重新索引 data/rag_datas/**/*.md
POST /api/ai/knowledge/documents/add     上传文件到 data/rag_datas
"""

import logging

from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from . import api, kb_files

logger = logging.getLogger("ai_assistant")


class KnowledgeStatusAPIView(APIView):
    """GET /api/ai/knowledge/status — 知识库状态。"""

    def get(self, request):
        return Response(
            {
                "doc_count": api.get_kb_doc_count(),
                "db_size_bytes": 0,
                "db_size_mb": 0.0,
                "collection_name": "project_knowledge",
                "reindex": {
                    "running": False,
                    "last_indexed": None,
                    "message": "",
                },
            }
        )


class KnowledgeDocumentsAPIView(APIView):
    """GET /api/ai/knowledge/documents — data/rag_datas 文件列表。"""

    def get(self, request):
        documents = api.list_kb_documents()
        return Response({"documents": documents, "total": len(documents)})


class KnowledgePreviewAPIView(APIView):
    """GET /api/ai/knowledge/documents/preview?path=相对路径 — 预览文档。"""

    def get(self, request):
        rel = (request.query_params.get("path") or "").strip()
        if not rel:
            raise ValidationError("缺少文件路径")
        try:
            return Response(kb_files.preview_document(rel))
        except kb_files.KbFileError as exc:
            msg = str(exc)
            if "找不到" in msg:
                raise NotFound(msg) from exc
            raise ValidationError(msg) from exc


class KnowledgeReindexAPIView(APIView):
    """POST /api/ai/knowledge/reindex — 重新索引 data/rag_datas。"""

    def post(self, request):
        result = api.reindex_knowledge()
        indexed = result.get("indexed") or []
        failed = result.get("failed") or []
        message = f"已索引 {len(indexed)} 个文档"
        if failed:
            message += f"，失败 {len(failed)} 个"
        return Response({"message": message, "indexed": indexed, "failed": failed})


class KnowledgeAddDocAPIView(APIView):
    """POST /api/ai/knowledge/documents/add — 上传到 data/rag_datas。"""

    def post(self, request):
        uploaded = request.FILES.get("file")
        if not uploaded:
            raise ValidationError("请选择要导入的文件")
        subdir = (request.data.get("subdir") or "").strip()
        content = uploaded.read()
        try:
            saved = kb_files.save_upload(uploaded.name, content, subdir)
        except kb_files.KbFileError as exc:
            raise ValidationError(str(exc)) from exc
        except OSError:
            logger.exception("知识库文档写入失败")
            raise ValidationError("文档保存失败") from None
        return Response(saved)
