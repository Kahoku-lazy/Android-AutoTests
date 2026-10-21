"""report-generator URL routing — endpoints under /api/reports/."""

from django.urls import path

from .views import (
    CaseBreakdownAPIView,
    ReportContentAPIView,
    ReportDownloadAPIView,
    ReportListAPIView,
    RunReportAPIView,
)

app_name = "reports"

urlpatterns = [
    path("", ReportListAPIView.as_view(), name="list"),
    path("cases/", CaseBreakdownAPIView.as_view(), name="case_breakdown"),
    path("run/<str:run_id>/", RunReportAPIView.as_view(), name="run_report"),
    path("<str:filename>/content/", ReportContentAPIView.as_view(), name="view"),
    path("<str:filename>/", ReportDownloadAPIView.as_view(), name="download"),
]
