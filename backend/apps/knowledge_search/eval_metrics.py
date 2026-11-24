from __future__ import annotations

_RECALL_KS = (1, 3, 5)


def first_gold_rank(hits: list[dict], gold_document_id: str) -> int | None:
    if not gold_document_id:
        return None
    for index, hit in enumerate(hits, 1):
        if hit.get("document_id") == gold_document_id:
            return index
    return None


def summarize(queries: list[dict]) -> dict:
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
