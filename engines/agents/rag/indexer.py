"""
python -m 调试路径: engines.agents.rag.indexer

本模块的业务功能如下：
1. RagIndexer: 扫描 rag_data 的 .md/.txt，解析、切块并写入 KnowledgeBase。
2. 按文件 mtime/size/切块策略版本做增量重建；未变化文件不重复嵌入。

本模块不读后端、不写数据库，只使用 AgentScope 的解析器/切块器和本地索引。
"""

from __future__ import annotations

import hashlib
import json

from agentscope.rag import KnowledgeBase, TextParser

from .chunker import CHUNKER_VERSION, MarkdownHeadingChunker
from .config import RagConfig


class RagIndexer:
    """
    本地 RAG 索引器。

    Attributes:
        config: RAG 配置。
        knowledge_base: AgentScope KnowledgeBase。
    """

    def __init__(self, config: RagConfig, knowledge_base: KnowledgeBase) -> None:
        """
        初始化索引器。

        Args:
            config: RAG 配置。
            knowledge_base: 已绑定嵌入模型与向量库的知识库句柄。
        """
        self.config = config
        self.knowledge_base = knowledge_base
        self._state_path = config.index_dir / "index_state.json"
        self._parser = TextParser()
        self._chunker = MarkdownHeadingChunker(
            parameters=MarkdownHeadingChunker.Parameters(
                chunk_size=config.chunk_size,
                overlap=config.chunk_overlap,
            ),
        )

    async def ensure_index(self) -> int:
        """
        确保索引与数据目录一致。

        Returns:
            本次重新索引的文件数。

        Raises:
            RuntimeError: 数据目录不存在。
        """
        if not self.config.data_dir.exists():
            raise RuntimeError(f"RAG 数据目录不存在：{self.config.data_dir}")
        self.config.index_dir.mkdir(parents=True, exist_ok=True)
        state = self._load_state()
        documents = {
            document.document_id: document
            for document in await self.knowledge_base.list_documents()
        }
        current: dict[str, list[int | str]] = {}
        reindexed = 0

        for path in sorted(self.config.data_dir.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in (".md", ".txt"):
                continue
            relative = path.relative_to(self.config.data_dir).as_posix()
            signature = [
                path.stat().st_mtime_ns,
                path.stat().st_size,
                CHUNKER_VERSION,
            ]
            current[relative] = signature
            document_id = _document_id(relative)
            if state.get(relative) == signature and document_id in documents:
                continue
            if document_id in documents:
                await self.knowledge_base.delete_document(document_id)
            sections = await self._parser.parse(path.read_bytes(), path.name)
            chunks = await self._chunker.chunk(sections)
            await self.knowledge_base.insert_document(
                chunks,
                document_id=document_id,
                document_metadata={
                    "filename": path.name,
                    "relative_path": relative,
                },
            )
            state[relative] = signature
            reindexed += 1

        for relative in set(state) - set(current):
            await self.knowledge_base.delete_document(_document_id(relative))
            state.pop(relative, None)

        self._write_state(state)
        return reindexed

    def _load_state(self) -> dict[str, list[int | str]]:
        """读取索引状态；损坏时按空状态处理。"""
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
                # 状态文件里的非法条目视为已损坏，跳过该文件；下次索引会按缺失重建
                continue
            version = str(value[2]) if len(value) >= 3 else ""
            loaded[str(key)] = [mtime, size, version]
        return loaded

    def _write_state(self, state: dict[str, list[int | str]]) -> None:
        """写索引状态；失败不影响本次索引结果。"""
        try:
            self._state_path.write_text(
                json.dumps(state, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError:
            return


def _document_id(relative_path: str) -> str:
    """按相对路径生成稳定的 document_id。"""
    digest = hashlib.sha1(relative_path.encode("utf-8")).hexdigest()[:16]
    return f"doc_{digest}"
