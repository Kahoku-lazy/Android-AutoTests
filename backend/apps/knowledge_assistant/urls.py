"""knowledge-assistant URL routing — status only.

实时语音走 /ws/knowledge-assistant/，不在 /api/ 下。
"""

from django.urls import path

from .views import KnowledgeAssistantStatusAPIView

app_name = "knowledge_assistant"

urlpatterns = [
    path("status/", KnowledgeAssistantStatusAPIView.as_view(), name="status"),
]
