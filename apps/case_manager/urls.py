"""case-manager URL routing — 12 endpoints under /api/cases/."""

from django.urls import path
from .views import (
    definitions_handler,
    definition_detail,
    definitions_batch,
    acquire_edit_lock,
    release_edit_lock,
    case_lock,
    case_unlock,
    set_visibility,
    directory_permission,
    export_yaml,
    list_exports,
    download_export,
    directory_list,
    directory_create,
    directory_detail,
    directory_batch_move,
)

app_name = "cases"

urlpatterns = [
    # Directories
    path("directories", directory_list, name="dir_list"),
    path("directories/create", directory_create, name="dir_create"),
    path("directories/batch-move", directory_batch_move, name="dir_batch_move"),
    path("directories/<int:dir_id>", directory_detail, name="dir_detail"),
    path("directories/<int:dir_id>/permission", directory_permission, name="dir_permission"),
    # Definitions
    path("definitions", definitions_handler, name="defs"),
    path("definitions/batch", definitions_batch, name="defs_batch"),
    path("definitions/<str:case_id>", definition_detail, name="def_detail"),
    path("definitions/<str:case_id>/lock", acquire_edit_lock, name="def_lock"),
    path("definitions/<str:case_id>/unlock", release_edit_lock, name="def_unlock"),
    path("definitions/<str:case_id>/case-lock", case_lock, name="case_lock"),
    path("definitions/<str:case_id>/case-unlock", case_unlock, name="case_unlock"),
    path("definitions/<str:case_id>/visibility", set_visibility, name="def_visibility"),
    path("export/yaml", export_yaml, name="export_yaml"),
    path("exports", list_exports, name="exports"),
    path("exports/<str:filename>", download_export, name="export_dl"),
]
