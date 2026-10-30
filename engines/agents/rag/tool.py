"""
文件名: ➡️ tool.py 🏁
路径: ➡️ engines/agents/rag/tool.py 🏁
模块功能：➡️ Omni 直连没有可注入的文本 LLM，因此通过工具调用把检索结果交回实时模型 🏁
Python 调试：➡️ python -m engines.agents.rag.tool 🏁
时间：➡️ 2026-10-28 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. build_rag_tool(): 把 RagService 包装成 RealtimeAgent 可调用的 search_knowledge 工具。
🏁
关联模块：➡️
1. 暂无本地 engines/utils 依赖
🏁
测试：➡️
1. tests/graybox/unit/test_case_plan_tools.py: 计划模式工具：装配四件套，并验证它们读写同一份 AgentState
2. tests/graybox/unit/test_forced_handover_thinking.py: 强制交卷时关闭思考，未满轮次的请求保持原样
3. tests/graybox/unit/test_model_retry_middleware.py: 模型重试与回退中间件：分类判定、退避序列、回退、流式首块、环境变量解析
4. tests/graybox/unit/test_rag_store.py: RAG 本地向量库与上下文格式化单测：不联网、不依赖 rag_data
🏁
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
