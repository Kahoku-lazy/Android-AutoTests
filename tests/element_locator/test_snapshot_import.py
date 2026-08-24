"""element_locator 快照导入单元测试（纯逻辑，fake ORM，无 DB）。"""

from types import SimpleNamespace

import pytest

from apps.element_locator import api_snapshot

pytestmark = [pytest.mark.unit, pytest.mark.element_locator]


class _FakePages:
    """fake Page.objects：内存行集合，支持 filter/first/get/create/count。"""

    def __init__(self):
        self.rows = []  # SimpleNamespace(id, label, parent_id, is_folder, ...)
        self.next_id = 1

    def _match(self, row, **kw):
        for k, v in kw.items():
            if k == "pk":
                k = "id"
            if getattr(row, k) != v:
                return False
        return True

    def filter(self, **kw):
        matched = [r for r in self.rows if self._match(r, **kw)]
        return _FakeResult(matched, parent=self)

    def get(self, **kw):
        for r in self.rows:
            if self._match(r, **kw):
                return r
        raise Exception("DoesNotExist")

    def create(self, **kw):
        kw.setdefault("element_count", 0)
        row = SimpleNamespace(id=self.next_id, **kw)
        row.save = lambda **save_kw: None
        self.next_id += 1
        self.rows.append(row)
        return row

    def count(self):
        return len(self.rows)


class _FakeResult:
    def __init__(self, rows, parent):
        self.rows = rows
        self._parent = parent

    def first(self):
        return self.rows[0] if self.rows else None

    def filter(self, **kw):
        matched = [r for r in self.rows if self._parent._match(r, **kw)]
        return _FakeResult(matched, parent=self._parent)

    def order_by(self, *args):
        return self

    def count(self):
        return len(self.rows)

    def __iter__(self):
        return iter(self.rows)

    def values_list(self, *args, **kw):
        return []


def _patch_pages(monkeypatch):
    fake = _FakePages()
    monkeypatch.setattr(api_snapshot, "Page", SimpleNamespace(objects=fake))
    # 深度校验走真实 page_tree 需访问 fake row 的 parent 链，此处恒 1（深度约束由 page_tree 自测覆盖）
    from apps.element_locator import page_tree as pt

    monkeypatch.setattr(pt, "page_depth", lambda page, parent_map=None: 1)
    return fake


def _patch_elements(monkeypatch, fake_pages):
    class _FakeElements:
        def __init__(self):
            self.created = []

        def filter(self, **kw):
            return _FakeResult([], parent=fake_pages)

        def create(self, **kw):
            self.created.append(kw)
            return SimpleNamespace(id=len(self.created), **kw)

        def count(self):
            return len(self.created)

    fake = _FakeElements()
    monkeypatch.setattr(api_snapshot, "Element", SimpleNamespace(objects=fake))
    return fake


def test_import_snapshot_creates_folder_page_and_elements(monkeypatch):
    pages = _patch_pages(monkeypatch)
    elements = _patch_elements(monkeypatch, pages)

    result = api_snapshot.import_snapshot_page(
        page_label="登录页",
        folder_path="AI/冒烟",
        package="com.demo",
        screenshot_path="inspector/shots/c.png",
        ocr_json={"ocr_count": 1, "texts": []},
        snapshot_id=9,
        elements=[
            {
                "class_name": "android.widget.Button",
                "text": "登录",
                "resource_id": "com.demo:id/login",
                "bounds": "[0,0][10,10]",
                "x": 0,
                "y": 0,
                "width": 10,
                "height": 10,
                "depth": 2,
                "index": "0",
                "clickable": True,
                "xpaths": [{"type": "resource-id", "xpath": "//x", "count": 1}],
                "thumbnail_path": "inspector/thumbs/x/el_0.png",
            }
        ],
    )

    folders = [r for r in pages.rows if r.is_folder]
    page = [r for r in pages.rows if not r.is_folder][0]
    assert [f.label for f in folders] == ["AI", "冒烟"]
    assert folders[1].parent_id == folders[0].id
    assert page.label == "登录页" and page.parent_id == folders[1].id
    assert page.snapshot_id == 9 and page.ocr_json == {"ocr_count": 1, "texts": []}
    assert result == {"saved": 1, "updated": 0, "skipped": 0, "page_id": page.id}

    el = elements.created[0]
    assert el["alias"] == "登录"
    assert el["x"] == 0 and el["depth"] == 2 and el["scrollable"] is False
    assert "xpath" in el["xpath_candidates"]


def test_import_snapshot_conflict_same_label(monkeypatch):
    pages = _patch_pages(monkeypatch)
    _patch_elements(monkeypatch, pages)
    pages.create(label="登录页", parent_id=None, is_folder=False)

    with pytest.raises(api_snapshot.ImportConflictError):
        api_snapshot.import_snapshot_page(page_label="登录页", elements=[{"bounds": "[0,0][1,1]"}])


def test_import_snapshot_requires_elements(monkeypatch):
    _patch_pages(monkeypatch)
    _patch_elements(monkeypatch, _FakePages())
    with pytest.raises(ValueError):
        api_snapshot.import_snapshot_page(page_label="空页", elements=[])


def test_get_page_full_returns_none_when_missing(monkeypatch):
    _patch_pages(monkeypatch)
    assert api_snapshot.get_page_full(999) is None


def test_get_page_full_parses_xpaths(monkeypatch):
    import json

    pages = _patch_pages(monkeypatch)
    page = pages.create(
        label="登录页",
        parent_id=None,
        is_folder=False,
        package="com.demo",
        activity="Main",
        screenshot_path="a.png",
        ocr_json={"ocr_count": 0},
        element_count=1,
    )

    class _ElQuery(_FakeResult):
        def order_by(self, *args):
            return self

    fake_els = SimpleNamespace(
        objects=SimpleNamespace(
            filter=lambda **kw: _ElQuery(
                [
                    SimpleNamespace(
                        id=1,
                        class_name="B",
                        text_val="登录",
                        content_desc="",
                        resource_id="com.demo:id/login",
                        bounds="[0,0][1,1]",
                        xpath_candidates=json.dumps([{"type": "t", "xpath": "//b", "count": 1}]),
                        x=0,
                        y=0,
                        width=1,
                        height=1,
                        depth=1,
                        index="0",
                        clickable=True,
                        enabled=True,
                        scrollable=False,
                        checked=False,
                        thumbnail_path="",
                        alias="登录",
                        is_test_point=False,
                    )
                ],
                parent=pages,
            )
        )
    )
    monkeypatch.setattr(api_snapshot, "Element", fake_els)

    full = api_snapshot.get_page_full(page.id)
    assert full["label"] == "登录页"
    assert full["elements"][0]["xpaths"] == [{"type": "t", "xpath": "//b", "count": 1}]
    assert full["ocr_json"] == {"ocr_count": 0}
