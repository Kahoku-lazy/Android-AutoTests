"""ai-assistant DRF views — 知识库（后端已移除，接口保留空壳）。

路径与响应形状保持旧契约不变，仅返回空数据：
  GET  /api/ai/knowledge/status          {doc_count:0, db_size_mb:0, reindex:{...}}
  GET  /api/ai/knowledge/documents       {documents:[], total:0}
  POST /api/ai/knowledge/reindex         {message}
  POST /api/ai/knowledge/documents/add   {id, source}
"""

from rest_framework.response import Response
from rest_framework.views import APIView


class KnowledgeStatusAPIView(APIView):
    """GET /api/ai/knowledge/status — 空壳（知识库已移除）。"""

    def get(self, request):
        return Response(
            {
                "doc_count": 0,
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
    """GET /api/ai/knowledge/documents — 空壳（知识库已移除）。"""

    def get(self, request):
        return Response({"documents": [], "total": 0})


class KnowledgeReindexAPIView(APIView):
    """POST /api/ai/knowledge/reindex — 空壳（知识库已移除）。"""

    def post(self, request):
        return Response({"message": "知识库已移除"})


class KnowledgeAddDocAPIView(APIView):
    """POST /api/ai/knowledge/documents/add — 空壳（知识库已移除）。"""

    def post(self, request):
        return Response({"id": "", "source": ""})
