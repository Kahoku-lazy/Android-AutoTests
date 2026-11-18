"""检索桥单测：多库合并、部分失败、三态、引擎缺失降级与用量入账。

用替身检索器承接引擎调用，不联网、不调真实嵌入 API。
"""

from __future__ import annotations

import pytest

from backend.apps.knowledge_search import api, retrieval
from backend.apps.usage_ledger.models import ModelUsage
from engines.ae_harness.knowledge.service import KnowledgeHit, Retrieval
from engines.ae_harness.knowledge.usage import UsageEvent

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


@pytest.fixture(autouse=True)
def _bases_file(tmp_path, settings):
    """派生 yaml 指到临时目录。"""
    settings.KNOWLEDGE_SEARCH_BASES_FILE = tmp_path / "bases.yaml"


@pytest.fixture()
def two_modules(tmp_path):
    """登记两个启用模块。"""
    dir_a = tmp_path / "a"
    dir_b = tmp_path / "b"
    dir_a.mkdir()
    dir_b.mkdir()
    api.create_module(name="kb_a", description="甲库", data_dir=str(dir_a))
    api.create_module(name="kb_b", description="乙库", data_dir=str(dir_b))
    return ["kb_a", "kb_b"]


def _hit(base: str, score: float, index: int = 0) -> KnowledgeHit:
    """造一条命中。"""
    return KnowledgeHit(
        base=base,
        source=f"{base}.md",
        text="原文",
        score=score,
        chunk_index=index,
        document_id=f"doc_{base}_{index}",
    )


class _FakeRetriever:
    """替身检索器：按库返回预置结果。"""

    canned: dict[str, Retrieval] = {}
    events: list[UsageEvent] = []
    index_count = 2
    index_error = ""

    def __init__(self, config):
        self.config = config

    async def retrieve(self, query, *, base=None, top_k=None):
        return self.canned.get(base, Retrieval("no_hit"))

    async def ensure_index(self, base):
        return self.index_count

    def error(self, base):
        return self.index_error

    def usage_events(self):
        events = self.events
        _FakeRetriever.events = []
        return events


@pytest.fixture()
def fake_retriever(monkeypatch):
    """把检索桥的引擎类换成替身。"""
    _FakeRetriever.canned = {}
    _FakeRetriever.events = []
    _FakeRetriever.index_count = 2
    _FakeRetriever.index_error = ""
    monkeypatch.setattr(retrieval, "KnowledgeRetriever", _FakeRetriever)
    return _FakeRetriever


def test_multi_base_merge_sort_truncate(two_modules, fake_retriever):
    """多库命中按相似度降序合并并截断。"""
    fake_retriever.canned = {
        "kb_a": Retrieval("ok", hits=(_hit("kb_a", 0.6), _hit("kb_a", 0.9, 1))),
        "kb_b": Retrieval("ok", hits=(_hit("kb_b", 0.8),)),
    }
    result = retrieval.search(question="问题", bases=two_modules)
    assert result["result"] == "ok"
    assert [hit["score"] for hit in result["hits"]] == [0.9, 0.8, 0.6]
    truncated = retrieval.search(question="问题", bases=two_modules, top_k=2)
    assert [hit["score"] for hit in truncated["hits"]] == [0.9, 0.8]


def test_partial_failure_returns_hits_and_errors(two_modules, fake_retriever):
    """单库失败不拖垮其它库：返回命中并附逐库错误。"""
    fake_retriever.canned = {
        "kb_a": Retrieval("ok", hits=(_hit("kb_a", 0.7),)),
        "kb_b": Retrieval("unavailable", error="索引失败"),
    }
    result = retrieval.search(question="问题", bases=two_modules)
    assert result["result"] == "ok"
    assert len(result["hits"]) == 1
    assert result["errors"] == ["kb_b: 索引失败"]


