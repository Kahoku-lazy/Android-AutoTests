"""test-runner public API."""
from .models import TestRunRecord, TestResult
from .runner import TestRunner, TestRunnerCallback, get_active_run, stop_run, list_active_runs


# ── Query helpers ──

def get_run_results(run_id):
    """Get all results for a test run."""
    return list(TestResult.objects.filter(run_id=run_id).order_by('created_at'))


# ── Write helpers ──

def persist_results(run_record, case_results):
    """Persist test results to DB."""
    objs = [
        TestResult(
            run=run_record,
            case_id=r.case_id,
            iteration=r.iteration,
            result=r.result,
            duration_ms=r.duration_ms,
            detail=getattr(r, "detail", "") or "",
        )
        for r in case_results
    ]
    return TestResult.objects.bulk_create(objs)


__all__ = [
    'TestRunRecord', 'TestResult',
    'TestRunner', 'TestRunnerCallback',
    'get_active_run', 'stop_run', 'list_active_runs',
    'get_run_results', 'persist_results',
]
