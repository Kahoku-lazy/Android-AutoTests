"""平台智能体报告接口：列表与按名读取。View 只分发，逻辑在 reports.py。

信封由全局渲染器统一包一层 `{status, data}`，View 只返回负载本体。
"""

from __future__ import annotations

from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from . import reports


class AgentReportListView(APIView):
    """GET /api/ai/agent-reports/：最近的平台运行报告。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request) -> Response:
        """返回报告列表，新的在前。

        Args:
            request: DRF 请求，查询参数 limit 为条数上限。

        Returns:
            含 reports 列表的负载。

        Raises:
            ValidationError: limit 不是整数。
        """
        limit = request.query_params.get("limit") or ""
        try:
            limit_value = int(limit) if limit else 50
        except (TypeError, ValueError) as exc:
            raise ValidationError("limit 必须是整数") from exc
        return Response({"reports": reports.list_reports(limit=limit_value)})


class AgentReportDetailView(APIView):
    """GET /api/ai/agent-reports/<run>/<name>/：读取一份报告。"""

    permission_classes = [IsAuthenticated]

    def get(self, request: Request, run: str, name: str) -> Response:
        """返回报告正文。

        Args:
            request: DRF 请求。
            run: 运行目录名。
            name: 报告文件名。

        Returns:
            含 report（run / name / content）的负载。

        Raises:
            ValidationError: 路径不在白名单内。
            NotFound: 文件不存在。
        """
        del request
        try:
            filename, content = reports.read_report(run, name)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        except FileNotFoundError as exc:
            raise NotFound(str(exc)) from exc
        return Response({"report": {"run": run, "name": filename, "content": content}})
