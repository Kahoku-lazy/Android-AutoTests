"""
文件名: ➡️ service.py 🏁
路径: ➡️ engines/ae_harness/knowledge/service.py 🏁
模块功能：➡️ 按库懒建索引并返回未经改写的检索命中，失败只降级不抛异常 🏁
Python 调试：➡️ python -m engines.ae_harness.knowledge.service 🏁
时间：➡️ 2026-11-15 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-15 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. KnowledgeHit: 一条未经改写的检索命中。
2. Retrieval: 一次检索的结果，区分「有命中」「无命中」「检索不可用」。
3. KnowledgeRetriever: 首次使用时才造嵌入模型、开库、建索引；不跨事件循环复用。
🏁
关联模块：➡️
1. engines.ae_harness.knowledge.config: 库目录与检索参数。
2. engines.ae_harness.knowledge.indexer: 按库增量索引。
3. engines.ae_harness.knowledge.store: 本地 SQLite 向量库。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_knowledge_retrieve.py: 命中字段、无命中与不可用
🏁
"""

from __future__ import annotations

import asyncio
import logging

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agentscope.rag import KnowledgeBase

from .config import INDEX_DIR, KnowledgeBaseSpec, KnowledgeConfig, load_config
from .indexer import KnowledgeIndexer
from .models import CreatedEmbedding, create_embedding_model
from .store import SQLiteVectorStore

__all__ = ["KnowledgeHit", "KnowledgeRetriever", "Retrieval"]

_LOG = logging.getLogger(__name__)
_DB_FILE = "rag.sqlite3"


@dataclass(frozen=True)
class KnowledgeHit:
    """
    一条未经改写的检索命中。

    Attributes:
        base: 命中来自哪个库。
        source: 来源文件名。
        text: 片段正文。
        score: 余弦相似度，越大越相关。
        chunk_index: 文件内片段序号。
        document_id: 稳定文档编号。
    """

    base: str
    source: str
    text: str
    score: float
    chunk_index: int
    document_id: str

    def as_dict(self) -> dict[str, object]:
        """
        转成可直接序列化的字典。

        Returns:
            六个验收字段组成的字典。
        """
        return {
            "base": self.base,
            "source": self.source,
            "text": self.text,
            "score": round(self.score, 4),
            "chunk_index": self.chunk_index,
            "document_id": self.document_id,
        }


@dataclass(frozen=True)
class Retrieval:
    """
    一次检索的结果。

    Attributes:
        status: ok 表示有命中；no_hit 表示库可用但无命中；unavailable 表示检索不可用。
        hits: 命中列表，按相似度降序。
        error: 不可用时的可读原因；其余情况为空串。
    """

    status: Literal["ok", "no_hit", "unavailable"]
    hits: tuple[KnowledgeHit, ...] = ()
    error: str = ""


