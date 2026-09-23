"""设备检查器历史快照的保留上限与一键清空 — 集成测试。

覆盖变更 add-snapshot-retention-and-clear：
  A) 保留上限：采集成功后自动淘汰最早的多余记录，列表最多返回上限条；
  B) 一键清空：只清调用者自己、返回删除条数、空列表返回 0；
  C) 两条路径都复用「删除不得破坏仍被引用的媒体」的判定。

真实写库（django_db）；设备用替身、媒体用临时目录隔离，不连设备。
"""

from datetime import timedelta

import pytest

from django.contrib.auth import get_user_model
from django.test import Client, override_settings
from django.utils import timezone

from apps.device_inspector import api as inspector_api
from apps.device_inspector import service
from apps.device_inspector.models import Snapshot
from apps.element_locator.models import Element, Page
from shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.integration, pytest.mark.device_inspector]

USER = "u1"
OTHER = "u2"
RETENTION = inspector_api.SNAPSHOT_RETENTION

TS = "20260101_000000_000000"
SHOT = "inspector/shots/capture_%s.png" % TS
THUMB = "inspector/thumbs/%s/el_0.png" % TS

FIXTURE_XML = (
    '<?xml version="1.0" encoding="UTF-8"?>\n'
    '<hierarchy rotation="0">\n'
    '  <node index="0" text="" resource-id="" class="android.widget.FrameLayout" package="com.demo"'
    ' checkable="false" checked="false" clickable="false" enabled="true" focusable="false"'
    ' focused="false" scrollable="false" long-clickable="false" password="false" selected="false"'
    ' visible-to-user="true" bounds="[0,0][1080,2340]" drawing-order="0" hint="" display-id="0">\n'
    '    <node index="0" text="设备" resource-id="com.demo:id/tvTitle" class="android.widget.TextView"'
    ' package="com.demo" content-desc="" checkable="false" checked="false" clickable="true" enabled="true"'
    ' focusable="false" focused="false" scrollable="false" long-clickable="false" password="false"'
    ' selected="false" visible-to-user="true" bounds="[58,59][156,217]" drawing-order="1" hint="" display-id="0"/>\n'
    "  </node>\n"
    "</hierarchy>\n"
)


class _FakeEngine:
    device_info = {"displayWidth": 1080, "displayHeight": 2340}

    def dump_hierarchy_xml(self):
        return FIXTURE_XML

    def app_current(self):
        return {"package": "com.demo", "activity": ".Main"}


def _write_file(media_root, rel, payload=b"png"):
    path = media_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _snapshot(user=USER, minutes_ago=0, shot="", thumb=""):
    """建一条快照；created_at 显式错开（auto_now_add 不能直接赋值，故落库后回写）。"""
    snapshot = Snapshot.objects.create(
        serial="S1",
        method="dump",
        dump_json={"actionable": [{"thumbnail_path": thumb}]} if thumb else {},
        screenshot_path=shot,
        package="com.demo",
        created_by=user,
    )
    if minutes_ago:
        Snapshot.objects.filter(id=snapshot.id).update(
            created_at=timezone.now() - timedelta(minutes=minutes_ago)
        )
    return snapshot


def _patch_capture(monkeypatch, tmp_path):
    import engines.device.registry as registry

    monkeypatch.setattr(service, "_shot_dir", lambda: tmp_path)
    monkeypatch.setattr(service, "open_inspector_engine", lambda serial: _FakeEngine())
    monkeypatch.setattr(
        service, "capture_page_screenshot", lambda engine, ts: "inspector/shots/capture_x.png"
    )
    monkeypatch.setattr(registry, "close_engine", lambda engine: None)


# ══════════════ A) 保留上限 ══════════════


@pytest.mark.django_db
def test_capture_prunes_to_retention(tmp_path, monkeypatch):
    """第十一条出现时自动淘汰创建时间最早的一条（采集成功后触发）。"""
    _patch_capture(monkeypatch, tmp_path)
    with override_settings(MEDIA_ROOT=tmp_path):
        existing = [_snapshot(minutes_ago=RETENTION + 1 - i) for i in range(RETENTION)]
        oldest_id = existing[0].id
        kept_ids = [s.id for s in existing[1:]]

        data = inspector_api.capture_snapshot(USER, "S1")

        ids = list(Snapshot.objects.filter(created_by=USER).values_list("id", flat=True))
        assert len(ids) == RETENTION
        assert oldest_id not in ids, "超出上限时必须淘汰创建时间最早的一条"
        assert all(i in ids for i in kept_ids), "其余快照必须保留"
        assert data["snapshot_id"] in ids, "本次采集的快照必须保留"


@pytest.mark.django_db
def test_prune_keeps_everything_within_retention(tmp_path):
    """未超过上限时不淘汰任何记录。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        for i in range(RETENTION):
            _snapshot(minutes_ago=i + 1)

        assert inspector_api.prune_snapshots(USER) == 0
        assert Snapshot.objects.filter(created_by=USER).count() == RETENTION


@pytest.mark.django_db
def test_prune_keeps_media_referenced_by_locator(tmp_path):
    """淘汰的媒体若仍被元素定位引用，文件必须保留。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        shot = _write_file(tmp_path, SHOT)
        thumb = _write_file(tmp_path, THUMB)
        oldest = _snapshot(minutes_ago=99, shot=SHOT, thumb=THUMB)
        for i in range(RETENTION):
            _snapshot(minutes_ago=i + 1)
        page = Page.objects.create(is_folder=False, label="被引用页面", screenshot_path=SHOT)
        Element.objects.create(
            page=page,
            resource_id="com.demo:id/x",
            bounds="[0,0][10,10]",
            thumbnail_path=THUMB,
        )

        assert inspector_api.prune_snapshots(USER) == 1

        assert not Snapshot.objects.filter(id=oldest.id).exists()
        assert shot.is_file(), "被引用的截图不得被删除"
        assert thumb.is_file(), "被引用的缩略图不得被删除"


