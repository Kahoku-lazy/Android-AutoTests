"""ai-assistant URL routing — DRF router + 豁免遗留路径。

Batch 1-3 已迁移：Agent 组（AgentViewSet + APIView）、对话组（ConversationViewSet + TaskBoardAPIView）、
工具箱/Agent 工具（ToolboxViewSet + AgentToolActionsMixin）、知识库与上传（APIView 组）。
豁免：SSE（chat_stream）与工具网关（schemas/agent-config/execute）。

router 使用 trailing_slash=False 以保持旧路径（无尾斜杠）原样匹配。
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views.tool_gateway import agent_config, tool_gateway, tool_schemas
from .views_drf import (
    AgentHealthAPIView,
    AgentTaskListAPIView,
    AgentViewSet,
    AvailableSkillsAPIView,
    AvailableToolsAPIView,
    ConversationViewSet,
    ModelDetectAPIView,
    PlatformConfigAPIView,
    PlatformToolToggleAPIView,
    TaskBoardAPIView,
    TaskSubmitAPIView,
)
from .views_knowledge_drf import (
    KnowledgeAddDocAPIView,
    KnowledgeDocumentsAPIView,
    KnowledgeReindexAPIView,
    KnowledgeStatusAPIView,
)
from .views_toolbox_drf import ToolboxViewSet
from .views_upload_drf import UploadAvatarAPIView, UploadFileAPIView

app_name = "ai"

# ── DRF router（无尾斜杠，与旧契约一致）──
router = DefaultRouter(trailing_slash=False)
router.register("agents", AgentViewSet, basename="ai_agent")
router.register("conversations", ConversationViewSet, basename="ai_conversation")
router.register("toolbox", ToolboxViewSet, basename="ai_toolbox")

# ── 特殊路由（先于 router，避免 /agents/{pk} 抢占）──
special_patterns = [
    path("agents/health", AgentHealthAPIView.as_view(), name="agent_health"),
    path("models/detect", ModelDetectAPIView.as_view(), name="models_detect"),
    path("available-tools", AvailableToolsAPIView.as_view(), name="available_tools"),
    path("available-skills", AvailableSkillsAPIView.as_view(), name="available_skills"),
    path(
        "platform-tools/toggle", PlatformToolToggleAPIView.as_view(), name="platform_tools_toggle"
    ),
    path("platform-config", PlatformConfigAPIView.as_view(), name="platform_config"),
    path("platform-config/update", PlatformConfigAPIView.as_view(), name="platform_config_update"),
    # Workbench task board
    path("tasks", TaskBoardAPIView.as_view(), name="ai_tasks_list"),
    # 任务发布（提交 + 列表）
    path("tasks/submit", TaskSubmitAPIView.as_view(), name="ai_tasks_submit"),
    path("agent-tasks", AgentTaskListAPIView.as_view(), name="ai_agent_tasks"),
    # Knowledge base
    path("knowledge/status", KnowledgeStatusAPIView.as_view(), name="kb_status"),
    path("knowledge/documents", KnowledgeDocumentsAPIView.as_view(), name="kb_documents"),
    path("knowledge/reindex", KnowledgeReindexAPIView.as_view(), name="kb_reindex"),
    path("knowledge/documents/add", KnowledgeAddDocAPIView.as_view(), name="kb_add_doc"),
    # Uploads
    path("upload-avatar", UploadAvatarAPIView.as_view(), name="upload_avatar"),
    path("upload-file", UploadFileAPIView.as_view(), name="upload_file"),
]

# ── 豁免路径（不迁移）──
legacy_patterns = [
    # Tool gateway — 中间件白名单 + 动态分发
    path("tools/schemas", tool_schemas, name="tool_schemas"),
    path("tools/agent-config/<str:agent_id>", agent_config, name="tool_agent_config"),
    path("tools/<str:module>/<str:action>", tool_gateway, name="tool_gateway"),
]

urlpatterns = special_patterns + router.urls + legacy_patterns
