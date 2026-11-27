from __future__ import annotations

import base64
import io

from PIL import Image, UnidentifiedImageError

from backend.apps.ai_assistant.models import AIAssistant, AIRole
from backend.apps.ai_assistant.services.assistant_id import generate_unique_assistant_id

MARKERS = ("teal", "ink", "amber", "rose", "moss")
AVATAR_MAX_EDGE = 128
AVATAR_MAX_CHARS = 12 * 1024


class AssistantRevisionConflict(Exception):
    pass


class AssistantRoleMissingError(Exception):
    pass


class AssistantIdExhaustedError(Exception):
    pass


class AvatarRejectedError(Exception):
    pass


def next_marker(latest: str | None) -> str:
    if latest not in MARKERS:
        return MARKERS[0]
    index = MARKERS.index(latest)
    return MARKERS[(index + 1) % len(MARKERS)]


def compress_avatar(raw: bytes) -> str:
    try:
        image = Image.open(io.BytesIO(raw))
        image = image.convert("RGB")
    except (UnidentifiedImageError, OSError) as exc:
        raise AvatarRejectedError("头像无法识别") from exc
    image.thumbnail((AVATAR_MAX_EDGE, AVATAR_MAX_EDGE))
    encoded = ""
    for quality in (80, 60, 40, 25):
        buffer = io.BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=True)
        encoded = base64.b64encode(buffer.getvalue()).decode("ascii")
        if len(encoded) <= AVATAR_MAX_CHARS:
            return encoded
    raise AvatarRejectedError("头像压缩后仍超过 12KB")


def _require_role(role_id: str) -> None:
    if not AIRole.objects.filter(role_id=role_id).exists():
        raise AssistantRoleMissingError("Agent 配置不存在")


def prepare_create(
    display_name: str,
    role_id: str,
    *,
    latest_marker: str | None,
    is_taken,
    avatar: bytes | None = None,
    tools: list | None = None,
) -> dict:
    _require_role(role_id)
    try:
        assistant_id = generate_unique_assistant_id(is_taken)
    except RuntimeError as exc:
        raise AssistantIdExhaustedError(str(exc)) from exc
    return {
        "assistant_id": assistant_id,
        "display_name": display_name,
        "avatar": compress_avatar(avatar) if avatar else "",
        "marker": next_marker(latest_marker),
        "role_id": role_id,
        "tools": list(tools or []),
    }


def update_assistant(assistant: AIAssistant, data: dict) -> AIAssistant:
    if "role_id" in data:
        _require_role(data["role_id"])
        assistant.role_id = data["role_id"]
    if "display_name" in data:
        assistant.display_name = data["display_name"]
    if "tools" in data:
        assistant.tools = list(data["tools"])
    if "avatar" in data:
        raw = data["avatar"]
        assistant.avatar = "" if raw in (None, b"", "") else compress_avatar(raw)
    if "revision" in data and int(data["revision"]) != assistant.revision:
        raise AssistantRevisionConflict("内容已变化，请先刷新")
    runtime_changed = "role_id" in data or "tools" in data
    if runtime_changed and assistant.release_state == "published":
        assistant.release_state = "draft"
    assistant.revision += 1
    assistant.save()
    return assistant


class AssistantInUseError(Exception):
    def __init__(self, names: list[str]):
        self.names = names
        quoted = "、".join(f"「{name}」" for name in names)
        super().__init__(f"该助手正被工作流{quoted}使用，请先解除绑定再删除")


def workflows_using(assistant_id: str) -> list[str]:
    from backend.apps.ai_assistant.models import AISopWorkflow

    names: list[str] = []
    for workflow in AISopWorkflow.objects.order_by("id"):
        bound = [
            workflow.executor_assistant_id,
            workflow.verifier_assistant_id,
            workflow.leader_assistant_id,
        ]
        bound.extend(str(item.get("assistant_id") or "") for item in workflow.members or [])
        if assistant_id in bound:
            names.append(workflow.name)
    return names


def delete_assistant(assistant: AIAssistant) -> None:
    names = workflows_using(assistant.assistant_id)
    if names:
        raise AssistantInUseError(names)
    assistant.delete()


def list_assistants():
    return AIAssistant.objects.defer("avatar").order_by("-created_at", "-id")


def get_assistant(assistant_id: str) -> AIAssistant | None:
    return AIAssistant.objects.filter(assistant_id=assistant_id).first()
