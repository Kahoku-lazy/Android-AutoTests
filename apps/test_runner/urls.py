"""test-runner URL routing — 12 endpoints under /api/runner/."""
from django.urls import path
from .views import start_test_run, stop_test_run, cancel_queued_task, test_run_status, list_test_runs, list_active, run_single_step, task_card_list, task_card_save, task_card_delete, run_monitor, run_snapshot

app_name = 'runner'

urlpatterns = [
    path('run', start_test_run, name='run'),
    path('active', list_active, name='active'),
    path('queue/cancel', cancel_queued_task, name='queue_cancel'),
    path('run/<str:run_id>/stop', stop_test_run, name='stop'),
    path('run/<str:run_id>/status', test_run_status, name='status'),
    path('runs', list_test_runs, name='runs'),
    path('run-step', run_single_step, name='run_step'),
    path('tasks', task_card_list, name='task_list'),
    path('tasks/save', task_card_save, name='task_save'),
    path('tasks/<str:task_id>', task_card_delete, name='task_delete'),
    # TREP v1.0 Phase 0: 监控 + 快照端点
    path('monitor/<str:run_id>', run_monitor, name='monitor'),
    path('run/<str:run_id>/snapshot', run_snapshot, name='snapshot'),
]
