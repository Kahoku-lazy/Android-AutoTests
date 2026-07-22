"""Element tools — search UI elements and pages in the element-locator module."""
from agentscope.tool import ToolBase, ToolChunk
from agentscope.permission import PermissionDecision, PermissionBehavior, PermissionContext
from agentscope.message import TextBlock
from apps.element_locator.models import Element, Page, PageFlow
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


class ListPagesTool(ToolBase):
    """List all recorded pages in the element-locator module."""

    name = "list_pages"
    description = """列出所有已录制的页面及其元素数量。

【触发条件】
- Android UI 自动化探索阶段（Step 3）
- 需要先了解有哪些页面可用，再调用 fetch_page_elements 获取具体元素
- 用户问"平台上有哪些页面"

【返回】
- 页面 ID、名称、所属 App、元素数量
- flow_out / flow_in 表示页面跳转入度出度（需配合 fetch_page_flows 使用）"""
    input_schema = {
        "type": "object",
        "properties": {
            "limit": {"type": "integer", "description": "最多返回条数（默认 30）"},
        },
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, limit=30, **kwargs):
        pages = await run_sync(lambda: list(Page.objects.filter(
            is_folder=False
        ).order_by("-updated_at")[:limit]))

        if not pages:
            return ToolChunk(content=[TextBlock(
                text="没有找到已录制的页面。请先在元素定位模块连接设备并 dump UI。"
            )])

        lines = [f"已录制页面 ({len(pages)}):"]
        for p in pages:
            el_count = p.element_count if hasattr(p, 'element_count') else 0
            pkg = p.package or ""
            lines.append(f"- [id={p.id}] {p.label} | 包={pkg} | 元素={el_count}")

        lines.append("\n用 fetch_page_elements(page_id=...) 获取页面上的具体元素。")
        lines.append("用 fetch_page_flows() 查看页面间跳转关系。")
        return ToolChunk(content=[TextBlock(text="\n".join(lines))])


class FetchPageFlowsTool(ToolBase):
    """Query page navigation flows (from_page → to_page edges)."""

    name = "fetch_page_flows"
    description = """查询页面跳转流（el_page_flows 表），获取页面导航关系图。

【触发条件】
- Android UI 自动化探索阶段（Step 3）
- 了解页面之间如何跳转（from → to，含触发元素）
- 设计跨页面测试场景时

【返回】
- 所有 PageFlow 记录：源页面 → 目标页面（触发: 元素文本, 动作类型）
- 可按 from_page_id / to_page_id 过滤
- 按源页面分组输出

【区分】
- fetch_page_flows: 运行时设备录制的导航边（el_page_flows）
- list_workflow_documents: 设计时创建的页面流转图（wf_documents）
- 两者互补，共同描绘页面导航全貌"""
    input_schema = {
        "type": "object",
        "properties": {
            "from_page_id": {"type": "integer", "description": "可选：只查从该页面出发的跳转"},
            "to_page_id": {"type": "integer", "description": "可选：只查到该页面的跳转"},
        },
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        from .tool_context import check_platform_permission
        return check_platform_permission(self)

    async def call(self, from_page_id=None, to_page_id=None, **kwargs):
        def _fetch():
            qs = PageFlow.objects.select_related("from_page", "to_page", "trigger_element")
            if from_page_id:
                qs = qs.filter(from_page_id=from_page_id)
            if to_page_id:
                qs = qs.filter(to_page_id=to_page_id)
            return list(qs.order_by("from_page_id", "id"))

        flows = await run_sync(_fetch)
        if not flows:
            return ToolChunk(content=[TextBlock(
                text="没有找到页面跳转流。请先在元素定位模块连接设备并录制页面跳转关系。"
            )])

        from collections import defaultdict
        grouped = defaultdict(list)
        for f in flows:
            fl = f.from_page.label if f.from_page else f"Page#{f.from_page_id}"
            tl = f.to_page.label if f.to_page else f"Page#{f.to_page_id}"
            trigger = (
                f.trigger_element.text_val or f.trigger_element.resource_id
                or f"Element#{f.trigger_element_id}"
            ) if f.trigger_element else "?"
            grouped[fl].append(f"  → {tl} (触发: {trigger}, 动作: {f.trigger_action})")

        fc = len(set(f.from_page_id for f in flows))
        tc = len(set(f.to_page_id for f in flows))
        lines = [f"页面导航流 ({len(flows)} 条，{fc} 源页面 → {tc} 目标页面):"]
        for from_lbl, targets in sorted(grouped.items()):
            lines.append(f"- [{from_lbl}]")
            lines.extend(targets[:15])
            if len(targets) > 15:
                lines.append(f"  ... 还有 {len(targets) - 15} 条")

        return ToolChunk(content=[TextBlock(text="\n".join(lines))])
