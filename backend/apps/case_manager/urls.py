"""case-manager URL routing — project / directory / document definition APIs."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views_drf import (
    CaseDirectoryViewSet,
    CaseFileViewSet,
    CaseProjectViewSet,
    TestDefinitionViewSet,
    move_items,
)

app_name = "cases"

router = DefaultRouter()
router.register(r"projects", CaseProjectViewSet, basename="cm_project")
router.register(r"directories", CaseDirectoryViewSet, basename="cm_dir")
router.register(r"files", CaseFileViewSet, basename="cm_file")
router.register(r"definitions", TestDefinitionViewSet, basename="cm_def")

urlpatterns = [
    *router.urls,
    path("move/", move_items, name="cm_move"),
]
