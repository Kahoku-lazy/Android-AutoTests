"""Element tools — search UI elements and pages in the element-locator module."""
from agentscope.tool import ToolBase, ToolChunk
from agentscope.permission import PermissionDecision, PermissionBehavior, PermissionContext
from agentscope.message import TextBlock
from apps.element_locator.models import Element, Page
from apps.element_locator.api import get_test_points
from .db_helper import run_sync


class GetTestPointsTool(ToolBase):
    """List elements marked as test points, optionally filtered by page."""
    name = "get_test_points"
    description = "Query UI elements that are flagged as test points. Optionally filter by page IDs."
    input_schema = {
        "type": "object",
        "properties": {
            "page_ids": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "Optional list of page IDs to filter elements."
            },
        },
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, page_ids=None, **kwargs):
        elements = await run_sync(lambda: get_test_points(page_ids=page_ids))
        if not elements:
            return ToolChunk(content=[TextBlock(text="No test points found.")])
        lines = []
        for el in elements:
            page_name = el.page.label if el.page else "?"
            lines.append(f"- [{el.id}] {el.text_val or '(no text)'} | class={el.class_name} | resource_id={el.resource_id} | page={page_name}")
        return ToolChunk(content=[TextBlock(text=f"Test points ({len(elements)}):\n" + "\n".join(lines))])


class SearchElementsTool(ToolBase):
    """Search all UI elements by text, class, resource_id, or page name."""
    name = "search_elements"
    description = "Search UI elements by text content, class name, resource_id, or page name. Use before writing test cases to find valid XPath targets."
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Search keyword — matches text, class_name, resource_id, or page name."
            },
            "limit": {
                "type": "integer",
                "description": "Max results (default 20)."
            },
        },
        "required": ["query"],
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, query, limit=20, **kwargs):
        from django.db.models import Q
        qs = await run_sync(lambda: list(Element.objects.select_related('page').filter(
            Q(text_val__icontains=query) |
            Q(class_name__icontains=query) |
            Q(resource_id__icontains=query) |
            Q(page__label__icontains=query)
        )[:limit]))
        if not qs:
            return ToolChunk(content=[TextBlock(text=f"No elements matching '{query}'.")])
        lines = []
        for el in qs:
            import json
            try:
                xpath_cands = json.loads(el.xpath_candidates) if el.xpath_candidates else []
                first_xpath = xpath_cands[0]['xpath'] if xpath_cands else '?'
            except Exception:
                first_xpath = '?'
            lines.append(f"- [{el.id}] text='{el.text_val or ''}' class={el.class_name} res_id={el.resource_id} xpath={first_xpath} page={el.page.label if el.page else '?'}")
        return ToolChunk(content=[TextBlock(text=f"Results for '{query}' ({len(qs)}):\n" + "\n".join(lines))])
