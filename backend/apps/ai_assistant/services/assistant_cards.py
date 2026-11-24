"""
模块功能：➡️ 助手名片写库。只登记展示字段、笔色、配置引用和工具勾选，不复制提示词 🏁
Python 调试：➡️ python -m backend.apps.ai_assistant.services.assistant_cards 🏁
时间：➡️ 2026-11-24 🏁
测试:➡️
1. 暂无（经 ai_assistant 的功能用例间接覆盖，未直接 import 本模块）
🏁
"""

from __future__ import annotations

import base64
import io

from PIL import Image, UnidentifiedImageError

from backend.apps.ai_assistant.models import AIAssistant, AIRole
from backend.apps.ai_assistant.services.assistant_id import generate_unique_assistant_id

# 自定义笔色，不按彩虹序。相邻创建只要求不同色。
MARKERS = ("teal", "ink", "amber", "rose", "moss")
AVATAR_MAX_EDGE = 128
AVATAR_MAX_CHARS = 12 * 1024


class AssistantRevisionConflict(Exception):
    """保存时版本戳与当前记录不一致。"""


class AssistantRoleMissingError(Exception):
    """引用的运营 Agent 配置不存在。"""


class AssistantIdExhaustedError(Exception):
    """当日可用的助手编号已耗尽。"""


class AvatarRejectedError(Exception):
    """头像无法解码，或压缩后仍超过上限。"""


def next_marker(latest: str | None) -> str:
    """按上一张名片的笔色取下一支不同色。

    Args:
        latest: 最近一张名片的笔色；没有时取第一支。

    Returns:
        与上一张不同的笔色名。
    """
    if latest not in MARKERS:
        return MARKERS[0]
    index = MARKERS.index(latest)
    return MARKERS[(index + 1) % len(MARKERS)]


def compress_avatar(raw: bytes) -> str:
    """把上传图压成最长边 128 的 JPEG base64。

    Args:
        raw: 原始图片字节。

    Returns:
        不含 data URL 前缀的 base64 文本，长度不超过 12KB。

    Raises:
        AvatarRejectedError: 无法解码，或降质量后仍超限。
    """
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
    """确认运营配置存在。不复制它的提示词或模型参数。"""
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
    """校验并准备一条待写入的名片，不写库。

    Args:
        display_name: 用户起的名称。
        role_id: 运营 Agent 配置短标识。
        latest_marker: 最近一张名片的笔色。
        is_taken: 编号查重函数。
        avatar: 原始图片字节。
        tools: 工具勾选。

    Returns:
        可直接交给 ORM 创建的字段字典。

    Raises:
        AssistantRoleMissingError: 引用的配置不存在。
        AssistantIdExhaustedError: 当日编号耗尽。
        AvatarRejectedError: 头像不合格。
    """
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
    """部分更新名片。编号与笔色不可改。

    Args:
        assistant: 待更新的名片。
        data: 已校验字段。avatar 为字节时重新压缩；空串表示删除头像。

    Returns:
        更新后的名片。

    Raises:
        AssistantRoleMissingError: 新的配置引用不存在。
        AvatarRejectedError: 新头像不合格。
    """
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
    """助手仍被工作流引用，拒绝删除。

    Attributes:
        names: 占用它的工作流名称，按工作流主键升序、去重。
    """

    def __init__(self, names: list[str]):
        self.names = names
        quoted = "、".join(f"「{name}」" for name in names)
        super().__init__(f"该助手正被工作流{quoted}使用，请先解除绑定再删除")


def workflows_using(assistant_id: str) -> list[str]:
    """找出把该助手用作执行、验收、队长或成员的工作流名称。

    Args:
        assistant_id: 助手编号。

    Returns:
        工作流名称列表，同一条只出现一次，按主键升序。
    """
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
    """物理删除助手名片。仍被工作流引用时拒绝，名片保持原样。

    Raises:
        AssistantInUseError: 至少一条工作流还绑定该助手。
    """
    names = workflows_using(assistant.assistant_id)
    if names:
        raise AssistantInUseError(names)
    assistant.delete()


def list_assistants():
    """返回全部名片，按创建时间倒序。"""
    return AIAssistant.objects.order_by("-created_at", "-id")


def get_assistant(assistant_id: str) -> AIAssistant | None:
    """按编号取名片；不存在返回 None。"""
    return AIAssistant.objects.filter(assistant_id=assistant_id).first()
