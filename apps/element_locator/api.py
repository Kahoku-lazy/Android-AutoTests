"""element-locator public API.

Semi-shared: models (cross-app read), api functions (cross-app write).
"""
from .models import Page, Element, PageFlow
from .service import gen_xpath_candidates, simple_yaml_dump


# ── Query helpers (cross-app read — allowed per 读放开规则) ──

def get_test_points(page_ids=None):
    """Get elements marked as test points, optionally filtered by page."""
    qs = Element.objects.filter(is_test_point=True).select_related('page')
    if page_ids:
        qs = qs.filter(page_id__in=page_ids)
    return list(qs.order_by('page_id', 'id'))


def get_flows():
    """Get all page flows with page labels."""
    return list(PageFlow.objects.select_related('from_page', 'to_page', 'trigger_element'))


# ── Write helpers (cross-app write — must go through api) ──

def create_page(device, package='', activity='', screenshot_path='', element_count=0):
    """Create a page snapshot record."""
    return Page.objects.create(
        device=device, package=package, activity=activity,
        screenshot_path=screenshot_path, element_count=element_count,
    )


def create_flow(from_page_id, to_page_id, trigger_element_id=None, trigger_action='click'):
    """Create a page flow record."""
    return PageFlow.objects.create(
        from_page_id=from_page_id, to_page_id=to_page_id,
        trigger_element_id=trigger_element_id, trigger_action=trigger_action,
    )


def clear_all():
    """Clear all pages, elements, and flows."""
    Element.objects.all().delete()
    PageFlow.objects.all().delete()
    Page.objects.all().delete()


__all__ = [
    'Page', 'Element', 'PageFlow', 'gen_xpath_candidates', 'simple_yaml_dump',
    'get_test_points', 'get_flows',
    'create_page', 'create_flow', 'clear_all',
]
