"""ai-assistant URL routing — agents and workflow sessions.

Task endpoints have moved to /api/tasks/ (apps.task_list).
模型不对外：没有模型卡片，也没有直连模型的对话流。
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views_drf import (
    AgentViewSet,
    WorkflowEventsView,
    WorkflowListView,
    WorkflowStreamView,
)
from .views_reports import AgentReportDetailView, AgentReportListView

app_name = "ai"

router = DefaultRouter()
router.register("agents", AgentViewSet, basename="ai_agent")

urlpatterns = [
    path("workflows/", WorkflowListView.as_view(), name="workflow_list"),
    path("workflows/events/", WorkflowEventsView.as_view(), name="workflow_events"),
    path("workflows/<str:key>/stream/", WorkflowStreamView.as_view(), name="workflow_stream"),
    path("agent-reports/", AgentReportListView.as_view(), name="agent_report_list"),
    path(
        "agent-reports/<str:run>/<str:name>/",
        AgentReportDetailView.as_view(),
        name="agent_report_detail",
    ),
    *router.urls,
]
