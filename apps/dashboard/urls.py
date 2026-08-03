"""Dashboard URL routing — aggregation endpoints under /api/."""

from django.urls import path

from .views import case_stats, dashboard_activities, dashboard_stats, device_stats

app_name = "dashboard"

urlpatterns = [
    path("dashboard/stats/", dashboard_stats, name="dashboard_stats"),
    path("dashboard/activities/", dashboard_activities, name="dashboard_activities"),
    path("devices/stats/", device_stats, name="device_stats"),
    path("cases/stats/", case_stats, name="case_stats"),
]
