from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from backend.apps.task_list.media_views import SignedTaskMediaAPIView
from backend.apps.task_list.views import TaskDrainAPIView

urlpatterns = [
    path("", lambda r: JsonResponse({"status": True, "service": "Android-AutoTests API"})),
    path(
        "media/signed/<int:task_id>/<int:media_id>/<int:expires>/<str:signature>/",
        SignedTaskMediaAPIView.as_view(),
        name="task_media_signed",
    ),
    path("api/", include("backend.apps.dashboard.urls")),
    path("admin/", admin.site.urls),
    path("api/devices/", include("backend.apps.device_pool.urls")),
    path("api/cases/", include("backend.apps.case_manager.urls")),
    path("api/reports/", include("backend.apps.report_generator.urls")),
    path("api/auth/", include("backend.apps.accounts.urls")),
    path("api/ai/", include("backend.apps.ai_assistant.urls")),
    path("api/tasks/", include("backend.apps.task_list.urls")),
    path("api/bugs/", include("backend.apps.bug_manager.urls")),
    path("api/serial-log/", include("backend.apps.serial_log.urls")),
    path("api/knowledge-search/", include("backend.apps.knowledge_search.urls")),
    path("api/ops/", include("backend.apps.ops_console.urls")),
    path("api/system/drain/", TaskDrainAPIView.as_view(), name="system_drain"),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
]

if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
