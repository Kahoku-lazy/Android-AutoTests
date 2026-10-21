"""serial-log URL routing — 四个端点，全部位于 /api/serial-log/ 之下。"""

from django.urls import path

from .views import (
    LogKeywordCatalogAPIView,
    LogPortLinesAPIView,
    LogPortListAPIView,
    LogPortToggleAPIView,
)

app_name = "serial_log"

urlpatterns = [
    path("ports/", LogPortListAPIView.as_view(), name="ports"),
    path("ports/toggle/", LogPortToggleAPIView.as_view(), name="ports_toggle"),
    path("ports/<int:port>/lines/", LogPortLinesAPIView.as_view(), name="port_lines"),
    path("keywords/", LogKeywordCatalogAPIView.as_view(), name="keywords"),
]
