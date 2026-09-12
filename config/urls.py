"""Root URL configuration — API + Admin + Docs."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from .api_docs import api_docs_html, api_docs_json

urlpatterns = [
    path("", lambda r: JsonResponse({"status": True, "service": "Android-AutoTests API"})),
    # API documentation
    path("api/docs", api_docs_json, name="api_docs_json"),
    path("api/docs.html", api_docs_html, name="api_docs_html"),
    # Dashboard stats (aggregated from all modules) — 见 apps/dashboard/urls.py
    path("api/", include("apps.dashboard.urls")),
    # Django Admin (管理员专用，不给普通用户)
    path("admin/", admin.site.urls),
    # ── Module routes (1 include() per app) ──
    path("api/inspector/", include("apps.device_inspector.urls")),
    path("api/elements/", include("apps.element_locator.urls")),
    path("api/devices/", include("apps.device_pool.urls")),
    path("api/cases/", include("apps.case_manager.urls")),
    path("api/workflow/", include("apps.workflow.urls")),
    path("api/reports/", include("apps.report_generator.urls")),
    path("api/auth/", include("apps.accounts.urls")),
    path("api/ai/", include("apps.ai_assistant.urls")),
    path("api/evaluator/", include("apps.evaluator.urls")),
    # ── DRF API documentation (drf-spectacular + Swagger UI) ──
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
]

# DEBUG 模式下由 Django 直接提供静态/媒体文件服务
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
