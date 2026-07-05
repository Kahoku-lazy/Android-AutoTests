"""Report tools — save and query test reports."""
from agentscope.tool import ToolBase, ToolChunk
from agentscope.permission import PermissionDecision, PermissionBehavior, PermissionContext
from agentscope.message import TextBlock
from apps.report_generator.api import save_report
from apps.report_generator.models import Report
from .db_helper import run_sync


class SaveReportTool(ToolBase):
    """Save a test report record."""
    name = "save_report"
    description = "Save a test report record linked to a test run."
    input_schema = {
        "type": "object",
        "properties": {
            "run_id": {
                "type": "string",
                "description": "The test run ID this report is for."
            },
            "title": {
                "type": "string",
                "description": "Report title."
            },
            "file_type": {
                "type": "string",
                "description": "Report file type: 'csv', 'json', 'html', 'md' (default 'json')."
            },
            "file_path": {
                "type": "string",
                "description": "Path to the generated report file."
            },
        },
        "required": ["run_id", "title", "file_path"],
    }
    is_concurrency_safe = True
    is_read_only = False

    async def check_permissions(self, tool_input, context):
        return PermissionDecision(behavior=PermissionBehavior.ALLOW, message="Report saving is always allowed.")

    async def call(self, run_id, title, file_path, file_type="json", **kwargs):
        obj = await run_sync(lambda: save_report(run_id=run_id, title=title, file_type=file_type, file_path=file_path))
        return ToolChunk(content=[TextBlock(
            text=f"Report saved.\nID: {obj.id}\nTitle: {title}\nType: {file_type}\nPath: {file_path}"
        )])


class ListReportsTool(ToolBase):
    """List existing reports."""
    name = "list_reports"
    description = "List all saved test reports."
    input_schema = {
        "type": "object",
        "properties": {},
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        return PermissionDecision(behavior=PermissionBehavior.ALLOW, message="Read-only report listing.")

    async def call(self, **kwargs):
        reports = await run_sync(lambda: list(Report.objects.order_by('-created_at')[:30]))
        if not reports:
            return ToolChunk(content=[TextBlock(text="No reports found.")])
        lines = [f"- [{r.id}] {r.title} | run={r.run_id} | type={r.file_type} | {r.created_at.strftime('%Y-%m-%d %H:%M')}" for r in reports]
        return ToolChunk(content=[TextBlock(text=f"Reports ({len(reports)}):\n" + "\n".join(lines))])
