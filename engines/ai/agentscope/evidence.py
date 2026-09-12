"""验收证据落盘：把验证截图 DataBlock 写成 media 相对路径（引擎层不碰 Django）。"""

from __future__ import annotations

import base64
import logging

from pathlib import Path

logger = logging.getLogger("ai_assistant.workflow")

__all__ = ["save_verify_screenshot"]


def save_verify_screenshot(
    media_root: str,
    task_id: int,
    step_idx: int,
    loop: int,
    block,
) -> str:
    """将验收截图落盘为 JPEG，返回相对 MEDIA_ROOT 的路径；无法保存时返回空串。

    Args:
        media_root: 媒体根目录绝对路径（Django MEDIA_ROOT）。
        task_id: 任务 id（目录 ai_tasks/{id}/）。
        step_idx: 步骤序号（1 起）。
        loop: 本步重试轮次（1 起）。
        block: AgentScope DataBlock（含 Base64Source），可空。

    Returns:
        如 ``ai_tasks/12/s2_l1.jpg``；缺参 / 无图 / 写盘失败返回 ``""``。
    """
    if not media_root or not task_id or block is None:
        return ""
    source = getattr(block, "source", None)
    raw_b64 = getattr(source, "data", None) or ""
    if not raw_b64:
        return ""
    try:
        data = base64.b64decode(raw_b64)
    except Exception:
        logger.exception("verify screenshot base64 decode failed task=%s", task_id)
        return ""
    if not data:
        return ""

    rel = f"ai_tasks/{task_id}/s{step_idx}_l{loop}.jpg"
    dest = Path(media_root) / rel
    try:
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
    except OSError:
        logger.exception("verify screenshot write failed path=%s", dest)
        return ""
    return rel.replace("\\", "/")
