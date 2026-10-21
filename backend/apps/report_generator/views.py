"""report-generator HTTP routes — endpoints under /api/reports/*.

列表只读聚合 task_list.Task；run/cases 详情仍为空壳。
File download/view still read LOG_DIR if files exist.

成功响应统一走全局 `{status, data}` 信封（`shared/renderers.EnvelopeJSONRenderer`）；
文件下载端点保持 `FileResponse` 附件语义，不套 JSON 信封。
"""

from pathlib import Path

from django.conf import settings
from django.http import FileResponse
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.apps.task_list.task_reports import build_report_list, parse_chart_range

REPORT_TAG = "reports"

LIST_PARAMETERS = [
    OpenApiParameter(
        "chart_range", OpenApiTypes.STR, OpenApiParameter.QUERY, description="趋势天数"
    ),
    OpenApiParameter(
        "start_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="起始日期"
    ),
    OpenApiParameter("end_date", OpenApiTypes.DATE, OpenApiParameter.QUERY, description="结束日期"),
    OpenApiParameter(
        "run_id", OpenApiTypes.STR, OpenApiParameter.QUERY, description="按 run_id 过滤"
    ),
    OpenApiParameter(
        "task_name", OpenApiTypes.STR, OpenApiParameter.QUERY, description="按任务名过滤"
    ),
    OpenApiParameter(
        "device_serial", OpenApiTypes.STR, OpenApiParameter.QUERY, description="按设备序列号过滤"
    ),
    OpenApiParameter(
        "creator", OpenApiTypes.STR, OpenApiParameter.QUERY, description="按创建人过滤"
    ),
]


class ReportListAPIView(APIView):
    """GET /api/reports — 当前用户可见的助手任务卡列表 / KPI / 趋势。"""

    @extend_schema(
        tags=[REPORT_TAG],
        operation_id="report_list",
        parameters=LIST_PARAMETERS,
        responses=OpenApiTypes.OBJECT,
    )
    def get(self, request):
        query = request.query_params
        return Response(
            build_report_list(
                getattr(request, "user_id", None),
                range_days=parse_chart_range(query.get("chart_range")),
                start_date=(query.get("start_date") or "").strip(),
                end_date=(query.get("end_date") or "").strip(),
                run_id=(query.get("run_id") or "").strip(),
                task_name=(query.get("task_name") or "").strip(),
                device_serial=(query.get("device_serial") or "").strip(),
                creator=(query.get("creator") or "").strip(),
            )
        )


class CaseBreakdownAPIView(APIView):
    """GET /api/reports/cases — empty groups after execution engine removal."""

    @extend_schema(
        tags=[REPORT_TAG],
        operation_id="report_case_breakdown",
        parameters=[
            OpenApiParameter(
                "result",
                OpenApiTypes.STR,
                OpenApiParameter.QUERY,
                required=True,
                enum=["pass", "fail"],
            )
        ],
        responses={200: OpenApiTypes.OBJECT, 400: OpenApiTypes.OBJECT},
    )
    def get(self, request):
        result_type = (request.query_params.get("result") or "").strip().lower()
        if result_type not in ("pass", "fail"):
            raise ValidationError("result 必须为 pass 或 fail")

        payload = {
            "result_type": result_type,
            "total": 0,
            "case_count": 0,
            "groups": [],
        }
        if result_type == "fail":
            payload["bug_summary"] = {}
        return Response(payload)


class RunReportAPIView(APIView):
    """GET /api/reports/run/{run_id} — runs no longer exist."""

    @extend_schema(
        tags=[REPORT_TAG], operation_id="report_run_detail", responses=OpenApiTypes.OBJECT
    )
    def get(self, request, run_id):
        raise NotFound("run not found")


class ReportDownloadAPIView(APIView):
    """GET /api/reports/{filename} — Download report file."""

    @extend_schema(
        tags=[REPORT_TAG],
        operation_id="report_download",
        responses={
            (200, "application/octet-stream"): OpenApiTypes.BINARY,
            404: OpenApiTypes.OBJECT,
        },
    )
    def get(self, request, filename):
        safe_name = Path(filename).name
        fp = settings.LOG_DIR / safe_name
        if not fp.exists():
            raise NotFound("not found")
        suffix = fp.suffix.lower()
        mt = (
            "text/csv" if suffix == ".csv" else "text/markdown" if suffix == ".md" else "text/plain"
        )
        response = FileResponse(open(str(fp), "rb"), content_type=mt)
        response["Content-Disposition"] = f'attachment; filename="{safe_name}"'
        return response


class ReportContentAPIView(APIView):
    """GET /api/reports/{filename}/content — Return file content for inline viewing."""

    @extend_schema(
        tags=[REPORT_TAG],
        operation_id="report_content",
        responses={200: OpenApiTypes.OBJECT, 404: OpenApiTypes.OBJECT},
    )
    def get(self, request, filename):
        safe_name = Path(filename).name
        fp = settings.LOG_DIR / safe_name
        if not fp.exists():
            raise NotFound("not found")

        try:
            content = fp.read_text(encoding="utf-8-sig")
        except Exception:
            try:
                content = fp.read_text(encoding="utf-8")
            except Exception:
                content = fp.read_text(encoding="latin-1")

        suffix = fp.suffix.lower()
        ftype = "csv" if suffix == ".csv" else "md" if suffix == ".md" else "log"

        rows = []
        if suffix == ".csv":
            lines = content.strip().split("\n")
            if lines:
                headers = [h.strip() for h in lines[0].split(",")]
                for line in lines[1:]:
                    cols = [c.strip() for c in line.split(",")]
                    if len(cols) == len(headers):
                        rows.append(dict(zip(headers, cols)))

        return Response(
            {
                "name": safe_name,
                "type": ftype,
                "size": fp.stat().st_size,
                "content": content,
                "rows": rows,
                "headers": [h.strip() for h in content.split("\n")[0].split(",")]
                if suffix == ".csv" and content
                else [],
            }
        )
