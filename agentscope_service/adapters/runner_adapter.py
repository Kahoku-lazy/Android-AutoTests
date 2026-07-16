"""Adapter for apps.test_runner — test execution operations."""
from __future__ import annotations


class RunnerAdapter:
    """Wraps test_runner.api and test_runner.models for tool access."""

    @staticmethod
    def get_run_results(run_id: str):
        from apps.test_runner.api import get_run_results
        return get_run_results(run_id)

    @staticmethod
    def list_active_runs():
        from apps.test_runner.api import list_active_runs
        return list_active_runs()

    @staticmethod
    def stop_run(run_id: str):
        from apps.test_runner.api import stop_run
        return stop_run(run_id)

    @staticmethod
    def get_run_record(run_id: str):
        from apps.test_runner.models import TestRunRecord
        return TestRunRecord.objects.filter(run_id=run_id).first()

    @staticmethod
    def list_ai_tasks(status: str = "all", limit: int = 20):
        from apps.test_runner.models import TestRunRecord
        qs = TestRunRecord.objects.filter(run_id__startswith="ai-task-")
        status_upper = status.upper()
        if status_upper in ("PENDING", "RUNNING", "COMPLETED", "FAILED", "STOPPED"):
            qs = qs.filter(status=status_upper)
        return list(qs.order_by("-started_at")[:limit])

    @staticmethod
    def get_sop(sop_id: str):
        from apps.test_runner.models import TestSOP
        return TestSOP.objects.filter(sop_id=sop_id).first()

    @staticmethod
    def create_sop(sop_id: str, conv_id: int, phase: int, status: str,
                   requirement: str, case_design):
        from apps.test_runner.models import TestSOP
        import json as _json
        return TestSOP.objects.create(
            sop_id=sop_id, conv_id=conv_id, phase=phase, status=status,
            requirement=requirement,
            case_design=_json.dumps(case_design) if not isinstance(case_design, str) else case_design,
        )

    @staticmethod
    def update_sop(sop_id: str, **fields):
        from apps.test_runner.models import TestSOP
        sop = TestSOP.objects.filter(sop_id=sop_id).first()
        if sop:
            for k, v in fields.items():
                setattr(sop, k, v)
            sop.save()
        return sop

    @staticmethod
    def create_run_record(run_id: str, status: str, device_serial: str,
                          selected_cases, loop_count: int):
        # Delegate to the state machine's built-in run creation
        from apps.test_runner.models import TestRunRecord
        from datetime import datetime
        return TestRunRecord.objects.create(
            run_id=run_id, status=status, device_serial=device_serial,
            selected_cases=selected_cases, loop_count=loop_count,
            started_at=datetime.now().isoformat(),
        )
