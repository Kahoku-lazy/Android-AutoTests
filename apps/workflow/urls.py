"""workflow URL routing under /api/workflow/."""

from django.urls import path
from . import views

urlpatterns = [
    path("directories", views.directory_list, name="wf_dir_list"),
    path("directories/create", views.directory_create, name="wf_dir_create"),
    path("directories/<int:dir_id>/move", views.directory_move, name="wf_dir_move"),
    path("directories/<int:dir_id>", views.directory_detail, name="wf_dir_detail"),
    path("documents", views.documents_list, name="wf_doc_list"),
    path("documents/create", views.documents_create, name="wf_doc_create"),
    path("documents/import", views.documents_import, name="wf_doc_import"),
    path("documents/<str:doc_id>/export", views.document_export, name="wf_doc_export"),
    path("documents/<str:doc_id>/move", views.document_move, name="wf_doc_move"),
    path("documents/<str:doc_id>", views.document_detail, name="wf_doc_detail"),
]
