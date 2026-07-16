"""Adapter for apps.element_locator — UI element operations."""
from __future__ import annotations


class ElementAdapter:
    """Wraps element_locator.api and element_locator.models for tool access."""

    @staticmethod
    def get_test_points(page_ids=None):
        from apps.element_locator.api import get_test_points
        return get_test_points(page_ids)

    @staticmethod
    def search_elements(query: str = "", limit: int = 20):
        from apps.element_locator.models import Element
        from django.db.models import Q
        qs = Element.objects.select_related('page')
        if query:
            qs = qs.filter(
                Q(alias__icontains=query) | Q(text_val__icontains=query) |
                Q(resource_id__icontains=query) | Q(class_name__icontains=query)
            )
        return list(qs[:limit])

    @staticmethod
    def fetch_page_elements(page_id=None, page_label=None, limit=30):
        from apps.element_locator.models import Element, Page
        qs = Element.objects.select_related('page')
        if page_id:
            qs = qs.filter(page_id=page_id)
        elif page_label:
            page = Page.objects.filter(label=page_label).first()
            if page:
                qs = qs.filter(page_id=page.id)
        return list(qs[:limit])

    @staticmethod
    def element_count() -> int:
        from apps.element_locator.models import Element
        return Element.objects.count()
