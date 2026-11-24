"""
模块功能：➡️ 评测指标纯函数：Recall@k / MRR / 误命中率，零依赖、可手算对拍 🏁
Python 调试：➡️ python -m backend.apps.knowledge_search.eval_metrics 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 knowledge_search 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from __future__ import annotations

_RECALL_KS = (1, 3, 5)


def first_gold_rank(hits: list[dict], gold_document_id: str) -> int | None:
    """
    正确答案文档在命中列表里的首个排名（1 起）。

    Args:
        hits: 命中字典列表（含 document_id），按相似度降序。
        gold_document_id: 正确答案文档编号。

    Returns:
        排名；未命中时 None。空 gold 一律 None。
    """
    if not gold_document_id:
        return None
    for index, hit in enumerate(hits, 1):
        if hit.get("document_id") == gold_document_id:
            return index
    return None


def summarize(queries: list[dict]) -> dict:
    """
    由逐题结果汇总指标。

    Args:
        queries: 题目字典列表，含 kind（positive/negative）、rank、is_hit。

    Returns:
        {n_pos, n_neg, recall_at_1/3/5, mrr, false_hit_rate}；
        分母为 0 的指标记 0.0。
    """
    positives = [query for query in queries if query.get("kind") == "positive"]
    negatives = [query for query in queries if query.get("kind") == "negative"]
    n_pos = len(positives)
    n_neg = len(negatives)

    recalls = {}
    for k in _RECALL_KS:
        hit_count = sum(
            1 for query in positives if query.get("rank") is not None and query["rank"] <= k
        )
        recalls[f"recall_at_{k}"] = round(hit_count / n_pos, 4) if n_pos else 0.0

    reciprocal = [1.0 / query["rank"] for query in positives if query.get("rank")]
    mrr = round(sum(reciprocal) / n_pos, 4) if n_pos else 0.0

    false_hits = sum(1 for query in negatives if query.get("is_hit"))
    false_hit_rate = round(false_hits / n_neg, 4) if n_neg else 0.0

    return {"n_pos": n_pos, "n_neg": n_neg, **recalls, "mrr": mrr, "false_hit_rate": false_hit_rate}
