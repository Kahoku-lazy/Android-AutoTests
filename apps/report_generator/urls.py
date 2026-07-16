"""report-generator URL routing — endpoints under /api/reports/."""
from django.urls import path
from .views import list_reports, run_report, task_report, case_breakdown, download_report, view_report

app_name = 'reports'

urlpatterns = [
    path('', list_reports, name='list'),
    path('cases', case_breakdown, name='case_breakdown'),
    path('run/<str:run_id>', run_report, name='run_report'),
    path('task/<str:task_id>', task_report, name='task_report'),
    path('<str:filename>/content', view_report, name='view'),
    path('<str:filename>', download_report, name='download'),
]
