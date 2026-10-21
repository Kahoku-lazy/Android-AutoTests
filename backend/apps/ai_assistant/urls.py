"""ai-assistant URL routing — agents and uploads only.

Task endpoints have moved to /api/tasks/ (apps.task_list).
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views_drf import AgentViewSet
from .views_upload_drf import UploadAvatarAPIView

app_name = "ai"

router = DefaultRouter()
router.register("agents", AgentViewSet, basename="ai_agent")

special_patterns = [
    # Avatar upload only; task file upload lives at /api/tasks/upload-file/.
    path("upload-avatar/", UploadAvatarAPIView.as_view(), name="upload_avatar"),
]

urlpatterns = special_patterns + router.urls
