"""
模块功能：➡️ 评测语料只读采样与 gold 文档映射 🏁
Python 调试：➡️ python -m backend.apps.knowledge_search.eval_corpus 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 knowledge_search 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from __future__ import annotations

import random

from pathlib import Path

_SUFFIXES = (".md", ".txt")


async def sample_chunks(
    data_dir: Path,
    *,
    chunk_size: int,
    chunk_overlap: int,
    count: int,
    seed: int,
) -> list[dict]:
    """
    只读扫描资料目录，切块后带种子均匀采样。

    Args:
        data_dir: 资料目录。
        chunk_size: 每块近似 token 数（与索引一致）。
        chunk_overlap: 相邻块重叠 token 数。
        count: 采样块数上限。
        seed: 随机种子（随运行落库，可复现）。

    Returns:
        块字典列表：source / relative_path / chunk_index / text。

    Raises:
        RuntimeError: 资料目录不存在。
    """
    from agentscope.rag import ApproxTokenChunker, TextParser

    if not data_dir.exists():
        raise RuntimeError(f"资料目录不存在：{data_dir}")
    parser = TextParser()
    chunker = ApproxTokenChunker(
        parameters=ApproxTokenChunker.Parameters(chunk_size=chunk_size, overlap=chunk_overlap)
    )
    chunks: list[dict] = []
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in _SUFFIXES:
            continue
        sections = await parser.parse(path.read_bytes(), path.name)
        for chunk in await chunker.chunk(sections):
            chunks.append(
                {
                    "source": path.name,
                    "relative_path": path.relative_to(data_dir).as_posix(),
                    "chunk_index": int(chunk.chunk_index),
                    "text": chunk.content.text,
                }
            )
    rng = random.Random(seed)
    rng.shuffle(chunks)
    return chunks[: max(count, 0)]


async def gold_document_map(
    module_name: str,
    description: str,
    embedding_spec,
    index_dir: Path,
) -> dict[str, str]:
    """
    经引擎公开 list_documents 建「文件名 / 相对路径 → 文档编号」映射。

    Args:
        module_name: 库名（即集合名）。
        description: 库说明。
        embedding_spec: 引擎向量模型配置。
        index_dir: 索引根目录。

    Returns:
        映射字典；同名文件以相对路径键消歧。

    Raises:
        ValueError: 嵌入密钥未配置。
    """
    from agentscope.rag import KnowledgeBase

    from engines.ae_harness.knowledge.models import create_embedding_model
    from engines.ae_harness.knowledge.store import SQLiteVectorStore

    created = create_embedding_model(embedding_spec)
    store = SQLiteVectorStore(index_dir / "rag.sqlite3")
    async with store:
        knowledge = KnowledgeBase(
            name=module_name,
            description=description,
            embedding_model=created.model,
            vector_store=store,
            collection=module_name,
        )
        documents = await knowledge.list_documents()
    mapping: dict[str, str] = {}
    for document in documents:
        mapping[document.source] = document.document_id
        relative = (document.metadata or {}).get("relative_path")
        if relative:
            mapping[str(relative)] = document.document_id
    return mapping
