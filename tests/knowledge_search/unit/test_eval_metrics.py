"""评测指标手算对拍：Recall@k / MRR / 误命中率。"""

from __future__ import annotations

import pytest

from backend.apps.knowledge_search.eval_metrics import first_gold_rank, summarize

pytestmark = [pytest.mark.unit]


def test_first_gold_rank():
    """排名从 1 起；未命中与空 gold 为 None。"""
    hits = [{"document_id": "doc_a"}, {"document_id": "doc_b"}, {"document_id": "doc_c"}]
    assert first_gold_rank(hits, "doc_b") == 2
    assert first_gold_rank(hits, "doc_x") is None
    assert first_gold_rank(hits, "") is None
    assert first_gold_rank([], "doc_a") is None


def test_summarize_hand_computed():
    """手算样例：ranks [1,3,None,5]，负样本 4 条中 1 条误命中。"""
    queries = [
        {"kind": "positive", "rank": 1, "is_hit": True},
        {"kind": "positive", "rank": 3, "is_hit": True},
        {"kind": "positive", "rank": None, "is_hit": False},
        {"kind": "positive", "rank": 5, "is_hit": True},
        {"kind": "negative", "rank": None, "is_hit": True},
        {"kind": "negative", "rank": None, "is_hit": False},
        {"kind": "negative", "rank": None, "is_hit": False},
        {"kind": "negative", "rank": None, "is_hit": False},
    ]
    metrics = summarize(queries)
    assert metrics["n_pos"] == 4
    assert metrics["n_neg"] == 4
    assert metrics["recall_at_1"] == 0.25
    assert metrics["recall_at_3"] == 0.5
    assert metrics["recall_at_5"] == 0.75
    # MRR = (1 + 1/3 + 0 + 1/5) / 4
    assert metrics["mrr"] == round((1 + 1 / 3 + 0 + 1 / 5) / 4, 4)
    assert metrics["false_hit_rate"] == 0.25


def test_summarize_empty_is_zero():
    """空样本各指标记 0，不除零。"""
    metrics = summarize([])
    assert metrics["n_pos"] == 0
    assert metrics["recall_at_1"] == 0.0
    assert metrics["mrr"] == 0.0
    assert metrics["false_hit_rate"] == 0.0
