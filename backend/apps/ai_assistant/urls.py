"""ai-assistant URL routing — 角色注册表与执行报告。

智能体配置页与对话工作流已随 AI 助手重设计下线，只保留创建入口；
报告接口保留，任务清单的「报告」按钮与执行报告页仍在读取。
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views_drf import (
    AgentReportView,
    AssistantAvatarView,
    AssistantPublishView,
    AssistantThreadDeleteView,
    AssistantThreadDetailView,
    AssistantThreadLogFileView,
    AssistantThreadLogView,
    AssistantThreadView,
    AssistantViewSet,
    EvalRunView,
    LiveEvalDetailView,
    ModelConfigDiscoverView,
    ModelConfigViewSet,
    RoleViewSet,
    SopWorkflowDetailView,
    SopWorkflowView,
    ToolCatalogView,
    WorkflowPublishView,
)

app_name = "ai"

router = DefaultRouter()
router.register("model-configs", ModelConfigViewSet, basename="ai_model_config")
router.register("roles", RoleViewSet, basename="ai_role")
router.register("assistants", AssistantViewSet, basename="ai_assistant_card")

urlpatterns = [
    path("tool-catalog/", ToolCatalogView.as_view(), name="ai_tool_catalog"),
    path("evals/run/", EvalRunView.as_view(), name="ai_eval_run"),
    path("evals/runs/<int:run_id>/", LiveEvalDetailView.as_view(), name="ai_eval_detail"),
    path("agent-reports/<str:run>/<str:name>/", AgentReportView.as_view(), name="ai_agent_report"),
    path("sop-workflows/", SopWorkflowView.as_view(), name="ai_sop_workflows"),
    path(
        "sop-workflows/<int:workflow_id>/publish/",
        WorkflowPublishView.as_view(),
        name="ai_sop_workflow_publish",
    ),
    path(
        "sop-workflows/<int:workflow_id>/",
        SopWorkflowDetailView.as_view(),
        name="ai_sop_workflow_detail",
    ),
    path(
        "assistants/<str:assistant_id>/threads/",
        AssistantThreadView.as_view(),
        name="ai_assistant_threads",
    ),
    path(
        "assistants/threads/<str:thread_id>/logs/",
        AssistantThreadLogView.as_view(),
        name="ai_assistant_thread_logs",
    ),
    path(
        "assistants/threads/<str:thread_id>/logs/<str:report_id>/",
        AssistantThreadLogFileView.as_view(),
        name="ai_assistant_thread_log_file",
    ),
    path(
        "assistants/threads/<str:thread_id>/",
        AssistantThreadDetailView.as_view(),
        name="ai_assistant_thread_detail",
    ),
    path(
        "assistants/threads/<str:thread_id>/delete/",
        AssistantThreadDeleteView.as_view(),
        name="ai_assistant_thread_delete",
    ),
    path(
        "assistants/<str:assistant_id>/publish/",
        AssistantPublishView.as_view(),
        name="ai_assistant_publish",
    ),
    path(
        "assistants/<str:assistant_id>/avatar/",
        AssistantAvatarView.as_view(),
        name="ai_assistant_avatar",
    ),
    path(
        "model-configs/discover/",
        ModelConfigDiscoverView.as_view(),
        name="ai_model_config_discover",
    ),
    *router.urls,
]
