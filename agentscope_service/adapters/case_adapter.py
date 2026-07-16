"""Adapter for apps.case_manager — test case operations."""
from __future__ import annotations


class CaseAdapter:
    """Wraps case_manager.api and case_manager.models for tool access."""

    @staticmethod
    def save_definition(case_id: str, title: str, category: str = "",
                        description: str = "", steps: str = "",
                        steps_data: list | None = None, enabled: bool = True,
                        package_name: str = "", directory_id=None,
                        priority: str = "medium", design_method: str = ""):
        from apps.case_manager.api import save_definition
        return save_definition(
            case_id=case_id, title=title, category=category,
            description=description, steps=steps,
            steps_data=steps_data or [], enabled=enabled,
            package_name=package_name, directory_id=directory_id,
            priority=priority, design_method=design_method,
        )

    @staticmethod
    def get_definition(case_id: str):
        from apps.case_manager.api import get_definition
        return get_definition(case_id)

    @staticmethod
    def get_enabled_definitions(case_ids=None):
        from apps.case_manager.api import get_enabled_definitions
        return get_enabled_definitions(case_ids)

    @staticmethod
    def list_definitions(limit: int = 50):
        from apps.case_manager.models import TestDefinition
        return list(TestDefinition.objects.filter(enabled=True)[:limit])

    @staticmethod
    def directory_exists(directory_id) -> bool:
        from apps.case_manager.models import CaseDirectory
        return CaseDirectory.objects.filter(id=directory_id).exists()
