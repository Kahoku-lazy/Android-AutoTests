"""report-generator URL routing — endpoints under /api/reports/."""
from django.urls import path
from .views import list_reports, run_report, download_report, view_report

app_name = 'reports'

urlpatterns = [
    path('', list_reports, name='list'),
    path('run/<str:run_id>', run_report, name='run_report'),
    path('<str:filename>/content', view_report, name='view'),
    path('<str:filename>', download_report, name='download'),
]
