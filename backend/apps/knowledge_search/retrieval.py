from __future__ import annotations

import asyncio
import threading
import uuid

from pathlib import Path

from utils.logs import backend_log

try:
    from engines.ae_harness.knowledge.config import INDEX_DIR, build_config
    from engines.ae_harness.knowledge.service import KnowledgeRetriever
except ModuleNotFoundError as exc:  # pragma: no cover - 引擎缺失分支由单测替身覆盖
    if not (exc.name or "").startswith("engines.ae_harness.knowledge"):
        raise
    INDEX_DIR = None
    build_config = None
    KnowledgeRetriever = None

_BASE_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def engine_available() -> bool:
    return KnowledgeRetriever is not None


def search(
    *,
    question: str,
    bases: list[str],
    top_k: int | None = None,
    execution_id: str = "",
) -> dict:
    text = str(question or "").strip()
    if not text:
        return {"result": "unavailable", "hits": [], "errors": ["检索问题不能为空"]}
    names = [str(name).strip() for name in bases or [] if str(name).strip()]
    if not names:
        return {"result": "unavailable", "hits": [], "errors": ["未勾选知识库模块"]}
    if not engine_available():
        return {"result": "unavailable", "hits": [], "errors": ["检索不可用：引擎知识库模块缺失"]}
    execution_id = execution_id or uuid.uuid4().hex
    config = _platform_config()
    if isinstance(config, str):
        return {"result": "unavailable", "hits": [], "errors": [config]}
    outcome = asyncio.run(_search_async(text, names, top_k, config))
    _record_usage(outcome.pop("events"), execution_id)
    return outcome


def index_module(*, name: str, execution_id: str = "") -> dict:
    if not engine_available():
        return {"status": False, "error": "检索不可用：引擎知识库模块缺失", "reindexed": 0}
    execution_id = execution_id or uuid.uuid4().hex
    config = _platform_config()
    if isinstance(config, str):
        return {"status": False, "error": config, "reindexed": 0}
    outcome = asyncio.run(_index_async(str(name).strip(), config))
    _record_usage(outcome.pop("events"), execution_id)
    return outcome


def _base_lock(base: str) -> threading.Lock:
    with _LOCKS_GUARD:
        return _BASE_LOCKS.setdefault(base, threading.Lock())


def _platform_config():
    from .api import get_retrieval_settings, list_modules

    settings_row = get_retrieval_settings()
    if settings_row is None:
        return "检索不可用：尚未配置检索参数"
    from backend.apps.ai_assistant.models import AIModelConfig

    model = AIModelConfig.objects.filter(pk=settings_row.embedding_model_id).first()
    if model is None or model.model_kind != "embedding":
        return "检索不可用：向量模型配置缺失"
    try:
        config = build_config(
            {
                "provider": model.provider,
                "api_key": model.api_key_env,
                "model_name": model.model_name,
                "dimensions": model.dimensions,
            },
            [
                {
                    "name": module.name,
                    "description": module.description,
                    "data_dir": module.data_dir,
                    "enabled": module.enabled,
                }
                for module in list_modules()
            ],
            top_k=settings_row.top_k,
            score_threshold=settings_row.score_threshold,
            chunk_size=settings_row.chunk_size,
            chunk_overlap=settings_row.chunk_overlap,
            index_epoch=settings_row.index_epoch,
        )
    except (ValueError, TypeError) as exc:
        backend_log.exception("knowledge config build failed: %s", exc)
        return f"检索不可用：{exc}"
    return config


def _epoch_path(base: str) -> Path:
    return Path(INDEX_DIR) / f"{base}.epoch"


def _epoch_matches(base: str, epoch: int) -> bool:
    try:
        recorded = _epoch_path(base).read_text(encoding="utf-8").strip()
    except OSError:
        return False
    return recorded == str(epoch)


def mark_indexed(base: str, epoch: int) -> None:
    target = _epoch_path(base)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(str(epoch), encoding="utf-8")


async def _search_async(question: str, names: list[str], top_k: int | None, config) -> dict:
    epoch = config.index_epoch
    stale = [name for name in names if not _epoch_matches(name, epoch)]
    if stale:
        return {
            "result": "unavailable",
            "hits": [],
            "errors": [f"{name}: 切块参数已变更，需重建索引" for name in stale],
            "events": [],
        }
    retriever = KnowledgeRetriever(config)
    hits: list[dict] = []
    errors: list[str] = []
    for name in names:
        with _base_lock(name):
            result = await retriever.retrieve(question, base=name, top_k=top_k)
        if result.status == "unavailable":
            errors.append(f"{name}: {result.error}")
            continue
        hits.extend(hit.as_dict() for hit in result.hits)
    events = [event.as_dict() for event in retriever.usage_events()]
    hits.sort(key=lambda hit: hit["score"], reverse=True)
    limit = top_k if isinstance(top_k, int) and top_k > 0 else config.top_k
    hits = hits[:limit]
    if hits:
        return {"result": "ok", "hits": hits, "errors": errors, "events": events}
    if errors:
        return {"result": "unavailable", "hits": [], "errors": errors, "events": events}
    return {"result": "no_hit", "hits": [], "errors": [], "events": events}


async def _index_async(name: str, config) -> dict:
    retriever = KnowledgeRetriever(config)
    with _base_lock(name):
        count = await retriever.ensure_index(name)
    error = retriever.error(name)
    events = [event.as_dict() for event in retriever.usage_events()]
    if error:
        return {"status": False, "error": error, "reindexed": 0, "events": events}
    mark_indexed(name, config.index_epoch)
    return {"status": True, "error": "", "reindexed": count, "events": events}


def _record_usage(events: list[dict], execution_id: str) -> None:
    if not events:
        return
    try:
        from backend.apps.usage_ledger.api import record_embedding_usages

        record_embedding_usages(events, execution_id=execution_id)
    except Exception:
        backend_log.exception("knowledge usage ledger write failed execution=%s", execution_id)
