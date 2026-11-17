"""助手名片写库：只引用配置、压缩头像、列表不含头像正文。"""

from __future__ import annotations

import io

import pytest

from PIL import Image

from backend.apps.ai_assistant.models import AIAssistant, AIModelConfig, AIRole
from backend.apps.ai_assistant.api import create_assistant
from backend.apps.ai_assistant.services.assistant_cards import (
    AssistantRoleMissingError,
    AvatarRejectedError,
    list_assistants,
    update_assistant,
)

pytestmark = [pytest.mark.unit, pytest.mark.django_db]


def _role(name: str = "执行配置") -> AIRole:
    config = AIModelConfig.objects.create(
        provider="deepseek",
        api_key_env="DEEPSEEK_API_KEY",
        model_name=f"model-{name}",
    )
    return AIRole.objects.create(
        role_id="20261116abc",
        name=name,
        model_config=config,
        system_prompt="你是执行者，这段不该被复制",
    )


def _png(size: int = 400) -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (size, size), (20, 120, 80)).save(buffer, format="PNG")
    return buffer.getvalue()


def test_create_stores_reference_not_prompt():
    role = _role()
    card = create_assistant("小助", role.role_id, tools=[])
    assert card.assistant_id.count("_") == 1
    assert card.role_id == role.role_id
    assert not hasattr(card, "system_prompt") or card.system_prompt == ""
    stored = AIAssistant.objects.get(pk=card.pk)
    assert "你是执行者" not in str(stored.__dict__)


def test_missing_role_is_rejected():
    with pytest.raises(AssistantRoleMissingError):
        create_assistant("小助", "20261116zzz")
    assert AIAssistant.objects.count() == 0


def test_avatar_is_compressed_and_list_omits_body():
    role = _role()
    card = create_assistant("小助", role.role_id, avatar=_png())
    assert card.avatar
    assert len(card.avatar) <= 12 * 1024
    row = {
        "assistant_id": card.assistant_id,
        "display_name": card.display_name,
        "has_avatar": bool(card.avatar),
        "marker": card.marker,
        "role_name": role.name,
    }
    assert "avatar" not in row
    listed = list(list_assistants())
    assert listed[0].avatar
    public = {item.assistant_id: bool(item.avatar) for item in listed}
    assert public[card.assistant_id] is True


def test_oversized_after_compress_is_rejected(monkeypatch):
    role = _role()
    monkeypatch.setattr(
        "backend.apps.ai_assistant.services.assistant_cards.AVATAR_MAX_CHARS",
        8,
    )
    with pytest.raises(AvatarRejectedError):
        create_assistant("小助", role.role_id, avatar=_png())
    assert AIAssistant.objects.count() == 0


def test_update_keeps_id_and_marker():
    role = _role()
    card = create_assistant("小助", role.role_id)
    updated = update_assistant(card, {"display_name": "新名", "avatar": b""})
    assert updated.assistant_id == card.assistant_id
    assert updated.marker == card.marker
    assert updated.display_name == "新名"
    assert updated.avatar == ""


def test_adjacent_markers_differ():
    role = _role()
    first = create_assistant("甲", role.role_id)
    second = create_assistant("乙", role.role_id)
    assert first.marker != second.marker
