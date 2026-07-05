"""case-manager URL routing — 8 endpoints under /api/cases/."""
from django.urls import path
from .views import (
    definitions_handler, definition_detail,
    export_yaml, list_exports, download_export,
)

app_name = 'cases'

urlpatterns = [
    path('definitions', definitions_handler, name='defs'),
    path('definitions/<str:case_id>', definition_detail, name='def_detail'),
    path('export/yaml', export_yaml, name='export_yaml'),
    path('exports', list_exports, name='exports'),
    path('exports/<str:filename>', download_export, name='export_dl'),
]
