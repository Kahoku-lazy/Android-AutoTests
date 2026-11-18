"""report-generator HTTP routes — endpoints under /api/reports/*.

列表是已生成报告的台账（SOP + 智能体两来源），只读聚合走 report_inventory。
旧 csv/md 文件下载/查看端点已随旧执行引擎遗产退役。

成功响应统一走全局 `{status, data}` 信封（`shared/renderers.EnvelopeJSONRenderer`）。
"""

from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.report_generator.report_inventory import build_report_inventory

REPORT_TAG = "reports"

LIST_PARAMETERS = [
    OpenApiParameter(
        "source", OpenApiTypes.STR, OpenApiParameter.QUERY, description="来源过滤：sop / agent"
    ),
    OpenApiParameter(
        "keyword",
        OpenApiTypes.STR,
        OpenApiParameter.QUERY,
        description="关键字：用例名称 / 任务 ID / 助手名称 / 助手编号",
    ),
    OpenApiParameter(
        "start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="起始日期"
    ),
    OpenApiParameter("end_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="结束日期"),
]


class ReportListAPIView(APIView):
    """GET /api/reports — 当前用户可见的已生成报告台账 / 报告数量统计。"""

    @extend_schema(
        tags=[REPORT_TAG],
        operation_id="report_list",
        parameters=LIST_PARAMETERS,
        responses=OpenApiTypes.OBJECT,
    )
    def get(self, request):
        query = request.query_params
        return Response(
            build_report_inventory(
                getattr(request, "user_id", None),
                source=(query.get("source") or "").strip(),
                keyword=(query.get("keyword") or "").strip(),
                start_date=(query.get("start_date") or "").strip(),
                end_date=(query.get("end_date") or "").strip(),
            )
        )
