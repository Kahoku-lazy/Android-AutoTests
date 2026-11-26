from __future__ import annotations

import asyncio
import sys
import threading

from pathlib import Path

from asgiref.sync import sync_to_async

from utils.logs import backend_log

from . import api
from .eval_corpus import gold_document_map, sample_chunks
from .eval_generation import generate_negative_questions, generate_positive_questions
from .eval_metrics import first_gold_rank, summarize

try:
    from engines.ae_harness.agents.models import create_model
    from engines.ae_harness.knowledge.config import INDEX_DIR, build_config
    from engines.ae_harness.knowledge.service import KnowledgeRetriever
except ModuleNotFoundError as exc:  # pragma: no cover - 引擎缺失分支由单测替身覆盖
    if not (exc.name or "").startswith("engines.ae_harness"):
        raise
    create_model = None
    INDEX_DIR = None
    build_config = None
    KnowledgeRetriever = None

EVAL_TOP_K = 5
MIN_POSITIVES = 5


def engine_available() -> bool:
    return KnowledgeRetriever is not None and create_model is not None


def start_eval_run(pk: int) -> None:
    if "pytest" in sys.modules:
        return
    threading.Thread(target=_run, args=(pk,), daemon=True, name=f"ks-eval-{pk}").start()


def estimate_cost(pos_count: int, neg_count: int, chunk_size: int = 400) -> dict:
    total = pos_count + neg_count
    return {
        "chat_input_tokens": pos_count * chunk_size * 2 + neg_count * 200,
        "chat_output_tokens": total * 80,
        "embedding_tokens": total * 60,
        "note": "启发式预估，不含首次建索引；实际以账本为准",
    }


def _run(pk: int) -> None:
    from django.db import close_old_connections

    close_old_connections()
    run = api.get_eval_run(pk)
    if run is None or run.status != api.KsEvalRun.STATUS_PENDING:
        return
    api.mark_eval_running(pk)
    collector: dict = {"chat": [], "embedding": []}
    try:
        metrics = asyncio.run(_run_async(run, collector))
        _record_usages(collector, run)
        api.finish_eval_run(pk, status=api.KsEvalRun.STATUS_DONE, metrics=metrics)
    except Exception as exc:  # noqa: BLE001 - 运行失败只收口，不炸线程
        backend_log.exception("knowledge eval run failed pk=%s: %s", pk, exc)
        _record_usages(collector, run)
        api.finish_eval_run(pk, status=api.KsEvalRun.STATUS_FAILED, error=str(exc))
    finally:
        close_old_connections()


