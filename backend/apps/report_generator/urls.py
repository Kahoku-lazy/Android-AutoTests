"""report-generator URL routing — endpoints under /api/reports/."""

from django.urls import path

from .views import (
    ReportContentAPIView,
    ReportDownloadAPIView,
    ReportListAPIView,
)

app_name = "reports"

urlpatterns = [
    path("", ReportListAPIView.as_view(), name="list"),
    path("<str:filename>/content/", ReportContentAPIView.as_view(), name="view"),
    path("<str:filename>/", ReportDownloadAPIView.as_view(), name="download"),
]
