"""
文件名: ➡️ service.py 🏁
路径: ➡️ engines/agents/rag/service.py 🏁
模块功能：➡️ 按库懒建索引，并返回未经聊天模型改写的检索命中 🏁
Python 调试：➡️ python -m engines.agents.rag.service 🏁
时间：➡️ 2026-10-28 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.1.0 🏁
修改时间: ➡️ 2026-11-11 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. KnowledgeBaseService: 按库名索引、检索并保留每个库的错误原因。
2. KnowledgeHit: 一条未经改写的检索命中。
3. RagService: 过渡别名，新增调用应使用 KnowledgeBaseService。
🏁
关联模块：➡️
1. engines.agents.config.config: 导入 load_model_config，读已注入密钥的模型表
2. engines.agents.models: 导入 create_model，按短名造嵌入模型
3. utils.logs: 导入 agent_event_log
🏁
测试：➡️
1. tests/engines/agents/unit/test_rag_retrieve.py: 按库检索、禁用库和失败重试
2. tests/engines/agents/unit/test_rag_store.py: 本地向量库单测
🏁
"""

from __future__ import annotations

import asyncio

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agentscope.embedding import EmbeddingResponse
from agentscope.rag import KnowledgeBase

from engines.agents.config.config import load_model_config
from engines.agents.models import create_model
from utils.logs import agent_event_log

from .catalog import KnowledgeBaseSpec, load_knowledge_catalog
from .config import RagConfig, load_rag_config
from .indexer import RagIndexer
from .store import SQLiteVectorStore


@dataclass(frozen=True)
class KnowledgeHit:
    """
    一条未经改写的检索命中。

    Attributes:
        base: 实际检索的库名。
        source: 来源文件。
        text: 片段正文。
        score: 余弦相似度。
        chunk_index: 文件内片段序号。
        document_id: 稳定文档编号。
    """

    base: str
    source: str
    text: str
    score: float
    chunk_index: int
    document_id: str


class KnowledgeBaseService:
    """
    按库名提供索引和检索。

    Attributes:
        config: 检索参数。
        enabled: 嵌入检索条件是否具备。
    """

    def __init__(
        self,
        config: RagConfig,
        catalog: tuple[KnowledgeBaseSpec, ...],
        usage_sink: Callable[[int], None] | None = None,
    ) -> None:
        """
        初始化服务；不立即建索引。

        Args:
            config: 检索参数。
            catalog: 已校验的知识库目录。
            usage_sink: 嵌入 token 用量回调。
        """
        self.config = config
        self.enabled = config.enabled
        self._catalog = {spec.name: spec for spec in catalog}
        self._usage_sink = usage_sink
        self._lock = asyncio.Lock()
        self._ready: set[str] = set()
        self._errors: dict[str, str] = {}
        self._indexed_counts: dict[str, int] = {}

    @classmethod
    def from_env(
        cls,
        environ: Mapping[str, str] | None = None,
        *,
        catalog_path: str | Path | None = None,
        usage_sink: Callable[[int], None] | None = None,
    ) -> "KnowledgeBaseService":
        """
        从环境变量和知识库目录创建服务。

        Args:
            environ: 测试注入的检索参数。
            catalog_path: 测试注入的库表路径。
            usage_sink: 嵌入 token 用量回调。

        Returns:
            未建索引的服务。

        Raises:
            ValueError: 知识库目录不合法。
        """
        return cls(
            load_rag_config(environ),
            load_knowledge_catalog(catalog_path),
            usage_sink=usage_sink,
        )

    def bases(self) -> tuple[str, ...]:
        """
        返回目录中的库名。

        Returns:
            按目录顺序排列的库名。
        """
        return tuple(self._catalog)

    def error(self, base: str) -> str:
        """
        返回一个库最近的可读错误。

        Args:
            base: 库名。

        Returns:
            错误原因；没有错误时为空字符串。
        """
        return self._errors.get(base, "")

    def indexed_count(self, base: str) -> int:
        """
        返回一个库最近一次重建的文件数。

        Args:
            base: 库名。

        Returns:
            重建文件数；尚未索引时为 0。
        """
        return self._indexed_counts.get(base, 0)

    async def ensure_index(self, base: str) -> int:
        """
        懒加载并增量更新一个库。

        Args:
            base: 库名。

        Returns:
            本次重建文件数；库不可用时返回 0。
        """
        spec = self._catalog.get(base)
        if spec is None:
            self._errors[base] = f"知识库不存在：{base}"
            return 0
        if not spec.enabled:
            self._errors[base] = f"知识库已禁用：{base}"
            return 0
        if not self.enabled:
            self._errors[base] = "嵌入检索未启用"
            return 0
        async with self._lock:
            if base in self._ready:
                return self._indexed_counts.get(base, 0)
            self._errors.pop(base, None)
            try:
                async with self._store() as store:
                    knowledge = self._knowledge(spec, store)
                    count = await RagIndexer(self.config, spec, knowledge).ensure_index()
            except Exception as exc:  # noqa: BLE001
                self._errors[base] = str(exc)
                agent_event_log.exception("知识库 %s 索引失败: %s", base, exc)
                return 0
            self._indexed_counts[base] = count
            self._ready.add(base)
            return count

    async def retrieve(
        self,
        base: str,
        query: str,
        top_k: int | None = None,
    ) -> list[KnowledgeHit]:
        """
        检索一个指定库。

        Args:
            base: 库名。
            query: 检索问题。
            top_k: 覆盖默认返回条数。

        Returns:
            按相似度降序的原始命中；不可用或无命中时返回空列表。
        """
        query = query.strip()
        if not query:
            self._errors[base] = "检索问题不能为空"
            return []
        await self.ensure_index(base)
        if self.error(base):
            return []
        spec = self._catalog[base]
        try:
            async with self._store() as store:
                results = await self._knowledge(spec, store).search(
                    [query],
                    top_k=top_k or self.config.top_k,
                    score_threshold=self.config.score_threshold,
                )
        except Exception as exc:  # noqa: BLE001
            self._ready.discard(base)
            self._errors[base] = str(exc)
            agent_event_log.exception("知识库 %s 检索失败: %s", base, exc)
            return []
        hits = [
            KnowledgeHit(
                base=base,
                source=result.chunk.source,
                text=getattr(result.chunk.content, "text", ""),
                score=float(result.score),
                chunk_index=int(result.chunk.chunk_index),
                document_id=result.document_id,
            )
            for result in results
            if getattr(result.chunk.content, "text", "")
        ]
        return _truncate_hits(hits, self.config.max_context_chars)

    def _store(self) -> SQLiteVectorStore:
        """打开本地向量库。"""
        return SQLiteVectorStore(self.config.index_dir / "rag.sqlite3")

    def _knowledge(self, spec: KnowledgeBaseSpec, store: SQLiteVectorStore) -> KnowledgeBase:
        """绑定一个库自己的 collection。"""
        return KnowledgeBase(
            name=spec.name,
            description=spec.description,
            embedding_model=_UsageEmbedding(
                create_model(load_model_config(), "text_embedding_v4"),
                self._usage_sink,
            ),
            vector_store=store,
            collection=spec.name,
        )


