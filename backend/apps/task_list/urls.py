"""task-list URL routing — endpoints under /api/tasks/."""

from django.urls import path

from .views import (
    AgentTaskCancelAPIView,
    AgentTaskClearAPIView,
    AgentTaskDeleteAPIView,
    AgentTaskDetailAPIView,
    AgentTaskListAPIView,
    AgentTaskRerunAPIView,
    TaskMediaAPIView,
    TaskReportAPIView,
    TaskSubmitAPIView,
)
from .views_upload import UploadFileAPIView

app_name = "tasks"

urlpatterns = [
    path("submit/", TaskSubmitAPIView.as_view(), name="task_submit"),
    path("upload-file/", UploadFileAPIView.as_view(), name="task_upload_file"),
    path("", AgentTaskListAPIView.as_view(), name="task_list"),
    path("clear/", AgentTaskClearAPIView.as_view(), name="task_clear"),
    path("<int:task_id>/report/", TaskReportAPIView.as_view(), name="task_report"),
    path("<int:task_id>/media/<int:media_id>/", TaskMediaAPIView.as_view(), name="task_media"),
    path("<int:task_id>/", AgentTaskDetailAPIView.as_view(), name="task_detail"),
    path("<int:task_id>/delete/", AgentTaskDeleteAPIView.as_view(), name="task_delete"),
    path("<int:task_id>/rerun/", AgentTaskRerunAPIView.as_view(), name="task_rerun"),
    path("<int:task_id>/cancel/", AgentTaskCancelAPIView.as_view(), name="task_cancel"),
]
