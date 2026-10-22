"""任务截图字节端点：登录、归属、缓存头与 404。"""

from __future__ import annotations

import base64
import io

import pytest

from django.contrib.auth import get_user_model
from django.test import Client
from PIL import Image

from backend.apps.ai_assistant.models import AIAgent
from backend.apps.task_list.models import Task, TaskMedia
from backend.shared.auth.jwt_auth import create_access_token

pytestmark = [pytest.mark.django_db, pytest.mark.unit]


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
    media = TaskMedia.objects.create(
        task=task,
        sha256="a" * 64,
        media_type="image/jpeg",
        byte_size=len(raw),
        thumb_b64=base64.b64encode(raw).decode("ascii"),
    )
    return owner, task, media, raw


def _client(user_id) -> Client:
    """带 JWT 的测试客户端。"""
    return Client(HTTP_AUTHORIZATION=f"Bearer {create_access_token(str(user_id))}")


def _url(task_id: int, media_id: int) -> str:
    return f"/api/tasks/{task_id}/media/{media_id}/"


def test_owner_gets_jpeg_bytes_with_cache_headers():
    owner, task, media, raw = _fixture()
    response = _client(owner.id).get(_url(task.id, media.id))

    assert response.status_code == 200
    assert response["Content-Type"] == "image/jpeg"
    assert response.content == raw
    assert response["ETag"] == f'"{media.sha256}"'
    assert "immutable" in response["Cache-Control"]


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


def test_anonymous_request_is_rejected():
    _, task, media, _ = _fixture("media-owner-anon")

    response = Client().get(_url(task.id, media.id))

    assert response.status_code == 401
    assert b"\xff\xd8" not in response.content