@pytest.mark.django_db
def test_prune_only_touches_own_snapshots():
    """淘汰只作用于发起采集的调用者，他人快照不受影响。"""
    for i in range(RETENTION + 2):
        _snapshot(minutes_ago=i + 1)
    for i in range(RETENTION + 2):
        _snapshot(user=OTHER, minutes_ago=i + 1)

    assert inspector_api.prune_snapshots(USER) == 2
    assert Snapshot.objects.filter(created_by=USER).count() == RETENTION
    assert Snapshot.objects.filter(created_by=OTHER).count() == RETENTION + 2


@pytest.mark.django_db
def test_list_is_capped_at_retention_with_real_total():
    """列表最多返回保留上限条，但 total 仍是真实总数。"""
    for i in range(RETENTION + 5):
        _snapshot(minutes_ago=RETENTION + 5 - i)

    data = inspector_api.list_snapshots(USER, 0, 100)

    assert data["total"] == RETENTION + 5, "total 不得被封顶改写"
    assert len(data["items"]) == RETENTION, "列表最多返回保留上限条"


# ══════════════ B) 一键清空 ══════════════


@pytest.mark.django_db
def test_clear_removes_all_own_snapshots_and_returns_count(tmp_path):
    """清空本人全部快照并返回删除条数。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        for i in range(4):
            _snapshot(minutes_ago=i + 1)

        assert inspector_api.clear_snapshots(USER) == 4
        assert Snapshot.objects.filter(created_by=USER).count() == 0
        assert inspector_api.list_snapshots(USER)["total"] == 0


@pytest.mark.django_db
def test_clear_only_removes_own_snapshots(tmp_path):
    """清空不得影响其它调用者的快照。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        _snapshot(minutes_ago=1)
        _snapshot(user=OTHER, minutes_ago=1)

        assert inspector_api.clear_snapshots(USER) == 1
        assert Snapshot.objects.filter(created_by=OTHER).count() == 1


@pytest.mark.django_db
def test_clear_keeps_media_referenced_by_locator(tmp_path):
    """清空时被元素定位引用的媒体仍保留。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        shot = _write_file(tmp_path, SHOT)
        thumb = _write_file(tmp_path, THUMB)
        _snapshot(minutes_ago=1, shot=SHOT, thumb=THUMB)
        page = Page.objects.create(is_folder=False, label="被引用页面", screenshot_path=SHOT)
        Element.objects.create(
            page=page,
            resource_id="com.demo:id/x",
            bounds="[0,0][10,10]",
            thumbnail_path=THUMB,
        )

        assert inspector_api.clear_snapshots(USER) == 1

        assert Snapshot.objects.filter(created_by=USER).count() == 0
        assert shot.is_file(), "被引用的截图不得被删除"
        assert thumb.is_file(), "被引用的缩略图不得被删除"


@pytest.mark.django_db
def test_clear_without_snapshots_returns_zero():
    """没有快照时清空成功返回 0（幂等）。"""
    assert inspector_api.clear_snapshots(USER) == 0


# ══════════════ C) 淘汰失败不回滚采集 / HTTP 端点 ══════════════


@pytest.mark.django_db
def test_capture_survives_prune_failure(tmp_path, monkeypatch):
    """淘汰是附带的维护动作：失败只告警，采集仍然成功返回。"""
    _patch_capture(monkeypatch, tmp_path)

    def _boom(_user_id):
        raise RuntimeError("淘汰失败")

    monkeypatch.setattr(inspector_api, "prune_snapshots", _boom)

    with override_settings(MEDIA_ROOT=tmp_path):
        data = inspector_api.capture_snapshot(USER, "S1")

        assert Snapshot.objects.filter(id=data["snapshot_id"]).exists(), "采集结果必须已落库"


@pytest.mark.django_db
def test_clear_endpoint_envelope_ownership_and_auth(tmp_path):
    """清空端点：信封 + 只清本人 + 删除条数 + 未登录 401。"""
    with override_settings(MEDIA_ROOT=tmp_path):
        user = get_user_model().objects.create_user(username="clear-user", password="x")
        user_id = str(user.id)
        headers = {"HTTP_AUTHORIZATION": "Bearer " + create_access_token(user_id)}
        _snapshot(user=user_id, minutes_ago=1)
        _snapshot(user=user_id, minutes_ago=2)
        _snapshot(user="someone-else", minutes_ago=1)
        client = Client()

        body = client.delete("/api/inspector/snapshots/clear/", **headers).json()

        assert body["status"] is True
        assert body["data"]["deleted"] == 2
        assert Snapshot.objects.filter(created_by=user_id).count() == 0
        assert Snapshot.objects.filter(created_by="someone-else").count() == 1

        anonymous = Client().delete("/api/inspector/snapshots/clear/")
        assert anonymous.status_code == 401
