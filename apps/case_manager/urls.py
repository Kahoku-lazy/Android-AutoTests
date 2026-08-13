"""case-manager URL routing — DRF router + legacy paths coexist."""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import list_step_types
from .views_api import (
    api_testing_definition_detail,
    api_testing_definitions_batch,
    api_testing_definitions_handler,
)
from .views_directories import (
    directory_batch_move,
    directory_create,
    directory_detail,
    directory_list,
    directory_permission,
)

# DRF ViewSets
from .views_drf import (
    ApiCaseViewSet,
    CaseActionsViewSet,
    CaseDirectoryViewSet,
    StorageCaseViewSet,
    UiCaseViewSet,
    WebCaseViewSet,
)
from .views_lock import (
    acquire_edit_lock,
    case_lock,
    case_unlock,
    release_edit_lock,
    set_visibility,
)
from .views_storage import (
    storage_definition_detail,
    storage_definitions_batch,
    storage_definitions_handler,
)
from .views_ui import (
    definition_detail,
    definitions_batch,
    definitions_handler,
    download_export,
    export_yaml,
    list_exports,
)
from .views_web import (
    web_definition_detail,
    web_definitions_batch,
    web_definitions_handler,
)

app_name = "cases"

# ── DRF router (new standard REST endpoints) ──
router = DefaultRouter()
router.register(r"directories", CaseDirectoryViewSet, basename="cm_dir")
router.register(r"definitions", UiCaseViewSet, basename="cm_ui")
router.register(r"storage/definitions", StorageCaseViewSet, basename="cm_storage")
router.register(r"api-testing/definitions", ApiCaseViewSet, basename="cm_api")
router.register(r"web/definitions", WebCaseViewSet, basename="cm_web")

# CaseActionsViewSet — lock/unlock/visibility (shared across all types)
# Registered manually (not via router) to avoid prefix collision with UiCaseViewSet.
actions_view = CaseActionsViewSet.as_view({"post": "acquire_lock"})
actions_unlock = CaseActionsViewSet.as_view({"post": "release_lock"})
actions_hard_lock = CaseActionsViewSet.as_view({"post": "case_lock"})
actions_hard_unlock = CaseActionsViewSet.as_view({"post": "case_unlock"})
actions_visibility = CaseActionsViewSet.as_view({"post": "set_visibility"})

drf_lock_patterns = [
    path("definitions/<str:case_id>/lock/", actions_view, name="drf_case_lock"),
    path("definitions/<str:case_id>/unlock/", actions_unlock, name="drf_case_unlock"),
    path("definitions/<str:case_id>/case-lock/", actions_hard_lock, name="drf_case_perm_lock"),
    path(
        "definitions/<str:case_id>/case-unlock/", actions_hard_unlock, name="drf_case_perm_unlock"
    ),
    path("definitions/<str:case_id>/visibility/", actions_visibility, name="drf_case_visibility"),
]

# ── Legacy paths (保留，旧前端继续工作) ──
legacy_patterns = [
    # Directories (shared, type-agnostic)
    path("directories", directory_list, name="dir_list"),
    path("directories/create", directory_create, name="dir_create"),
    path("directories/batch-move", directory_batch_move, name="dir_batch_move"),
    path("directories/<int:dir_id>", directory_detail, name="dir_detail"),
    path("directories/<int:dir_id>/permission", directory_permission, name="dir_permission"),
    # UI Automation (existing routes)
    path("definitions", definitions_handler, name="defs"),
    path("definitions/batch", definitions_batch, name="defs_batch"),
    path("definitions/<str:case_id>/lock", acquire_edit_lock, name="case_lock"),
    path("definitions/<str:case_id>/unlock", release_edit_lock, name="case_unlock"),
    path("definitions/<str:case_id>/case-lock", case_lock, name="case_perm_lock"),
    path("definitions/<str:case_id>/case-unlock", case_unlock, name="case_perm_unlock"),
    path("definitions/<str:case_id>/visibility", set_visibility, name="case_visibility"),
    path("definitions/<str:case_id>", definition_detail, name="def_detail"),
    # Storage
    path("storage/definitions", storage_definitions_handler, name="storage_defs"),
    path("storage/definitions/batch", storage_definitions_batch, name="storage_defs_batch"),
    path("storage/definitions/<str:case_id>", storage_definition_detail, name="storage_def_detail"),
    # API Testing
    path("api-testing/definitions", api_testing_definitions_handler, name="api_defs"),
    path("api-testing/definitions/batch", api_testing_definitions_batch, name="api_defs_batch"),
    path(
        "api-testing/definitions/<str:case_id>",
        api_testing_definition_detail,
        name="api_def_detail",
    ),
    # Web Automation
    path("web/definitions", web_definitions_handler, name="web_defs"),
    path("web/definitions/batch", web_definitions_batch, name="web_defs_batch"),
    path("web/definitions/<str:case_id>", web_definition_detail, name="web_def_detail"),
    # YAML Export / step types
    path("step-types", list_step_types, name="step_types"),
    path("export/yaml", export_yaml, name="export_yaml"),
    path("exports", list_exports, name="exports"),
    path("exports/<str:filename>", download_export, name="export_dl"),
]

urlpatterns = router.urls + drf_lock_patterns + legacy_patterns
