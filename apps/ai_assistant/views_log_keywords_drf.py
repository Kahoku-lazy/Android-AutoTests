"""日志关键词目录（JWT 管理面）：当前支持筛选的关键词 → 功能模块 / 功能点。

GET /api/ai/log-keywords/   登录可读：对照表全量（关键词 → 功能点）+ 计数 + 取值来源 + 更新时间

只读：不经内部令牌网关 `/api/ai/tools/`，不写库、不写文件、不启停采集。
"""

from __future__ import annotations

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from . import log_keywords


class LogKeywordCatalogAPIView(APIView):
    """GET /api/ai/log-keywords/ — 关键词对照表（只读，登录可读）。"""

    @extend_schema(responses=OpenApiTypes.OBJECT)
    def get(self, request):
        return Response(log_keywords.collect_keywords())
