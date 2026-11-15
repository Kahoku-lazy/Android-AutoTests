"""按库检索：隔离、禁用、无命中和失败重试。"""

from __future__ import annotations

from pathlib import Path

import pytest

from engines.agents.rag.catalog import KnowledgeBaseSpec
from engines.agents.rag.config import RagConfig
from engines.agents.rag.service import KnowledgeBaseService

pytestmark = [pytest.mark.unit]


def _config(tmp_path: Path) -> RagConfig:
    return RagConfig(
        enabled=True,
        index_dir=tmp_path / "index",
        api_key="sk-test",
        score_threshold=0.55,
        max_context_chars=20,
    )


def _service(tmp_path: Path) -> KnowledgeBaseService:
    manuals = tmp_path / "manuals"
    keywords = tmp_path / "keywords"
    manuals.mkdir()
    keywords.mkdir()
    (manuals / "reset.md").write_text("# 恢复\n\n长按 3 秒。\n", encoding="utf-8")
    (keywords / "power.md").write_text("# 电源\n\n关键词 POWER_ON。\n", encoding="utf-8")
    return KnowledgeBaseService(
        _config(tmp_path),
        (
            KnowledgeBaseSpec("product_manuals", "产品资料", manuals, True),
            KnowledgeBaseSpec("log_keywords", "日志关键词", keywords, False),
        ),
    )


@pytest.mark.asyncio
async def test_retrieve_only_returns_named_base(tmp_path, monkeypatch):
    service = _service(tmp_path)
    seen: list[str] = []

    class _Result:
        def __init__(self, collection: str) -> None:
            self.score = 0.9
            self.document_id = "doc"
            self.chunk = type(
                "Chunk",
                (),
                {
                    "source": f"{collection}.md",
                    "chunk_index": 1,
                    "content": type("Content", (), {"text": collection})(),
                },
            )()

    class _Knowledge:
        def __init__(self, spec, store) -> None:
            self.collection = spec.name

        async def search(self, queries, top_k, score_threshold):
            seen.append(self.collection)
            return [_Result(self.collection)]

    async def _indexed(self):
        return 0

    monkeypatch.setattr("engines.agents.rag.service.RagIndexer.ensure_index", _indexed)
    monkeypatch.setattr("engines.agents.rag.service.KnowledgeBaseService._knowledge", _Knowledge)

    hits = await service.retrieve("product_manuals", "恢复")

    assert seen == ["product_manuals"]
    assert [hit.base for hit in hits] == ["product_manuals"]
    assert hits[0].text == "product_manuals"


@pytest.mark.asyncio
async def test_retrieve_disabled_base_returns_reason(tmp_path):
    service = _service(tmp_path)

    assert await service.retrieve("log_keywords", "电源") == []
    assert "已禁用" in service.error("log_keywords")


@pytest.mark.asyncio
async def test_retrieve_unknown_base_returns_reason(tmp_path):
    service = _service(tmp_path)

    assert await service.retrieve("missing", "恢复") == []
    assert "不存在" in service.error("missing")


@pytest.mark.asyncio
async def test_retrieve_does_not_cache_failure(tmp_path, monkeypatch):
    service = _service(tmp_path)

    def _boom(*args, **kwargs):
        raise RuntimeError("嵌入失败")

    monkeypatch.setattr("engines.agents.rag.service.create_model", _boom)
    assert await service.ensure_index("product_manuals") == 0
    assert "嵌入失败" in service.error("product_manuals")

    async def _indexed(self):
        return 1

    monkeypatch.setattr("engines.agents.rag.service.create_model", lambda *args, **kwargs: object())
    monkeypatch.setattr("engines.agents.rag.service.RagIndexer.ensure_index", _indexed)

    assert await service.ensure_index("product_manuals") == 1
    assert service.error("product_manuals") == ""