def test_all_unavailable_and_no_hit(two_modules, fake_retriever):
    """全部失败为 unavailable；库可用但没命中为 no_hit，文案不同。"""
    fake_retriever.canned = {
        "kb_a": Retrieval("unavailable", error="密钥缺失"),
        "kb_b": Retrieval("unavailable", error="索引失败"),
    }
    failed = retrieval.search(question="问题", bases=two_modules)
    assert failed["result"] == "unavailable"
    assert failed["hits"] == []
    assert len(failed["errors"]) == 2

    fake_retriever.canned = {"kb_a": Retrieval("no_hit"), "kb_b": Retrieval("no_hit")}
    empty = retrieval.search(question="问题", bases=two_modules)
    assert empty["result"] == "no_hit"
    assert empty["errors"] == []


def test_empty_inputs_rejected(two_modules, fake_retriever):
    """空白问题与空勾选直接降级，不触发检索。"""
    assert retrieval.search(question="  ", bases=two_modules)["result"] == "unavailable"
    assert retrieval.search(question="问题", bases=[])["result"] == "unavailable"


def test_engine_missing_degrades(two_modules, monkeypatch):
    """引擎整目录删除后降级为 unavailable，不抛异常。"""
    monkeypatch.setattr(retrieval, "KnowledgeRetriever", None)
    result = retrieval.search(question="问题", bases=two_modules)
    assert result["result"] == "unavailable"
    assert "引擎知识库模块缺失" in result["errors"][0]
    indexed = retrieval.index_module(name="kb_a")
    assert indexed["status"] is False


def test_config_load_failure_degrades(two_modules, fake_retriever, monkeypatch):
    """库目录装载失败降级为 unavailable。"""

    def broken_load(**kwargs):
        raise ValueError("目录冲突")

    monkeypatch.setattr(retrieval, "load_config", broken_load)
    result = retrieval.search(question="问题", bases=two_modules)
    assert result["result"] == "unavailable"


def test_usage_recorded_to_ledger(two_modules, fake_retriever):
    """检索结束把嵌入用量写入账本，source=knowledge。"""
    fake_retriever.canned = {"kb_a": Retrieval("ok", hits=(_hit("kb_a", 0.7),))}
    fake_retriever.events = [
        UsageEvent(
            model="text-embedding-v4",
            api_key_env="DASHSCOPE_API_KEY",
            tokens=10,
            time=0.1,
            phase="retrieve",
            base="kb_a",
        )
    ]
    retrieval.search(question="问题", bases=["kb_a"], execution_id="exec-x")
    row = ModelUsage.objects.get(execution_id="exec-x")
    assert row.source == "knowledge"
    assert row.category == "Embedding"
    assert row.input_tokens == 10


def test_ledger_failure_does_not_block(two_modules, fake_retriever, monkeypatch):
    """入账失败只记日志，检索结果照常返回。"""
    import backend.apps.usage_ledger.api as ledger_api

    def broken_record(*args, **kwargs):
        raise RuntimeError("账本不可写")

    monkeypatch.setattr(ledger_api, "record_embedding_usages", broken_record)
    fake_retriever.canned = {"kb_a": Retrieval("ok", hits=(_hit("kb_a", 0.7),))}
    fake_retriever.events = [
        UsageEvent(model="m", api_key_env="DASHSCOPE_API_KEY", tokens=1, time=0.1)
    ]
    result = retrieval.search(question="问题", bases=["kb_a"])
    assert result["result"] == "ok"


def test_index_module_success_and_failure(two_modules, fake_retriever):
    """预建索引返回重建数；失败给可读原因。"""
    ok = retrieval.index_module(name="kb_a", execution_id="idx-1")
    assert ok == {"status": True, "error": "", "reindexed": 2}
    fake_retriever.index_error = "资料目录不存在"
    bad = retrieval.index_module(name="kb_a")
    assert bad["status"] is False
    assert "资料目录不存在" in bad["error"]
