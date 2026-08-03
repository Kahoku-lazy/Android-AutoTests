"""case-manager lock & visibility helpers — generalized across all three case types."""

__all__ = [
    "find_case_across_types",
    "get_case_for_lock",
]

from .models import TestDefinition
from .models_api import ApiTestCase
from .models_storage import StorageTestCase
from .models_web import WebTestCase

_ALL_CASE_MODELS = (TestDefinition, StorageTestCase, ApiTestCase, WebTestCase)


def find_case_across_types(case_id):
    """Look up a case ID across all three test case tables.

    Returns (model_instance, model_class) or (None, None).
    """
    for model in _ALL_CASE_MODELS:
        try:
            return model.objects.get(id=case_id), model
        except model.DoesNotExist:
            continue
    return None, None


def get_case_for_lock(case_id):
    """Fetch a case for lock operations — returns minimal fields needed by lock views.

    Returns the model instance (with .only() for efficiency) or None.
    """
    for model in _ALL_CASE_MODELS:
        try:
            return model.objects.only(
                "id",
                "created_by",
                "editing_by",
                "editing_since",
                "permission",
                "permitted_editors",
                "locked",
                "visibility",
                "permitted_users",
            ).get(id=case_id)
        except model.DoesNotExist:
            continue
    return None
