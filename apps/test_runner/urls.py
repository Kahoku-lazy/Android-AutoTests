"""test-runner URL routing — 4 endpoints under /api/runner/."""
from django.urls import path
from .views import start_test_run, stop_test_run, test_run_status, list_test_runs, list_active, run_single_step

app_name = 'runner'

urlpatterns = [
    path('run', start_test_run, name='run'),
    path('active', list_active, name='active'),
    path('run/<str:run_id>/stop', stop_test_run, name='stop'),
    path('run/<str:run_id>/status', test_run_status, name='status'),
    path('runs', list_test_runs, name='runs'),
    path('run-step', run_single_step, name='run_step'),
]