class _UsageEmbedding:
    """在已建好的嵌入模型外包一层用量记录，不把回调传进创建出口。"""

    def __init__(self, model: Any, usage_sink: Callable[[int], None] | None) -> None:
        """保存模型和回调。

        Args:
            model: create_model 返回的嵌入模型。
            usage_sink: 嵌入 token 用量回调；None 表示不记录。
        """
        self._model = model
        self._usage_sink = usage_sink

    def __getattr__(self, name: str) -> Any:
        """其余属性转给底层模型。

        Args:
            name: 属性名。

        Returns:
            底层模型的同名属性。
        """
        return getattr(self._model, name)

    async def __call__(self, *args: Any, **kwargs: Any) -> EmbeddingResponse:
        """调用嵌入模型，成功后上报 token；上报失败不打断检索。

        Args:
            *args: 传给底层模型。
            **kwargs: 传给底层模型。

        Returns:
            底层模型的嵌入响应。
        """
        response = await self._model(*args, **kwargs)
        tokens = getattr(getattr(response, "usage", None), "tokens", None)
        if tokens and self._usage_sink is not None:
            try:
                self._usage_sink(int(tokens))
            except Exception:  # noqa: BLE001
                agent_event_log.exception("嵌入用量回调失败")
        return response


def _truncate_hits(hits: list[KnowledgeHit], max_chars: int) -> list[KnowledgeHit]:
    """按单条正文截断，不把多条命中拼成提示词。"""
    truncated: list[KnowledgeHit] = []
    for hit in hits:
        text = hit.text.strip()
        if not text:
            continue
        if len(text) > max_chars:
            text = text[:max_chars]
        truncated.append(
            KnowledgeHit(
                hit.base,
                hit.source,
                text,
                hit.score,
                hit.chunk_index,
                hit.document_id,
            )
        )
    return truncated


RagService = KnowledgeBaseService

__all__ = ["KnowledgeBaseService", "KnowledgeHit", "RagService"]
