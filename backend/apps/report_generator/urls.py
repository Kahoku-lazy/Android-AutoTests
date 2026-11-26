from django.urls import path

from .views import ReportListAPIView

app_name = "reports"

urlpatterns = [
    path("", ReportListAPIView.as_view(), name="list"),
]
