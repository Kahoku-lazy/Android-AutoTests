"""评测运行器集成场景：替身承接引擎与模型，验证生命周期、进度、入账与失败收口。"""

from __future__ import annotations

from types import SimpleNamespace

import pytest

from backend.apps.knowledge_search import api, eval_runner
from backend.apps.usage_ledger.models import ModelUsage
from engines.ae_harness.knowledge.service import KnowledgeHit, Retrieval
from engines.ae_harness.knowledge.usage import UsageEvent

pytestmark = [pytest.mark.integration, pytest.mark.django_db(transaction=True)]


_RETRIEVAL = {
    "provider": "dashscope",
    "api_key_env": "DASHSCOPE_API_KEY",
    "model_name": "text-embedding-v4",
    "dimensions": 1024,
    "top_k": 4,
    "score_threshold": 0.45,
    "chunk_size": 400,
    "chunk_overlap": 60,
    "index_epoch": 0,
}


@pytest.fixture(autouse=True)
def _dirs(tmp_path, settings):
    settings.LOG_DIR = tmp_path / "logs"


@pytest.fixture()
def run_row(tmp_path):
    """登记模块并创建一次 pending 运行（快照冻结）。"""
    data_dir = tmp_path / "docs"
    data_dir.mkdir()
    module = api.create_module(name="kb_eval", description="评测库", data_dir=str(data_dir))
    return api.create_eval_run(
        module_name=module.name,
        module_snapshot={
            "name": module.name,
            "description": module.description,
            "data_dir": module.data_dir,
            "enabled": True,
        },
        model_config_id=1,
        model_snapshot={
            "provider": "dashscope",
            "api_key_env": "DASHSCOPE_API_KEY",
            "model_name": "qwen-flash",
            "base_url": "",
        },
        retrieval_snapshot=_RETRIEVAL,
        pos_count=5,
        neg_count=2,
        seed=42,
        cost_estimate={},
    )


def _chunks(count=6):
    return [
        {
            "source": f"f{i}.md",
            "relative_path": f"f{i}.md",
            "chunk_index": 0,
            "text": f"资料片段 {i}",
        }
        for i in range(count)
    ]


class _FakeRetriever:
    """替身检索器：正题命中 gold，负样本不命中。"""

    def __init__(self, config):
        self.config = config
        self._usage_left = [
            UsageEvent(
                model="text-embedding-v4",
                api_key_env="DASHSCOPE_API_KEY",
                tokens=8,
                time=0.1,
                phase="retrieve",
                base="kb_eval",
            )
        ]

    async def ensure_index(self, base):
        return 1

    async def retrieve(self, query, *, base=None, top_k=None):
        if query.startswith("负样本"):
            return Retrieval("no_hit")
        return Retrieval(
            "ok",
            hits=(
                KnowledgeHit(
                    base=base,
                    source="f0.md",
                    text="原文",
                    score=0.8,
                    chunk_index=0,
                    document_id="doc_f0",
                ),
            ),
        )

    def usage_events(self):
        events = self._usage_left
        self._usage_left = []
        return events


@pytest.fixture()
def patched_engine(monkeypatch):
    """替身：配置 / 检索器 / 模型 / 采样 / gold 映射 / 出题。"""
    config = SimpleNamespace(
        chunk_size=400,
        chunk_overlap=60,
        top_k=4,
        score_threshold=0.45,
        index_epoch=0,
        embedding=object(),
    )
    monkeypatch.setattr(eval_runner, "build_config", lambda *args, **kwargs: config)
    monkeypatch.setattr(eval_runner, "KnowledgeRetriever", _FakeRetriever)
    monkeypatch.setattr(
        eval_runner,
        "create_model",
        lambda *args, **kwargs: SimpleNamespace(model=object(), api_key_env="DASHSCOPE_API_KEY"),
    )

    async def fake_sample(data_dir, **kwargs):
        return _chunks()

    async def fake_gold_map(name, description, embedding_spec, index_dir):
        return {f"f{i}.md": f"doc_f{i}" for i in range(6)}

    async def fake_positives(model, chunks, **kwargs):
        questions = [{"question": f"问题 {i}", "chunk": chunks[i]} for i in range(5)]
        usage = {
            "round": "chat-1",
            "api_key_env": "DASHSCOPE_API_KEY",
            "model_name": "qwen-flash",
            "input_tokens": 100,
            "output_tokens": 50,
        }
        return questions, [usage]

    async def fake_negatives(model, description, sources, count, **kwargs):
        return [f"负样本 {i}" for i in range(count)], []

    monkeypatch.setattr(eval_runner, "sample_chunks", fake_sample)
    monkeypatch.setattr(eval_runner, "gold_document_map", fake_gold_map)
    monkeypatch.setattr(eval_runner, "generate_positive_questions", fake_positives)
    monkeypatch.setattr(eval_runner, "generate_negative_questions", fake_negatives)


def test_run_completes_with_metrics_and_ledger(run_row, patched_engine):
    """运行收口 done：指标、逐题明细、两类用量入账齐全。"""
    eval_runner._run(run_row.pk)
    run = api.get_eval_run(run_row.pk)
    assert run.status == "done"
    assert run.phase == "retrieving"
    assert run.progress_done == 7
    assert run.metrics["n_pos"] == 5
    assert run.metrics["n_neg"] == 2
    # 正题 gold 均为 doc_f0..f4，命中只有 doc_f0 → 仅第一题命中
    assert run.metrics["recall_at_1"] == 0.2
    assert run.metrics["false_hit_rate"] == 0.0
    assert run.queries.count() == 7
    rows = ModelUsage.objects.filter(source="knowledge_eval", execution_id=str(run.run_id))
    categories = sorted(row.category for row in rows)
    assert categories == ["Embedding", "LLM"]


def test_run_fails_when_positives_insufficient(run_row, patched_engine, monkeypatch):
    """有效正题不足 5 条：运行失败并给可读原因。"""

    async def few_positives(model, chunks, **kwargs):
        return [{"question": "唯一问题", "chunk": chunks[0]}], []

    monkeypatch.setattr(eval_runner, "generate_positive_questions", few_positives)
    eval_runner._run(run_row.pk)
    run = api.get_eval_run(run_row.pk)
    assert run.status == "failed"
    assert "有效正题不足" in run.error


def test_run_fails_when_engine_missing(run_row, monkeypatch):
    """引擎缺失：运行失败降级，不抛异常。"""
    monkeypatch.setattr(eval_runner, "KnowledgeRetriever", None)
    eval_runner._run(run_row.pk)
    run = api.get_eval_run(run_row.pk)
    assert run.status == "failed"
    assert "引擎知识库模块缺失" in run.error


def test_snapshot_isolates_module_change(run_row, patched_engine, tmp_path):
    """运行期间改模块路径：运行仍按触发时快照执行。"""
    new_dir = tmp_path / "new_docs"
    new_dir.mkdir()
    module = api.list_modules()[0]
    api.update_module(module.pk, data_dir=str(new_dir))
    eval_runner._run(run_row.pk)
    run = api.get_eval_run(run_row.pk)
    assert run.status == "done"
    assert run.module_snapshot["data_dir"] != str(new_dir.resolve())
