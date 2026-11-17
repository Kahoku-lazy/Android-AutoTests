"""用例编号在两张表之间同一天不重复。"""

from __future__ import annotations

import pytest

from backend.apps.case_manager.api_ids import next_case_id
from backend.apps.case_manager.models import AutomationCase, CaseProject, FunctionalCase

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def test_next_case_id_skips_both_tables():
    project = CaseProject.objects.create(name="编号", library_kind="functional", created_by="u1")
    today = next_case_id()
    prefix = today[:12]
    AutomationCase.objects.create(
        id=f"{prefix}0003",
        project=project,
        title="自动",
        business_type="appliance",
    )
    FunctionalCase.objects.create(
        id=f"{prefix}0007",
        project=project,
        title="功能",
        business_type="appliance",
    )
    assert next_case_id() == f"{prefix}0008"
