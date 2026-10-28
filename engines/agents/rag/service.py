"""
python -m 调试路径: engines.agents.rag.service

本模块的业务功能如下：
1. RagService: 懒加载索引、检索、把命中片段格式化为 LLM 上下文。
2. format_context(): 控制注入上下文的来源、相关度与长度。

RAG 失败只降级为空上下文，不向语音会话抛错。
"""

from __future__ import annotations

import asyncio

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import Any

from agentscope.credential import DashScopeCredential
from agentscope.embedding import (
    DashScopeEmbeddingModel,
    EmbeddingResponse,
)
from agentscope.rag import KnowledgeBase

from utils.logs import agent_event_log

from .config import RagConfig, load_rag_config
from .indexer import RagIndexer
from .store import SQLiteVectorStore


@dataclass(frozen=True)
class RagHit:
    """一条检索命中。"""

    source: str
    text: str
    score: float
    chunk_index: int
    document_id: str


class RagService:
    """
    语音 LLM 的 RAG 服务。

    Attributes:
        config: RAG 配置。
        enabled: 是否启用。
        error: 最近一次索引/检索失败原因；空字符串表示正常。
    """

    def __init__(
        self,
        config: RagConfig,
        usage_sink: Callable[[int], None] | None = None,
    ) -> None:
        """
        初始化 RAG 服务；不立即建索引。

        Args:
            config: RAG 配置。
            usage_sink: 嵌入 token 用量回调；用于写入用量账本。
        """
        self.config = config
        self.enabled = config.enabled
        self.error = ""
        self._usage_sink = usage_sink
        self._knowledge_base: KnowledgeBase | None = None
        self._indexer: RagIndexer | None = None
        self._lock = asyncio.Lock()
        self._ready = False
        self._failed = False
        self._indexed_count = 0

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        usage_sink: Callable[[int], None] | None = None,
    ) -> "RagService":
        """
        从环境变量创建服务。

        Args:
            environ: 测试注入的配置映射。
            usage_sink: 嵌入 token 用量回调。

        Returns:
            RagService 实例。
        """
        return cls(load_rag_config(environ), usage_sink=usage_sink)

    @property
    def indexed_count(self) -> int:
        """本次运行最近一次重建的文件数。"""
        return self._indexed_count

    async def ensure_index(self) -> int:
        """
        懒加载并增量更新索引。

        Returns:
            本次重建的文件数；未启用/失败时返回 0。
        """
        if not self.enabled:
            return 0
        async with self._lock:
            if self._ready:
                return self._indexed_count
            if self._failed:
                return 0
            try:
                embedding = _UsageEmbeddingModel(
                    credential=DashScopeCredential(api_key=self.config.api_key),
                    model=self.config.embedding_model,
                    dimensions=self.config.embedding_dimensions,
                    usage_sink=self._usage_sink,
                )
                store = SQLiteVectorStore(
                    self.config.index_dir / "rag.sqlite3",
                )
                knowledge_base = KnowledgeBase(
                    name="voice_knowledge",
                    description="语音助手本地产品资料",
                    embedding_model=embedding,
                    vector_store=store,
                    collection=self.config.collection,
                )
                indexer = RagIndexer(self.config, knowledge_base)
                self._indexed_count = await indexer.ensure_index()
                self._knowledge_base = knowledge_base
                self._indexer = indexer
                self._ready = True
            except Exception as exc:  # noqa: BLE001
                self._failed = True
                self.error = str(exc)
                agent_event_log.exception("RAG 索引失败: %s", exc)
            return self._indexed_count

    async def search(
        self,
        query: str,
        top_k: int | None = None,
    ) -> list[RagHit]:
        """
        检索相关资料。

        Args:
            query: 用户问题。
            top_k: 覆盖配置的返回条数。

        Returns:
            按相关度降序的命中；未启用/失败/无命中返回空列表。
        """
        query = query.strip()
        if not query or not self.enabled:
            return []
        await self.ensure_index()
        if self._knowledge_base is None or self.error:
            return []
        try:
            results = await self._knowledge_base.search(
                [query],
                top_k=top_k or self.config.top_k,
                score_threshold=self.config.score_threshold,
            )
        except Exception as exc:  # noqa: BLE001
            self.error = str(exc)
            agent_event_log.exception("RAG 检索失败: %s", exc)
            return []
        return [
            RagHit(
                source=result.chunk.source,
                text=result.chunk.content.text if hasattr(result.chunk.content, "text") else "",
                score=float(result.score),
                chunk_index=int(result.chunk.chunk_index),
                document_id=result.document_id,
            )
            for result in results
            if getattr(result.chunk.content, "text", "")
        ]

    async def build_context(self, query: str) -> str:
        """
        检索并格式化为可注入 LLM 的上下文。

        Args:
            query: 用户问题。

        Returns:
            命中时返回带来源/相关度的上下文；否则空字符串。
        """
        hits = await self.search(query)
        return format_context(hits, self.config.max_context_chars)


def format_context(hits: list[RagHit], max_chars: int) -> str:
    """
    把检索命中格式化为 LLM 上下文。

    Args:
        hits: 检索命中。
        max_chars: 上下文最大字符数。

    Returns:
        以「【检索资料】」开头的上下文；无命中返回空字符串。
    """
    if not hits:
        return ""
    lines = [
        "【检索资料】请优先依据以下资料回答；资料没有覆盖的内容不要编造。",
    ]
    used = len(lines[0])
    for index, hit in enumerate(hits, start=1):
        text = hit.text.strip()
        if not text:
            continue
        block = (
            f"[{index}] 来源：{hit.source}"
            f"（片段 {hit.chunk_index}，相关度 {hit.score:.2f}）\n{text}"
        )
        if used + len(block) > max_chars:
            remaining = max_chars - used
            if remaining <= 40:
                break
            block = block[:remaining]
        lines.append(block)
        used += len(block)
        if used >= max_chars:
            break
    return "\n\n".join(lines) if len(lines) > 1 else ""


class _UsageEmbeddingModel(DashScopeEmbeddingModel):
    """在 DashScope 嵌入模型上旁路记录 token 用量。"""

    def __init__(
        self,
        *args: Any,
        usage_sink: Callable[[int], None] | None = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(*args, **kwargs)
        self._usage_sink = usage_sink

    async def __call__(self, *args: Any, **kwargs: Any) -> EmbeddingResponse:
        response = await super().__call__(*args, **kwargs)
        tokens = getattr(getattr(response, "usage", None), "tokens", None)
        if tokens and self._usage_sink is not None:
            self._usage_sink(int(tokens))
        return response


__all__ = ["RagHit", "RagService", "format_context"]
