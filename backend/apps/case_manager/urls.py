from rest_framework.routers import DefaultRouter

from .views_drf import CaseProjectViewSet

app_name = "cases"

router = DefaultRouter()
router.register(r"projects", CaseProjectViewSet, basename="cm_project")

urlpatterns = [*router.urls]
