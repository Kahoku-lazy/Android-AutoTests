"""
python -m 调试路径: engines.agents.rag.tool

本模块的业务功能如下：
1. build_rag_tool(): 把 RagService 包装成 RealtimeAgent 可调用的 search_knowledge 工具。

Omni 直连没有可注入的文本 LLM，因此通过工具调用把检索结果交回实时模型。
"""

from __future__ import annotations

from agentscope.permission import PermissionBehavior, PermissionDecision
from agentscope.tool import FunctionTool

from .service import RagService

_ALLOW = PermissionDecision(PermissionBehavior.ALLOW, "本地只读产品资料检索")


def build_rag_tool(rag: RagService) -> FunctionTool:
    """
    构造 search_knowledge 工具。

    Args:
        rag: 已配置的 RAG 服务。

    Returns:
        FunctionTool，供 RealtimeAgent 调用。
    """

    async def search_knowledge(query: str) -> str:
        """检索本地产品资料并返回与问题相关的片段与来源。"""
        context = await rag.build_context(str(query or ""))
        return context or "没有检索到与问题相关的资料。"

    return FunctionTool(
        search_knowledge,
        name="search_knowledge",
        description=(
            "检索本地产品资料。当用户询问按键、指示灯、固件、恢复出厂、"
            "H717D 等产品相关问题时，先调用本工具，再依据返回资料回答；"
            "资料没有覆盖的内容不要编造。"
        ),
        is_read_only=True,
        permission=_ALLOW,
    )
