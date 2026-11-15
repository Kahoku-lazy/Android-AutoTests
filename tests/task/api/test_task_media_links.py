"""截图签名直链：签发、直接打开、过期/篡改拒绝与缓存语义。"""

from __future__ import annotations

import base64
import io

from pathlib import Path

import pytest

from django.conf import settings as django_settings
from django.contrib.auth import get_user_model
from django.test import Client
from PIL import Image

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list import api, media_links, media_storage
from backend.apps.task_list.models import Task, TaskMedia
from backend.shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


@pytest.fixture(autouse=True)
def _temp_media_dir(settings, tmp_path):
    settings.TASK_MEDIA_DIR = tmp_path / "task_media"
    media_storage.reset_media_storage()
    yield
    media_storage.reset_media_storage()


def _jpeg_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (8, 8), (30, 40, 50)).save(buffer, format="JPEG")
    return buffer.getvalue()


def _fixture(username: str = "signed-owner"):
    owner = get_user_model().objects.create_user(username=username, password="pass")
    agent = AIAgent.objects.create(name=f"{username}-助手", owner=owner)
    task = Task.objects.create(agent=agent, title="直链任务", status="completed")
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
    return Client(HTTP_AUTHORIZATION=f"Bearer {create_access_token(str(user_id))}")


def _link(client: Client, task_id: int, media_id: int):
    return client.post(f"/api/tasks/{task_id}/media/{media_id}/link/")


def test_link_endpoint_returns_relative_url_and_expiry():
    owner, task, media, _ = _fixture()
    response = _link(_client(owner.id), task.id, media.id)

    assert response.status_code == 200
    body = response.json()
    assert body["status"] is True
    payload = body["data"]
    assert payload["url"].startswith(f"/media/signed/{task.id}/{media.id}/")
    assert payload["expires"] > 0
    assert payload["expires_at"]


def test_link_endpoint_requires_login():
    _, task, media, _ = _fixture("signed-anon")
    assert _link(Client(), task.id, media.id).status_code == 401


def test_invisible_task_cannot_create_link():
    _, task, media, _ = _fixture("signed-owner-a")
    stranger, _, _, _ = _fixture("signed-owner-b")

    assert _link(_client(stranger.id), task.id, media.id).status_code == 404


def test_signed_url_serves_webp_without_jwt():
    owner, task, media, _ = _fixture("signed-open")
    url = _link(_client(owner.id), task.id, media.id).json()["data"]["url"]

    response = Client().get(url)

    assert response.status_code == 200
    assert response["Content-Type"] == "image/webp"
    assert Image.open(io.BytesIO(response.content)).format == "WEBP"
    assert response["ETag"] == f'"{media.sha256}"'


def test_signed_url_304():
    owner, task, media, _ = _fixture("signed-etag")
    url = _link(_client(owner.id), task.id, media.id).json()["data"]["url"]
    first = Client().get(url)

    again = Client().get(url, HTTP_IF_NONE_MATCH=first["ETag"])

    assert again.status_code == 304
    assert again.content == b""


def test_expired_link_is_rejected():
    _, task, media, _ = _fixture("signed-expired")
    expires, signature = media_links.sign(task.id, media.id, now=1_700_000_000, ttl=60)

    response = Client().get(media_links.build_path(task.id, media.id, expires, signature))

    assert response.status_code == 403


def test_tampered_signature_is_rejected():
    _, task, media, _ = _fixture("signed-tampered")
    expires, _ = media_links.sign(task.id, media.id)

    response = Client().get(media_links.build_path(task.id, media.id, expires, "0" * 64))

    assert response.status_code == 403


def test_signature_cannot_be_reused_for_another_media():
    _, task, media, _ = _fixture("signed-reuse")
    expires, signature = media_links.sign(task.id, media.id + 1)

    response = Client().get(media_links.build_path(task.id, media.id, expires, signature))

    assert response.status_code == 403


def test_valid_signature_with_missing_media_is_404():
    _, task, media, _ = _fixture("signed-missing")
    expires, signature = media_links.sign(task.id, 999_999)

    response = Client().get(media_links.build_path(task.id, 999_999, expires, signature))

    assert response.status_code == 404


def test_ttl_is_clamped_to_one_hour():
    now = 1_700_000_000
    expires, _ = media_links.sign(1, 1, now=now, ttl=99_999)

    assert expires - now == 3600


def test_file_is_written_under_temp_dir():
    _, task, media, _ = _fixture("signed-file")
    assert Path(django_settings.TASK_MEDIA_DIR, media.storage_key).is_file()
