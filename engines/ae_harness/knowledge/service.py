from __future__ import annotations

import asyncio
import logging

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agentscope.rag import KnowledgeBase

from .config import INDEX_DIR, KnowledgeBaseSpec, KnowledgeConfig
from .indexer import KnowledgeIndexer
from .models import CreatedEmbedding, create_embedding_model
from .store import SQLiteVectorStore
from .usage import UsageEvent, UsageRecordingEmbedding, tag_events

__all__ = ["KnowledgeHit", "KnowledgeRetriever", "Retrieval"]

_LOG = logging.getLogger(__name__)
_DB_FILE = "rag.sqlite3"


@dataclass(frozen=True)
class KnowledgeHit:
    base: str
    source: str
    text: str
    score: float
    chunk_index: int
    document_id: str

    def as_dict(self) -> dict[str, object]:
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
    status: Literal["ok", "no_hit", "unavailable"]
    hits: tuple[KnowledgeHit, ...] = ()
    error: str = ""


class KnowledgeRetriever:
    def __init__(self, config: KnowledgeConfig, *, index_dir: Path | None = None) -> None:
        self.config = config
        self._index_dir = index_dir or INDEX_DIR
        self._embedding: CreatedEmbedding | None = None
        self._usage_proxy: UsageRecordingEmbedding | None = None
        self._usage: list[UsageEvent] = []
        self._lock = asyncio.Lock()
        self._ready: set[str] = set()
        self._errors: dict[str, str] = {}
        self._counts: dict[str, int] = {}

    def error(self, base: str) -> str:
        return self._errors.get(base, "")

    def indexed_count(self, base: str) -> int:
        return self._counts.get(base, 0)

    async def ensure_index(self, base: str) -> int:
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
            finally:
                self._collect_usage(phase="index", base=base)
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
        finally:
            self._collect_usage(phase="retrieve", base=base)
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

    def usage_events(self) -> list[UsageEvent]:
        self._collect_usage(phase="", base="")
        events = self._usage
        self._usage = []
        return events

    def _collect_usage(self, *, phase: str, base: str) -> None:
        if self._usage_proxy is not None:
            self._usage.extend(tag_events(self._usage_proxy.drain_events(), phase=phase, base=base))

    def _embedding_model(self) -> CreatedEmbedding:
        if self._embedding is None:
            self._embedding = create_embedding_model(self.config.embedding)
        return self._embedding

    def _proxy(self) -> UsageRecordingEmbedding:
        if self._usage_proxy is None:
            created = self._embedding_model()
            self._usage_proxy = UsageRecordingEmbedding(created.model, created.api_key_env)
        return self._usage_proxy

    def _store(self) -> SQLiteVectorStore:
        return SQLiteVectorStore(self._index_dir / _DB_FILE)

    def _knowledge(self, spec: KnowledgeBaseSpec, store: SQLiteVectorStore) -> KnowledgeBase:
        return KnowledgeBase(
            name=spec.name,
            description=spec.description,
            embedding_model=self._proxy(),
            vector_store=store,
            collection=spec.name,
        )
