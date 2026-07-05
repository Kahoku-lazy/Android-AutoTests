"""case-manager public API.

Semi-shared: models (cross-app read), api functions (cross-app write).
"""
import json
from .models import TestDefinition, TestCaseCache


# ── Query helpers ──

def get_enabled_definitions(case_ids):
    """Get enabled test definitions by ID list."""
    return list(TestDefinition.objects.filter(id__in=case_ids, enabled=True))


def get_definition(case_id):
    """Get a single definition by ID, or None."""
    try:
        return TestDefinition.objects.get(id=case_id)
    except TestDefinition.DoesNotExist:
        return None


# ── Write helpers ──

def save_definition(case_id, **fields):
    """Create or update a test definition."""
    defaults = {
        'title': fields.get('title', ''),
        'category': fields.get('category', ''),
        'description': fields.get('description', ''),
        'steps': fields.get('steps', ''),
        'steps_json': json.dumps(fields.get('steps_data', []), ensure_ascii=False),
        'enabled': fields.get('enabled', True),
        'package_name': fields.get('package_name', ''),
    }
    obj, _ = TestDefinition.objects.update_or_create(id=case_id, defaults=defaults)
    return obj


def cache_yaml(name, yaml_content):
    """Cache YAML export to DB."""
    return TestCaseCache.objects.create(name=name, yaml_content=yaml_content)


__all__ = [
    'TestDefinition', 'TestCaseCache',
    'get_enabled_definitions', 'get_definition',
    'save_definition', 'cache_yaml',
]
