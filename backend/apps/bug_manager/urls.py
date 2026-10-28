"""bug-manager URL routing — endpoints under /api/bugs/."""

from django.urls import path

from backend.apps.bug_manager.views import (
    BugDetailAPIView,
    BugListAPIView,
    BugSyncAPIView,
)

app_name = "bugs"

urlpatterns = [
    path("", BugListAPIView.as_view(), name="bug_list"),
    path("sync/", BugSyncAPIView.as_view(), name="bug_sync"),
    path("<int:bug_id>/", BugDetailAPIView.as_view(), name="bug_detail"),
]
