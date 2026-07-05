"""report-generator URL routing — 2 endpoints under /api/reports/."""
from django.urls import path
from .views import list_reports, download_report, view_report

app_name = 'reports'

urlpatterns = [
    path('', list_reports, name='list'),
    path('<str:filename>/content', view_report, name='view'),
    path('<str:filename>', download_report, name='download'),
]
