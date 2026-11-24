from __future__ import annotations

import hashlib
import json
import logging

from pathlib import Path
from typing import Final

from agentscope.rag import ApproxTokenChunker, KnowledgeBase, TextParser

from .config import KnowledgeBaseSpec

__all__ = ["CHUNKER_VERSION", "KnowledgeIndexer"]

_LOG = logging.getLogger(__name__)

CHUNKER_VERSION: Final[str] = "approx_token_v1"
_SUFFIXES: Final[tuple[str, ...]] = (".md", ".txt")
_STATE_FILE: Final[str] = "index_state.json"


class KnowledgeIndexer:
    def __init__(
        self,
        spec: KnowledgeBaseSpec,
        knowledge_base: KnowledgeBase,
        *,
        index_dir: Path,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        self.spec = spec
        self.knowledge_base = knowledge_base
        self._state_path = index_dir / "collections" / spec.name / _STATE_FILE
        self._parser = TextParser()
        self._chunker = ApproxTokenChunker(
            parameters=ApproxTokenChunker.Parameters(
                chunk_size=chunk_size,
                overlap=chunk_overlap,
            ),
        )

    async def ensure_index(self) -> int:
        if not self.spec.data_dir.exists():
            raise RuntimeError(f"知识库资料目录不存在：{self.spec.name}: {self.spec.data_dir}")
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        state = self._load_state()
        documents = {
            document.document_id: document
            for document in await self.knowledge_base.list_documents()
        }
        current: dict[str, list[int | str]] = {}
        reindexed = 0

        for path in sorted(self.spec.data_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in _SUFFIXES:
                continue
            relative = path.relative_to(self.spec.data_dir).as_posix()
            stat = path.stat()
            signature: list[int | str] = [int(stat.st_mtime_ns), int(stat.st_size), CHUNKER_VERSION]
            current[relative] = signature
            document_id = _document_id(relative)
            if list(state.get(relative, [])) == signature and document_id in documents:
                continue
            if document_id in documents:
                await self.knowledge_base.delete_document(document_id)
            sections = await self._parser.parse(path.read_bytes(), path.name)
            chunks = await self._chunker.chunk(sections)
            await self.knowledge_base.insert_document(
                chunks,
                document_id=document_id,
                document_metadata={"filename": path.name, "relative_path": relative},
            )
            state[relative] = signature
            reindexed += 1

        stale = {item.document_id for item in documents.values()} - {
            _document_id(relative) for relative in current
        }
        for document_id in sorted(stale):
            await self.knowledge_base.delete_document(document_id)
        for relative in set(state) - set(current):
            state.pop(relative, None)

        self._write_state(state)
        return reindexed

    def _load_state(self) -> dict[str, list[int | str]]:
        if not self._state_path.exists():
            return {}
        try:
            data = json.loads(self._state_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return {}
        if not isinstance(data, dict):
            return {}
        loaded: dict[str, list[int | str]] = {}
        for key, value in data.items():
            if not isinstance(value, list) or len(value) < 2:
                continue
            try:
                mtime = int(value[0])
                size = int(value[1])
            except (TypeError, ValueError):
                continue  # silent-except
            version = str(value[2]) if len(value) >= 3 else ""
            loaded[str(key)] = [mtime, size, version]
        return loaded

    def _write_state(self, state: dict[str, list[int | str]]) -> None:
        try:
            self._state_path.write_text(
                json.dumps(state, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            _LOG.warning("知识库 %s 的索引状态写失败，下次会按文件重新嵌入", self.spec.name)


def _document_id(relative_path: str) -> str:
    digest = hashlib.sha1(relative_path.encode("utf-8")).hexdigest()[:16]
    return f"doc_{digest}"
