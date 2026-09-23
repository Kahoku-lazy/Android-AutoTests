"""element_locator DRF ViewSets — Android PageFlow.

Page tree + Page elements (device-dependent, complex validation) remain
as plain Django views in views_pages.py / views_page_elements.py.
"""

from rest_framework import viewsets

from .models import PageFlow
from .serializers import PageFlowSerializer

# ═══════════════════════════════════════════════════════
# PageFlow ViewSet (Android)
# ═══════════════════════════════════════════════════════


class PageFlowViewSet(viewsets.ModelViewSet):
    """Android page navigation flow — list + create + destroy."""

    serializer_class = PageFlowSerializer
    http_method_names = ["get", "post", "delete", "head", "options"]

    def get_queryset(self):
        return PageFlow.objects.select_related("from_page", "to_page", "trigger_element").order_by(
            "-created_at"
        )
