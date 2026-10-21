"""Dashboard URL routing — aggregation endpoints under /api/."""

from django.urls import path

from .views import (
    CaseStatsAPIView,
    DashboardActivitiesAPIView,
    DashboardStatsAPIView,
    DeviceStatsAPIView,
)

app_name = "dashboard"

urlpatterns = [
    path("dashboard/stats/", DashboardStatsAPIView.as_view(), name="dashboard_stats"),
    path(
        "dashboard/activities/", DashboardActivitiesAPIView.as_view(), name="dashboard_activities"
    ),
    path("devices/stats/", DeviceStatsAPIView.as_view(), name="device_stats"),
    path("cases/stats/", CaseStatsAPIView.as_view(), name="case_stats"),
]
