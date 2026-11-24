from django.urls import path

from .views import (
    EvalRunDetailAPIView,
    EvalRunListAPIView,
    KnowledgeModuleDetailAPIView,
    KnowledgeModuleIndexAPIView,
    KnowledgeModuleListAPIView,
    KnowledgeQueryAPIView,
    RetrievalSettingsAPIView,
)

app_name = "knowledge_search"

urlpatterns = [
    path("settings/", RetrievalSettingsAPIView.as_view(), name="settings"),
    path("modules/", KnowledgeModuleListAPIView.as_view(), name="modules"),
    path("modules/<int:pk>/", KnowledgeModuleDetailAPIView.as_view(), name="module_detail"),
    path("modules/<int:pk>/index/", KnowledgeModuleIndexAPIView.as_view(), name="module_index"),
    path("query/", KnowledgeQueryAPIView.as_view(), name="query"),
    path("evaluations/", EvalRunListAPIView.as_view(), name="evaluations"),
    path("evaluations/<int:pk>/", EvalRunDetailAPIView.as_view(), name="evaluation_detail"),
]
