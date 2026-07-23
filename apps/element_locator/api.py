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


def get_web_elements(locator_type=None, is_test_point=None):
    """Get web elements, optionally filtered."""
    from .models import WebElement
    qs = WebElement.objects.all()
    if locator_type:
        qs = qs.filter(locator_type=locator_type)
    if is_test_point is not None:
        qs = qs.filter(is_test_point=is_test_point)
    return list(qs.order_by("name"))


def get_web_groups():
    """Get all web groups ordered by name."""
    from .models import WebGroup
    return list(WebGroup.objects.order_by("sort_order", "name"))


def get_web_flows():
    """Get all web page flows with group labels."""
    from .models import WebPageFlow
    return list(WebPageFlow.objects.select_related('from_group', 'to_group', 'trigger_element'))


def get_api_groups():
    """Get all API groups ordered by name."""
    from .models import ApiGroup
    return list(ApiGroup.objects.order_by("sort_order", "name"))


def get_api_endpoints():
    """Get all API endpoint definitions."""
    from .models import ApiEndpoint
    return list(ApiEndpoint.objects.order_by("name"))


__all__ = [
    'Page', 'Element', 'PageFlow', 'gen_xpath_candidates', 'simple_yaml_dump',
    'get_test_points', 'get_flows', 'get_web_elements', 'get_web_groups',
    'create_page', 'create_flow', 'clear_all',
]
