"""
文件名: ➡️ indexer.py 🏁
路径: ➡️ engines/ae_harness/knowledge/indexer.py 🏁
模块功能：➡️ 按库增量建索引：只扫 .md/.txt，未变化文件不重复嵌入 🏁
Python 调试：➡️ python -m engines.ae_harness.knowledge.indexer 🏁
时间：➡️ 2026-11-15 🏁
作者：➡️ kahoku 🏁
版本：➡️ 1.0.0 🏁
修改时间: ➡️ 2026-11-15 🏁
类型: ➡️ Harness 配置模块 🏁
简介说明：➡️
1. KnowledgeIndexer: 扫描一个库的资料目录，解析、切块并写入该库的 KnowledgeBase。
2. ensure_index(): 用修改时间、大小与切块版本判断是否需要重建；删除的文件同步清理。
🏁
关联模块：➡️
1. engines.ae_harness.knowledge.config: 库规格与切块参数。
2. agentscope.rag: TextParser / ApproxTokenChunker / KnowledgeBase。
🏁
测试：➡️
1. tests/engines/ae_harness/unit/test_knowledge_index.py: 增量跳过、删除清理与缺失目录
🏁
"""

from __future__ import annotations

import hashlib
import json

from pathlib import Path
from typing import Final

from agentscope.rag import ApproxTokenChunker, KnowledgeBase, TextParser

from .config import KnowledgeBaseSpec

__all__ = ["CHUNKER_VERSION", "KnowledgeIndexer"]

# 写入 index_state；切块策略变化时强制全量重建。
CHUNKER_VERSION: Final[str] = "approx_token_v1"
_SUFFIXES: Final[tuple[str, ...]] = (".md", ".txt")
_STATE_FILE: Final[str] = "index_state.json"


class KnowledgeIndexer:
    """
    一个本地库的增量索引器。

    Attributes:
        spec: 当前索引的库。
        knowledge_base: 已绑定嵌入模型、向量库和该库 collection 的句柄。
        index_dir: 索引状态根目录。
    """

    def __init__(
        self,
        spec: KnowledgeBaseSpec,
        knowledge_base: KnowledgeBase,
        *,
        index_dir: Path,
        chunk_size: int,
        chunk_overlap: int,
    ) -> None:
        """
        保存库规格、句柄与切块参数。

        Args:
            spec: 当前索引的库。
            knowledge_base: 该库的 KnowledgeBase 句柄。
            index_dir: 索引状态根目录。
            chunk_size: 每块近似 token 数。
            chunk_overlap: 相邻块重叠 token 数。
        """
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
        """
        确保索引与资料目录一致。

        Returns:
            本次重新索引的文件数；目录不存在时为 0。

        Raises:
            RuntimeError: 资料目录不存在。
        """
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

        for relative in set(state) - set(current):
            await self.knowledge_base.delete_document(_document_id(relative))
            state.pop(relative, None)

        self._write_state(state)
        return reindexed

    def _load_state(self) -> dict[str, list[int | str]]:
        """读取索引状态；文件缺失或损坏时按空状态处理。"""
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
