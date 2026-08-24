"""workflow AI 数据出口（api_digest）单元测试 — 伪 Manager，零 DB。

覆盖 get_document_digest 的 ok/错误路径（不存在/类型/解析失败/非对象）
与 list_document_summaries 的计数、目录名、损坏配置（None 而非 0）。
"""

import pytest

from apps.workflow import api_digest
from apps.workflow.models import WorkflowDocument

pytestmark = [pytest.mark.unit, pytest.mark.workflow]


# ── 伪 ORM 设施 ──


class _FakeQS(list):
    def __init__(self, items, log):
        super().__init__(items)
        self._log = log

    def filter(self, *args, **kwargs):
        self._log.append(("filter", args, kwargs))
        return self

    def select_related(self, *args):
        return self

    def order_by(self, *fields):
        self._log.append(("order_by", fields))
        return self

    def __getitem__(self, key):
        result = list.__getitem__(self, key)
        if isinstance(key, slice):
            return _FakeQS(result, self._log)
        return result


class _FakeManager:
    def __init__(self, items, log):
        self._items = list(items)
        self._log = log

    def filter(self, *args, **kwargs):
        return _FakeQS(self._items, self._log).filter(*args, **kwargs)

    def select_related(self, *args):
        return _FakeQS(self._items, self._log)

    def order_by(self, *fields):
        return _FakeQS(self._items, self._log)

    def get(self, **kwargs):
        doc_id = kwargs.get("doc_id")
        for it in self._items:
            if it.doc_id == doc_id:
                return it
        raise WorkflowDocument.DoesNotExist


class _Dir:
    def __init__(self, id, name):
        self.id = id
        self.name = name


class _Doc:
    def __init__(
        self,
        doc_id,
        title="",
        config_json="{}",
        doc_type="page_flow",
        directory=None,
        updated_at=None,
    ):
        self.doc_id = doc_id
        self.title = title
        self.config_json = config_json
        self.doc_type = doc_type
        self.directory = directory
        self.directory_id = directory.id if directory else None
        self.updated_at = updated_at


def _patch_docs(monkeypatch, docs):
    log = []
    monkeypatch.setattr(WorkflowDocument, "objects", _FakeManager(docs, log))
    return log


# ── get_document_digest ──


def test_get_document_digest_ok(monkeypatch):
    doc = _Doc(
        "WF-PF-1",
        title="流程A",
        config_json='{"nodes": [{"id": "n1", "type": "PageNode", "widgets_values": ["首页"]}], "links": []}',
    )
    _patch_docs(monkeypatch, [doc])
    ok, digest = api_digest.get_document_digest("WF-PF-1")
    assert ok is True
    assert digest["doc_id"] == "WF-PF-1"
    assert digest["title"] == "流程A"
    assert digest["node_count"] == 1


def test_get_document_digest_missing(monkeypatch):
    _patch_docs(monkeypatch, [])
    ok, msg = api_digest.get_document_digest("WF-PF-X")
    assert ok is False
    assert "文档不存在" in msg


def test_get_document_digest_rejects_test_case(monkeypatch):
    _patch_docs(monkeypatch, [_Doc("TC-1", doc_type="test_case")])
    ok, msg = api_digest.get_document_digest("TC-1")
    assert ok is False
    assert "不支持" in msg


def test_get_document_digest_bad_json(monkeypatch):
    _patch_docs(monkeypatch, [_Doc("WF-PF-1", config_json="{oops")])
    ok, msg = api_digest.get_document_digest("WF-PF-1")
    assert ok is False
    assert "解析失败" in msg


def test_get_document_digest_non_dict(monkeypatch):
    _patch_docs(monkeypatch, [_Doc("WF-PF-1", config_json="[1, 2]")])
    ok, msg = api_digest.get_document_digest("WF-PF-1")
    assert ok is False
    assert "JSON 对象" in msg


# ── list_document_summaries ──


def test_list_document_summaries_counts_and_dir(monkeypatch):
    d1 = _Doc(
        "WF-PF-1",
        title="流程A",
        config_json='{"nodes": [1, 2, 3], "links": [1]}',
        directory=_Dir(5, "默认目录"),
    )
    d2 = _Doc("WF-PF-2", title="流程B", config_json="{}")
    _patch_docs(monkeypatch, [d1, d2])
    rows = api_digest.list_document_summaries()
    assert len(rows) == 2
    assert rows[0]["doc_id"] == "WF-PF-1"
    assert rows[0]["node_count"] == 3
    assert rows[0]["link_count"] == 1
    assert rows[0]["directory_name"] == "默认目录"
    assert rows[1]["directory_name"] == ""
    assert rows[1]["node_count"] == 0


def test_list_document_summaries_corrupt_config_counts_none(monkeypatch):
    """损坏配置 → node/link_count 为 None（未知），不伪装成 0。"""
    _patch_docs(monkeypatch, [_Doc("WF-PF-1", config_json="{broken")])
    row = api_digest.list_document_summaries()[0]
    assert row["node_count"] is None
    assert row["link_count"] is None


def test_list_document_summaries_query_and_dir_filter(monkeypatch):
    log = _patch_docs(monkeypatch, [_Doc("WF-PF-1")])
    api_digest.list_document_summaries(query="登录", directory_id=3, limit=5)
    calls = [c for c in log if c[0] == "filter"]
    assert len(calls) == 3  # doc_type / directory_id / query
    assert calls[1][2] == {"directory_id": 3}
    assert any(c[0] == "order_by" and c[1] == ("-updated_at",) for c in log)


def test_list_document_summaries_empty_query_skips_query_filter(monkeypatch):
    log = _patch_docs(monkeypatch, [_Doc("WF-PF-1")])
    api_digest.list_document_summaries()
    calls = [c for c in log if c[0] == "filter"]
    assert len(calls) == 1  # 仅 doc_type
