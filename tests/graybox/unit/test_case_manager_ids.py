"""Unit tests for document case ID allocation."""

from __future__ import annotations

import re

import pytest

from django.utils import timezone

from apps.case_manager.api_ids import next_case_id
from apps.case_manager.models import CaseProject
from apps.case_manager.models import TestDefinition as CaseDoc

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


def test_next_case_id_format():
    today = timezone.now().strftime("%Y%m%d")
    case_id = next_case_id()
    assert re.match(rf"^TC-{today}-\d{{4}}$", case_id)


def test_next_case_id_increments_same_day():
    today = timezone.now().strftime("%Y%m%d")
    project = CaseProject.objects.create(name="p1", created_by="u1")
    CaseDoc.objects.create(
        id=f"TC-{today}-0003",
        project=project,
        title="t",
        test_type="app",
        business_type="appliance",
        steps="s",
        expected_result="e",
        created_by="u1",
    )
    assert next_case_id() == f"TC-{today}-0004"
