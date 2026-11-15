"""任务截图字节端点：登录、归属、缓存头、WebP 字节与 404。"""

from __future__ import annotations

import base64
import hashlib
import io

from io import StringIO
from pathlib import Path

import pytest

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import Client
from PIL import Image

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list import api, media_storage
from backend.apps.task_list.models import Task, TaskMedia
from backend.shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


@pytest.fixture(autouse=True)
def _temp_media_dir(settings, tmp_path):
    """截图落盘改到临时目录，避免测试写进真实 DATA_DIR。"""
    settings.TASK_MEDIA_DIR = tmp_path / "task_media"
    media_storage.reset_media_storage()
    yield
    media_storage.reset_media_storage()


def _jpeg_bytes() -> bytes:
    """造一张最小 JPEG。"""
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), (10, 20, 30)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _fixture(username: str = "media-owner"):
    """建一位拥有任务与一张截图的用户。"""
    owner = get_user_model().objects.create_user(username=username, password="pass")
    agent = AIAgent.objects.create(name=f"{username}-助手", owner=owner)
    task = Task.objects.create(agent=agent, title="媒体任务", status="completed")
    raw = _jpeg_bytes()
    packed = media_storage.encode(base64.b64encode(raw).decode("ascii"))
    assert packed is not None
    media_id = api.store_task_media(
        task.id,
        packed,
        {"event_seq": 1, "role_name": "executor_role", "step_seq": 1, "attempt": 1},
    )
    media = TaskMedia.objects.get(id=media_id)
    return owner, task, media, raw


def _client(user_id) -> Client:
    """带 JWT 的测试客户端。"""
    return Client(HTTP_AUTHORIZATION=f"Bearer {create_access_token(str(user_id))}")


def _url(task_id: int, media_id: int) -> str:
    return f"/api/tasks/{task_id}/media/{media_id}/"


def test_owner_gets_webp_bytes_with_cache_headers():
    owner, task, media, raw = _fixture()
    response = _client(owner.id).get(_url(task.id, media.id))

    assert response.status_code == 200
    assert response["Content-Type"] == "image/webp"
    assert Image.open(io.BytesIO(response.content)).format == "WEBP"
    assert response["ETag"] == f'"{media.sha256}"'
    assert media.sha256 == hashlib.sha256(raw).hexdigest()
    assert "immutable" in response["Cache-Control"]
    assert Path(django_settings.TASK_MEDIA_DIR, media.storage_key).is_file()


def test_matching_etag_returns_not_modified():
    owner, task, media, _ = _fixture("media-owner-etag")
    client = _client(owner.id)
    first = client.get(_url(task.id, media.id))
    again = client.get(_url(task.id, media.id), HTTP_IF_NONE_MATCH=first["ETag"])

    assert again.status_code == 304
    assert again.content == b""


def test_other_user_gets_404():
    _, task, media, _ = _fixture("media-owner-a")
    stranger, _, _, _ = _fixture("media-owner-b")

    response = _client(stranger.id).get(_url(task.id, media.id))

    assert response.status_code == 404


def test_media_from_other_task_gets_404():
    owner, task, media, _ = _fixture("media-owner-cross")
    _, other_task, _, _ = _fixture("media-owner-cross-2")

    response = _client(owner.id).get(_url(other_task.id, media.id))

    assert response.status_code == 404


def test_legacy_thumb_b64_row_still_serves():
    """迁移窗口内，未迁到磁盘的旧行继续按原格式可读。"""
    owner, task, _, _ = _fixture("media-legacy")
    raw = _jpeg_bytes()
    legacy = TaskMedia.objects.create(
        task=task,
        sha256="b" * 64,
        media_type="image/jpeg",
        byte_size=len(raw),
        thumb_b64=base64.b64encode(raw).decode("ascii"),
    )

    response = _client(owner.id).get(_url(task.id, legacy.id))

    assert response.status_code == 200
    assert response["Content-Type"] == "image/jpeg"
    assert response.content == raw


def test_migrate_command_moves_legacy_row_to_webp_file():
    owner, task, _, _ = _fixture("media-migrate")
    raw = _jpeg_bytes()
    legacy = TaskMedia.objects.create(
        task=task,
        sha256="c" * 64,
        media_type="image/jpeg",
        byte_size=len(raw),
        thumb_b64=base64.b64encode(raw).decode("ascii"),
    )

    call_command("migrate_task_media_to_disk", stdout=StringIO())

    legacy.refresh_from_db()
    assert legacy.storage_key
    assert not legacy.thumb_b64
    assert legacy.media_type == "image/webp"
    assert Path(django_settings.TASK_MEDIA_DIR, legacy.storage_key).is_file()


def test_reconcile_removes_orphans_and_reports_missing():
    owner, task, media, _ = _fixture("media-reconcile")
    Path(django_settings.TASK_MEDIA_DIR, media.storage_key).unlink()
    orphan = Path(django_settings.TASK_MEDIA_DIR, str(task.id), f"{'f' * 64}.webp")
    orphan.write_bytes(b"orphan")

    out = StringIO()
    err = StringIO()
    call_command("reconcile_task_media", stdout=out, stderr=err)

    assert not orphan.exists()
    assert "1 row(s) missing" in out.getvalue()
    assert "missing:" in err.getvalue()


def test_anonymous_request_is_rejected():
    _, task, media, _ = _fixture("media-owner-anon")

    response = Client().get(_url(task.id, media.id))

    assert response.status_code == 401
    assert b"RIFF" not in response.content
