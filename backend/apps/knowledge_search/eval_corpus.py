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
