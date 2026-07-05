"""RAG tool — search the project knowledge base."""
from agentscope.tool import ToolBase, ToolChunk
from agentscope.permission import PermissionDecision, PermissionBehavior, PermissionContext
from agentscope.message import TextBlock
from ..rag.document_store import search as kb_search
from .db_helper import run_sync


class KnowledgeBaseSearchTool(ToolBase):
    """Search the project knowledge base for documentation, references, and examples."""
    name = "search_knowledge_base"
    description = (
        "Search the project knowledge base for documentation, API references, step type definitions, "
        "test case templates, and architecture guides. Use this when you need context about how to write "
        "test cases, what step types are available, or how the platform works."
    )
    input_schema = {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": "Natural language search query."
            },
            "top_k": {
                "type": "integer",
                "description": "Number of results to return (default 5)."
            },
        },
        "required": ["query"],
    }
    is_concurrency_safe = True
    is_read_only = True

    async def check_permissions(self, tool_input, context):
        return PermissionDecision(behavior=PermissionBehavior.ALLOW, message="Read-only knowledge search.")

    async def call(self, query, top_k=5, **kwargs):
        # Quick check: if collection is empty or unavailable, return immediately
        # instead of blocking for 10+ seconds downloading ONNX models
        from ..rag.document_store import _get_collection
        try:
            col = await run_sync(lambda: _get_collection(), timeout=5)
        except Exception:
            return ToolChunk(content=[TextBlock(
                text="知识库暂不可用（ChromaDB 未初始化）。请直接基于平台工具操作，无需查阅知识库。"
            )])
        if col is None:
            return ToolChunk(content=[TextBlock(
                text="知识库暂不可用（ChromaDB 未初始化）。请直接基于平台工具操作，无需查阅知识库。"
            )])
        try:
            col_count = await run_sync(lambda: col.count(), timeout=3)
        except Exception:
            return ToolChunk(content=[TextBlock(
                text="知识库查询超时，请直接使用平台工具操作。"
            )])
        if col_count == 0:
            return ToolChunk(content=[TextBlock(
                text="知识库为空，暂无可检索的文档。请直接使用平台工具（save_test_case, fetch_page_elements 等）操作。"
            )])

        try:
            results = await run_sync(lambda: kb_search(query, top_k=top_k), timeout=8)
        except Exception:
            return ToolChunk(content=[TextBlock(
                text=f"知识库搜索 '{query}' 超时，请直接使用平台工具操作。"
            )])
        if not results:
            return ToolChunk(content=[TextBlock(text=f"No knowledge base results for '{query}'.")])
        lines = []
        for i, r in enumerate(results):
            meta = r.get('metadata', {})
            source = meta.get('source', 'unknown')
            lines.append(f"### Result {i+1} (source: {source}, score: {r['score']:.3f})")
            lines.append(r['content'][:1000])
            lines.append("")
        return ToolChunk(content=[TextBlock(text="\n".join(lines))])
