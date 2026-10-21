"""Root URL configuration — API + Admin + Docs."""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

urlpatterns = [
    path("", lambda r: JsonResponse({"status": True, "service": "Android-AutoTests API"})),
    # Dashboard stats (aggregated from all modules) — 见 apps/dashboard/urls.py
    path("api/", include("backend.apps.dashboard.urls")),
    # Django Admin (管理员专用，不给普通用户)
    path("admin/", admin.site.urls),
    # ── Module routes (1 include() per app) ──
    path("api/devices/", include("backend.apps.device_pool.urls")),
    path("api/cases/", include("backend.apps.case_manager.urls")),
    path("api/workflow/", include("backend.apps.workflow.urls")),
    path("api/reports/", include("backend.apps.report_generator.urls")),
    path("api/auth/", include("backend.apps.accounts.urls")),
    path("api/ai/", include("backend.apps.ai_assistant.urls")),
    path("api/tasks/", include("backend.apps.task_list.urls")),
    path("api/serial-log/", include("backend.apps.serial_log.urls")),
    # ── DRF API documentation (drf-spectacular + Swagger UI) ──
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger"),
]

# DEBUG 模式下由 Django 直接提供静态/媒体文件服务
if settings.DEBUG:
    # 静态走 staticfiles finders（app 静态 + STATICFILES_DIRS）：Admin/Jazzmin 与
    # drf-spectacular sidecar 资产都依赖它；改成 STATIC_ROOT 会因未 collectstatic 而 404
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
