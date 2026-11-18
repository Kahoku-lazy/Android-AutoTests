"""知识库只读检索桥：局部可选导入引擎、多库合并、预建索引与用量入账。

引擎 knowledge 整目录删除后降级为「检索不可用」，不抛 500。
本模块不造 Agent、不生成答案；命中原文逐字返回。
ORM 读写（派生 yaml、入账）只在同步入口做；异步段只做检索，避免
Django 的 SynchronousOnlyOperation。
"""

from __future__ import annotations

import asyncio
import threading
import uuid

from pathlib import Path

from utils.logs import backend_log

from . import registry

# 局部可选导入：只吞知识库模块自身的缺失，内部写错仍要抛。
try:
    from engines.ae_harness.knowledge.config import load_config
    from engines.ae_harness.knowledge.service import KnowledgeRetriever
except ModuleNotFoundError as exc:  # pragma: no cover - 引擎缺失分支由单测替身覆盖
    if not (exc.name or "").startswith("engines.ae_harness.knowledge"):
        raise
    load_config = None
    KnowledgeRetriever = None

# 进程级 per-base 锁：检索器锁是实例级，挡不住跨请求并发首问重复建索引。
_BASE_LOCKS: dict[str, threading.Lock] = {}
_LOCKS_GUARD = threading.Lock()


def engine_available() -> bool:
    """
    引擎知识库是否可导入。

    Returns:
        可用为真；整目录删除后为假。
    """
    return KnowledgeRetriever is not None


def search(
    *,
    question: str,
    bases: list[str],
    top_k: int | None = None,
    execution_id: str = "",
) -> dict:
    """
    多选模块检索：逐库检索、按相似度合并排序、用量入账。

    Args:
        question: 检索问题。
        bases: 勾选的库名列表。
        top_k: 返回条数上限；None 用配置默认。
        execution_id: 入账执行 ID；空时生成。

    Returns:
        {result: ok/no_hit/unavailable, hits: 命中字典列表, errors: 逐库错误}。
    """
    text = str(question or "").strip()
    if not text:
        return {"result": "unavailable", "hits": [], "errors": ["检索问题不能为空"]}
    names = [str(name).strip() for name in bases or [] if str(name).strip()]
    if not names:
        return {"result": "unavailable", "hits": [], "errors": ["未勾选知识库模块"]}
    if not engine_available():
        return {"result": "unavailable", "hits": [], "errors": ["检索不可用：引擎知识库模块缺失"]}
    execution_id = execution_id or uuid.uuid4().hex
    bases_path = _sync_bases()
    if bases_path is None:
        return {"result": "unavailable", "hits": [], "errors": ["检索不可用：库目录派生失败"]}
    outcome = asyncio.run(_search_async(text, names, top_k, bases_path))
    _record_usage(outcome.pop("events"), execution_id)
    return outcome


def index_module(*, name: str, execution_id: str = "") -> dict:
    """
    预建索引：同步重建单库增量索引。

    Args:
        name: 库名。
        execution_id: 入账执行 ID；空时生成。

    Returns:
        {status: 成败, error: 可读原因, reindexed: 本次重建文件数}。
    """
    if not engine_available():
        return {"status": False, "error": "检索不可用：引擎知识库模块缺失", "reindexed": 0}
    execution_id = execution_id or uuid.uuid4().hex
    bases_path = _sync_bases()
    if bases_path is None:
        return {"status": False, "error": "检索不可用：库目录派生失败", "reindexed": 0}
    outcome = asyncio.run(_index_async(str(name).strip(), bases_path))
    _record_usage(outcome.pop("events"), execution_id)
    return outcome


def _base_lock(base: str) -> threading.Lock:
    """取一个库的进程级锁；不存在时创建。"""
    with _LOCKS_GUARD:
        return _BASE_LOCKS.setdefault(base, threading.Lock())


def _sync_bases() -> Path | None:
    """
    在同步上下文里由 DB 重生成平台库目录 yaml。

    Returns:
        yaml 路径；派生失败时 None。
    """
    try:
        return registry.sync_yaml()
    except Exception as exc:  # noqa: BLE001 - 派生失败只降级
        backend_log.exception("knowledge bases sync failed: %s", exc)
        return None


def _load_config(bases_path: Path):
    """
    把平台库目录交给引擎校验装载。

    Args:
        bases_path: 平台库目录 yaml 路径。

    Returns:
        引擎知识库配置；装载失败时 None。
    """
    try:
        return load_config(bases_path=bases_path)
    except Exception as exc:  # noqa: BLE001 - 配置非法只降级，不打断调用方
        backend_log.exception("knowledge bases load failed: %s", exc)
        return None


async def _search_async(
    question: str, names: list[str], top_k: int | None, bases_path: Path
) -> dict:
    """逐库检索并合并；单库失败只记错误，不拖垮其它库。"""
    config = _load_config(bases_path)
    if config is None:
        return {
            "result": "unavailable",
            "hits": [],
            "errors": ["检索不可用：库目录装载失败"],
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


async def _index_async(name: str, bases_path: Path) -> dict:
    """重建单库索引；失败给可读原因。"""
    config = _load_config(bases_path)
    if config is None:
        return {
            "status": False,
            "error": "检索不可用：库目录装载失败",
            "reindexed": 0,
            "events": [],
        }
    retriever = KnowledgeRetriever(config)
    with _base_lock(name):
        count = await retriever.ensure_index(name)
    error = retriever.error(name)
    events = [event.as_dict() for event in retriever.usage_events()]
    if error:
        return {"status": False, "error": error, "reindexed": 0, "events": events}
    return {"status": True, "error": "", "reindexed": count, "events": events}


def _record_usage(events: list[dict], execution_id: str) -> None:
    """在同步上下文里经账本 api 入账；失败只记日志，不阻断检索。"""
    if not events:
        return
    try:
        from backend.apps.usage_ledger.api import record_embedding_usages

        record_embedding_usages(events, execution_id=execution_id)
    except Exception:
        backend_log.exception("knowledge usage ledger write failed execution=%s", execution_id)
