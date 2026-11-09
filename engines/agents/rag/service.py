"""
文件名: ➡️ service.py 🏁
路径: ➡️ engines/agents/rag/service.py 🏁
模块功能：➡️ 检索服务：懒建索引、检索并把命中片段格式化成注入上下文 🏁
Python 调试：➡️ python -m engines.agents.rag.service 🏁
时间：➡️ 2026-10-28 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-10-30 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. RagService: 懒加载索引、检索、把命中片段格式化为 LLM 上下文。
2. format_context(): 控制注入上下文的来源、相关度与长度。
🏁
关联模块：➡️
1. engines.agents.models: 导入 get_embedding_model，取嵌入模型实例
2. utils.logs: 导入 agent_event_log
🏁
测试：➡️
1. tests/graybox/unit/test_agent_middleware_assembly.py: 中间件装配：默认集合、顺序、各能力开关与单项失败隔离
2. tests/graybox/unit/test_rag_store.py: RAG 本地向量库与上下文格式化单测：不联网、不依赖 rag_data
🏁
"""

from __future__ import annotations

import asyncio

from collections.abc import Callable, Mapping
from dataclasses import dataclass

from agentscope.rag import KnowledgeBase

from engines.agents.models import get_embedding_model
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
                embedding = get_embedding_model(
                    self.config.api_key,
                    model_name=self.config.embedding_model,
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


__all__ = ["RagHit", "RagService", "format_context"]
