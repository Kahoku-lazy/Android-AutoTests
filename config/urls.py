"""Root URL configuration — API + Admin + Docs."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

from apps.dashboard.views import (
    case_stats,
    dashboard_activities,
    dashboard_stats,
    device_stats,
)

from .api_docs import api_docs_html, api_docs_json

urlpatterns = [
    path("", lambda r: JsonResponse({"status": True, "service": "Android-AutoTests API"})),
    # API documentation
    path("api/docs", api_docs_json, name="api_docs_json"),
    path("api/docs.html", api_docs_html, name="api_docs_html"),
    # Dashboard stats (aggregated from all modules)
    path("api/dashboard/stats/", dashboard_stats, name="dashboard_stats"),
    path("api/dashboard/activities/", dashboard_activities, name="dashboard_activities"),
    path("api/devices/stats/", device_stats, name="device_stats"),
    path("api/cases/stats/", case_stats, name="case_stats"),
    # Django Admin (管理员专用，不给普通用户)
    path("admin/", admin.site.urls),
    # ── Module routes (1 include() per app) ──
    path("api/elements/", include("apps.element_locator.urls")),
    path("api/devices/", include("apps.device_pool.urls")),
    path("api/cases/", include("apps.case_manager.urls")),
    path("api/workflow/", include("apps.workflow.urls")),
    path("api/runner/", include("apps.test_runner.urls")),
    path("api/reports/", include("apps.report_generator.urls")),
    path("api/ai/", include("apps.ai_assistant.urls")),
    path("api/evaluator/", include("apps.evaluator.urls")),
]

# DEBUG 模式下由 Django 直接提供静态/媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