class KnowledgeRetriever:
    """
    一个进程内的知识库检索器。

    惰性初始化：构造时不读配置以外的任何东西、不连库、不建索引。每次入口新建一个，
    **不要跨事件循环复用**（内部有 asyncio.Lock）。

    Attributes:
        config: 知识库配置。
    """

    def __init__(self, config: KnowledgeConfig, *, index_dir: Path | None = None) -> None:
        """
        保存配置；不做任何 IO。

        Args:
            config: 已装载的知识库配置。
            index_dir: 索引目录；None 时用模块自带的 index/。
        """
        self.config = config
        self._index_dir = index_dir or INDEX_DIR
        self._embedding: CreatedEmbedding | None = None
        self._lock = asyncio.Lock()
        self._ready: set[str] = set()
        self._errors: dict[str, str] = {}
        self._counts: dict[str, int] = {}

    @classmethod
    def from_config(cls, **kwargs: object) -> "KnowledgeRetriever":
        """
        用模块自带的配置创建检索器。

        Args:
            **kwargs: 透传给 load_config 的路径覆盖参数。

        Returns:
            未初始化的检索器。
        """
        return cls(load_config(**kwargs))  # type: ignore[arg-type]

    def error(self, base: str) -> str:
        """
        返回一个库最近的可读错误。

        Args:
            base: 库名。

        Returns:
            错误原因；没有错误时为空串。
        """
        return self._errors.get(base, "")

    def indexed_count(self, base: str) -> int:
        """
        返回一个库最近一次重建的文件数。

        Args:
            base: 库名。

        Returns:
            文件数；尚未索引时为 0。
        """
        return self._counts.get(base, 0)

    async def ensure_index(self, base: str) -> int:
        """
        懒建并增量更新一个库。

        Args:
            base: 库名。

        Returns:
            本次重新索引的文件数；库不可用时为 0。
        """
        spec = self.config.base(base)
        if spec is None:
            self._errors[base] = f"知识库不存在：{base}"
            return 0
        if not spec.enabled:
            self._errors[base] = f"知识库已禁用：{base}"
            return 0
        async with self._lock:
            if base in self._ready:
                return self._counts.get(base, 0)
            self._errors.pop(base, None)
            try:
                async with self._store() as store:
                    knowledge = self._knowledge(spec, store)
                    count = await KnowledgeIndexer(
                        spec,
                        knowledge,
                        index_dir=self._index_dir,
                        chunk_size=self.config.chunk_size,
                        chunk_overlap=self.config.chunk_overlap,
                    ).ensure_index()
            except Exception as exc:  # noqa: BLE001 - 单库失败只降级，不打断调用方
                self._errors[base] = str(exc)
                _LOG.exception("知识库 %s 索引失败: %s", base, exc)
                return 0
            self._counts[base] = count
            self._ready.add(base)
            return count

    async def retrieve(
        self,
        query: str,
        *,
        base: str | None = None,
        top_k: int | None = None,
    ) -> Retrieval:
        """
        检索一个库或全部启用库。

        Args:
            query: 检索问题。
            base: 指定库名；None 时检索全部启用库并合并排序。
            top_k: 覆盖默认返回条数；None 或非正数时用配置值。

        Returns:
            检索结果；任何失败都降级成 unavailable，不抛异常。
        """
        text = query.strip()
        if not text:
            return Retrieval("unavailable", error="检索问题不能为空")
        targets = self._targets(base)
        if isinstance(targets, Retrieval):
            return targets
        limit = top_k if isinstance(top_k, int) and top_k > 0 else self.config.top_k
        hits: list[KnowledgeHit] = []
        errors: list[str] = []
        for name in targets:
            hits.extend(await self._search_one(name, text, limit))
            if self._errors.get(name):
                errors.append(f"{name}: {self._errors[name]}")
        if not hits:
            if errors:
                return Retrieval("unavailable", error="；".join(errors))
            return Retrieval("no_hit")
        hits.sort(key=lambda hit: hit.score, reverse=True)
        return Retrieval("ok", hits=tuple(hits[:limit]))

    def _targets(self, base: str | None) -> tuple[str, ...] | Retrieval:
        """确定要检索的库；参数不合法时直接给出降级结果。"""
        if base:
            spec = self.config.base(base)
            if spec is None:
                return Retrieval("unavailable", error=f"知识库不存在：{base}")
            if not spec.enabled:
                return Retrieval("unavailable", error=f"知识库已禁用：{base}")
            return (base,)
        enabled = tuple(spec.name for spec in self.config.enabled_bases())
        if not enabled:
            return Retrieval("unavailable", error="没有启用的知识库")
        return enabled

    async def _search_one(self, base: str, query: str, top_k: int) -> list[KnowledgeHit]:
        """检索单个库；失败时写错误并返回空列表。"""
        await self.ensure_index(base)
        if self._errors.get(base):
            return []
        spec = self.config.base(base)
        if spec is None:
            return []
        try:
            async with self._store() as store:
                results = await self._knowledge(spec, store).search(
                    [query],
                    top_k=top_k,
                    score_threshold=self.config.score_threshold,
                )
        except Exception as exc:  # noqa: BLE001 - 检索失败只降级
            self._ready.discard(base)
            self._errors[base] = str(exc)
            _LOG.exception("知识库 %s 检索失败: %s", base, exc)
            return []
        return [
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

    def _embedding_model(self) -> CreatedEmbedding:
        """懒造嵌入模型；同一实例内只造一次。"""
        if self._embedding is None:
            self._embedding = create_embedding_model(self.config.embedding)
        return self._embedding

    def _store(self) -> SQLiteVectorStore:
        """打开本地向量库。"""
        return SQLiteVectorStore(self._index_dir / _DB_FILE)

    def _knowledge(self, spec: KnowledgeBaseSpec, store: SQLiteVectorStore) -> KnowledgeBase:
        """把库名、嵌入模型与向量库绑成一个句柄。"""
        return KnowledgeBase(
            name=spec.name,
            description=spec.description,
            embedding_model=self._embedding_model().model,
            vector_store=store,
            collection=spec.name,
        )
