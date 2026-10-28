"""
python -m 调试路径: engines.agents.middleware.rag_context

本模块的业务功能如下：
1. RagContextMiddleware: 用上下文里最后一条用户消息检索本地知识库，把命中片段追加到系统提示词。
2. build_rag_middleware: 按环境变量装配上述中间件，复用现有 rag 索引。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from agentscope.middleware import MiddlewareBase

from utils.logs import agent_event_log

from .envs import env_flag, env_int

if TYPE_CHECKING:
    from ..rag.service import RagService

RAG_ENABLED_ENV = "AGENT_RAG_ENABLED"
"""是否把 RAG 作为中间件注入；索引本身仍由 rag 配置（KNOWLEDGE_ASSISTANT_RAG_*）决定。"""

TOP_K_ENV = "AGENT_RAG_TOP_K"
"""覆盖检索条数；0 表示沿用 rag 配置。"""

DEFAULT_HEADER = "## 参考资料（来自本地知识库）"
DEFAULT_MAX_CHARS = 3000


class RagContextMiddleware(MiddlewareBase):
    """
    把本地知识库命中的片段追加到系统提示词。

    同一条用户消息只检索一次：后续 reasoning 步骤复用同一段上下文，避免每轮
    推理都打一次向量库。检索失败只记警告，原样返回系统提示词。

    Attributes:
        top_k: 检索条数；None 表示沿用 rag 配置。
    """

    def __init__(
        self,
        service: RagService,
        *,
        top_k: int | None = None,
        header: str = DEFAULT_HEADER,
        max_chars: int = DEFAULT_MAX_CHARS,
    ) -> None:
        """
        创建 RAG 上下文中间件。

        Args:
            service: 复用现有索引的检索服务。
            top_k: 覆盖检索条数；None 表示沿用 rag 配置。
            header: 注入段的标题。
            max_chars: 注入正文的字符上限。
        """
        self._service = service
        self.top_k = top_k
        self._header = header
        self._max_chars = max_chars
        self._query = ""
        self._block = ""

    @staticmethod
    def _last_user_text(agent: Any) -> str:
        """取上下文里最后一条用户消息的纯文本。

        Args:
            agent: 正在组装的智能体。

        Returns:
            文本；没有用户消息时为空串。
        """
        context = getattr(getattr(agent, "state", None), "context", None) or []
        for message in reversed(context):
            if str(getattr(message, "role", "")) != "user":
                continue
            reader = getattr(message, "get_text_content", None)
            text = reader() if callable(reader) else str(getattr(message, "content", "") or "")
            return str(text or "").strip()
        return ""

    async def _context_for(self, query: str) -> str:
        """检索一条查询并拼成注入段；失败或无命中返回空串。

        Args:
            query: 用户消息文本。

        Returns:
            注入段正文；没有可用资料时为空串。
        """
        from ..rag.service import format_context

        try:
            hits = await self._service.search(query, top_k=self.top_k)
        except Exception as exc:  # noqa: BLE001 - 检索失败不能打断回复
            agent_event_log.warning("RAG 中间件检索失败，已跳过注入：%s", exc)
            return ""
        if not hits:
            return ""
        return format_context(hits, self._max_chars)

    async def on_system_prompt(self, agent: Any, current_prompt: str) -> str:
        """组装系统提示词时追加一次检索结果。

        Args:
            agent: 正在组装的智能体。
            current_prompt: 上游给出的系统提示词。

        Returns:
            追加了参考资料的系统提示词；没命中或失败时原样返回。

        Raises:
            Exception: 不主动抛出；检索异常在内部降级。
        """
        query = self._last_user_text(agent)
        if not query:
            return current_prompt
        if query != self._query:
            self._query = query
            self._block = await self._context_for(query)
        if not self._block:
            return current_prompt
        return f"{current_prompt}\n\n{self._header}\n{self._block}"


def build_rag_middleware() -> RagContextMiddleware | None:
    """按环境变量装配 RAG 上下文中间件。

    Returns:
        装配好的中间件；未开启或索引未启用时返回 None。
    """
    if not env_flag(RAG_ENABLED_ENV):
        return None
    from ..rag.service import RagService

    service = RagService.from_env()
    if not service.enabled:
        agent_event_log.warning(
            "AGENT_RAG_ENABLED 已开启，但 rag 索引未启用（见 KNOWLEDGE_ASSISTANT_RAG_ENABLED）"
        )
        return None
    top_k = env_int(TOP_K_ENV, 0)
    return RagContextMiddleware(service, top_k=top_k or None)