async def _run_async(run, collector: dict) -> dict:
    if not engine_available():
        raise RuntimeError("检索不可用：引擎知识库模块缺失")
    snapshot = run.module_snapshot
    name = snapshot["name"]
    config = _config_from_snapshot(run)
    retriever = KnowledgeRetriever(config)
    await sync_to_async(api.set_eval_phase)(run.pk, "indexing")
    await retriever.ensure_index(name)
    collector["embedding"].extend(event.as_dict() for event in retriever.usage_events())

    chunks = await sample_chunks(
        Path(snapshot["data_dir"]),
        chunk_size=config.chunk_size,
        chunk_overlap=config.chunk_overlap,
        count=run.pos_count,
        seed=run.seed,
    )
    gold_map = await gold_document_map(name, snapshot["description"], config.embedding, INDEX_DIR)
    chunks = [chunk for chunk in chunks if chunk["relative_path"] in gold_map]
    if not chunks:
        raise RuntimeError("没有已索引的资料可供出题，请先预建索引")

    model_snapshot = run.model_snapshot
    await sync_to_async(api.set_eval_phase)(run.pk, "generating")
    created = create_model(
        model_snapshot["provider"],
        model_snapshot["api_key_env"],
        model_snapshot["model_name"],
        model_snapshot.get("base_url", ""),
        stream=False,
    )
    positives, usages = await generate_positive_questions(
        created.model,
        chunks,
        api_key_env=created.api_key_env,
        model_name=model_snapshot["model_name"],
    )
    collector["chat"].extend(usages)
    if len(positives) < MIN_POSITIVES:
        raise RuntimeError(f"有效正题不足 {MIN_POSITIVES} 条（实际 {len(positives)}），评测终止")
    negatives, usages = await generate_negative_questions(
        created.model,
        snapshot["description"],
        sorted({chunk["source"] for chunk in chunks}),
        run.neg_count,
        api_key_env=created.api_key_env,
        model_name=model_snapshot["model_name"],
    )
    collector["chat"].extend(usages)

    queries: list[dict] = []
    total = len(positives) + len(negatives)
    done = 0
    await sync_to_async(api.set_eval_phase)(run.pk, "retrieving")
    await sync_to_async(api.set_eval_progress)(run.pk, done, total)

    for item in positives:
        chunk = item["chunk"]
        gold = gold_map[chunk["relative_path"]]
        hits = await _retrieve(retriever, name, item["question"], collector)
        rank = first_gold_rank(hits, gold)
        row = {
            "kind": "positive",
            "question": item["question"],
            "gold_document_id": gold,
            "gold_source": chunk["source"],
            "source_chunk_index": chunk["chunk_index"],
            "source_text": chunk["text"][:2000],
            "hits": hits,
            "rank": rank,
            "is_hit": rank is not None,
        }
        await sync_to_async(api.add_eval_query)(run.pk, **row)
        queries.append(row)
        done += 1
        await sync_to_async(api.set_eval_progress)(run.pk, done, total)

    for question in negatives:
        hits = await _retrieve(retriever, name, question, collector)
        row = {
            "kind": "negative",
            "question": question,
            "gold_document_id": "",
            "gold_source": "",
            "source_chunk_index": 0,
            "source_text": "",
            "hits": hits,
            "rank": None,
            "is_hit": bool(hits),
        }
        await sync_to_async(api.add_eval_query)(run.pk, **row)
        queries.append(row)
        done += 1
        await sync_to_async(api.set_eval_progress)(run.pk, done, total)

    return summarize(queries)


async def _retrieve(retriever, name: str, question: str, collector: dict) -> list[dict]:
    result = await retriever.retrieve(question, base=name, top_k=EVAL_TOP_K)
    collector["embedding"].extend(event.as_dict() for event in retriever.usage_events())
    if result.status == "unavailable":
        raise RuntimeError(f"检索不可用：{result.error}")
    return [hit.as_dict() for hit in result.hits]


def _config_from_snapshot(run):
    retrieval = (run.model_snapshot or {}).get("retrieval") or {}
    if not retrieval.get("model_name"):
        raise RuntimeError("检索不可用：评测触发时没有检索配置")
    snapshot = run.module_snapshot
    return build_config(
        {
            "provider": retrieval["provider"],
            "api_key": retrieval["api_key_env"],
            "model_name": retrieval["model_name"],
            "dimensions": retrieval["dimensions"],
        },
        [
            {
                "name": snapshot["name"],
                "description": snapshot["description"],
                "data_dir": snapshot["data_dir"],
                "enabled": True,
            }
        ],
        top_k=retrieval["top_k"],
        score_threshold=retrieval["score_threshold"],
        chunk_size=retrieval["chunk_size"],
        chunk_overlap=retrieval["chunk_overlap"],
        index_epoch=retrieval["index_epoch"],
    )


def _record_usages(collector: dict, run) -> None:
    try:
        from backend.apps.usage_ledger.api import record_embedding_usages, record_run_usages

        execution_id = str(run.run_id)
        if collector["chat"]:
            record_run_usages(
                collector["chat"],
                execution_id=execution_id,
                model=run.model_snapshot.get("model_name", ""),
                source="knowledge_eval",
            )
        if collector["embedding"]:
            record_embedding_usages(
                collector["embedding"],
                execution_id=execution_id,
                source="knowledge_eval",
            )
    except Exception:
        backend_log.exception("knowledge eval usage ledger write failed run=%s", run.run_id)
