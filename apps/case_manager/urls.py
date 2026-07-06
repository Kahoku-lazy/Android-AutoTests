"""case-manager URL routing — 12 endpoints under /api/cases/."""

from django.urls import path
from .views import (
    definitions_handler,
    definition_detail,
    definitions_batch,
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
    # Definitions
    path("definitions", definitions_handler, name="defs"),
    path("definitions/batch", definitions_batch, name="defs_batch"),
    path("definitions/<str:case_id>", definition_detail, name="def_detail"),
    path("export/yaml", export_yaml, name="export_yaml"),
    path("exports", list_exports, name="exports"),
    path("exports/<str:filename>", download_export, name="export_dl"),
]
