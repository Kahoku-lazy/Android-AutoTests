"""ai-assistant URL routing — agents only.

Task endpoints have moved to /api/tasks/ (apps.task_list).
Avatar is a fixed built-in icon, so the old upload-avatar endpoint is gone.
"""

from rest_framework.routers import DefaultRouter

from .views_drf import AgentViewSet

app_name = "ai"

router = DefaultRouter()
router.register("agents", AgentViewSet, basename="ai_agent")

urlpatterns = router.urls
