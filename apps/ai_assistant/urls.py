"""ai-assistant URL routing — DRF router + 任务发布端点。

Batch 1-3 已迁移：Agent 组（AgentViewSet + APIView）、上传（APIView 组）与
任务发布（任务提交 / 列表 / 详情 / 关闭 / 重跑）。
AI 工具箱、平台工具调试与内部工具网关已整体下线。

router 使用默认的 trailing_slash=True：全平台唯一约定是「/api/ 路径以 / 结尾」
（见 openspec/specs/api-path-convention）。
"""

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views_drf import (
    AgentTaskCancelAPIView,
    AgentTaskClearAPIView,
    AgentTaskDeleteAPIView,
    AgentTaskDetailAPIView,
    AgentTaskListAPIView,
    AgentTaskRerunAPIView,
    AgentViewSet,
    TaskSubmitAPIView,
)
from .views_upload_drf import UploadAvatarAPIView, UploadFileAPIView

app_name = "ai"

# ── DRF router ──
router = DefaultRouter()
router.register("agents", AgentViewSet, basename="ai_agent")

# ── 特殊路由（先于 router，避免 /agents/{pk} 抢占）──
special_patterns = [
    # 任务发布（提交 + 列表）
    path("tasks/submit/", TaskSubmitAPIView.as_view(), name="ai_tasks_submit"),
    path("agent-tasks/", AgentTaskListAPIView.as_view(), name="ai_agent_tasks"),
    path("agent-tasks/clear/", AgentTaskClearAPIView.as_view(), name="ai_agent_tasks_clear"),
    path(
        "agent-tasks/<int:task_id>/",
        AgentTaskDetailAPIView.as_view(),
        name="ai_agent_task_detail",
    ),
    path(
        "agent-tasks/<int:task_id>/delete/",
        AgentTaskDeleteAPIView.as_view(),
        name="ai_agent_task_delete",
    ),
    path(
        "agent-tasks/<int:task_id>/rerun/",
        AgentTaskRerunAPIView.as_view(),
        name="ai_agent_task_rerun",
    ),
    path(
        "agent-tasks/<int:task_id>/cancel/",
        AgentTaskCancelAPIView.as_view(),
        name="ai_agent_task_cancel",
    ),
    # Uploads
    path("upload-avatar/", UploadAvatarAPIView.as_view(), name="upload_avatar"),
    path("upload-file/", UploadFileAPIView.as_view(), name="upload_file"),
]

urlpatterns = special_patterns + router.urls
