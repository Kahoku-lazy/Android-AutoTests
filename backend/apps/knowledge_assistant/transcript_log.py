"""
python -m 调试路径: backend.apps.knowledge_assistant.transcript_log

本模块的业务功能如下：
1. today_file(): 按本地自然日定位对话日志文件。
2. describe_path(): 把日志路径转成便于展示的相对路径。
3. DialogueLog: 把一条对话消息或会话事件追加到当日 JSONL 文件。

日志是业务档案，不是 project-log 的四组运行日志；写入失败只记警告，
不向语音会话抛异常。
"""

from __future__ import annotations

import json
import threading
import uuid

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Final

from utils.logs import backend_log

BEIJING_TZ: Final[timezone] = timezone(timedelta(hours=8))
REPO_ROOT: Final[Path] = Path(__file__).resolve().parents[3]
_WRITE_LOCK = threading.Lock()
_USAGE_EVENTS: Final[set[str]] = {
    "model_usage",
    "asr_usage",
    "tts_usage",
    "embedding_usage",
}


def _now() -> datetime:
    """返回北京时间当前时刻。"""
    return datetime.now(BEIJING_TZ)


def _timestamp() -> str:
    """返回带毫秒与 +08:00 偏移的 ISO 时间戳。"""
    return _now().isoformat(timespec="milliseconds")


def today_file(log_dir: Path) -> Path:
    """
    返回指定目录下当日对话日志文件路径。

    Args:
        log_dir: 对话日志目录。

    Returns:
        `YYYY-MM-DD.jsonl` 形式的路径（不保证已存在）。
    """
    return Path(log_dir) / f"{_now():%Y-%m-%d}.jsonl"


def describe_path(path: Path) -> str:
    """
    把绝对路径转成便于展示的相对路径。

    Args:
        path: 目标路径。

    Returns:
        位于仓库内时返回 posix 相对路径，否则返回绝对路径字符串。
    """
    try:
        return Path(path).resolve().relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return str(path)


class DialogueLog:
    """
    一次会话的对话日志写入器。

    Attributes:
        log_dir: 日志目录。
        session_id: 本次会话 id，写入每一行。
        user_id: 当前登录用户 id，写入每一行。
    """

    def __init__(
        self,
        log_dir: Path,
        session_id: str,
        user_id: str,
        usage_sink: Callable[[dict, str, str], object] | None = None,
    ) -> None:
        """
        初始化写入器。

        Args:
            log_dir: 日志目录；不存在时在首次写入前创建。
            session_id: 本次会话 id。
            user_id: 当前登录用户 id。
            usage_sink: 可选的用量账本写入函数；收到 (payload, session_id, user_id)。
        """
        self.log_dir = Path(log_dir)
        self.session_id = session_id
        self.user_id = user_id
        self.usage_sink = usage_sink

    @property
    def path(self) -> Path:
        """当前应写入的当日日志文件路径。"""
        return today_file(self.log_dir)

    @property
    def display_path(self) -> str:
        """当前日志文件的展示路径。"""
        return describe_path(self.path)

    def message(self, role: str, text: str, reply_id: str = "") -> None:
        """
        写入一条最终对话消息。

        Args:
            role: `user` 或 `assistant`。
            text: 最终文本；空文本不写入。
            reply_id: 该消息对应的 AgentScope reply id。
        """
        if not text.strip():
            return
        self._append(
            {
                "type": "message",
                "role": role,
                "text": text,
                "reply_id": reply_id,
            },
        )

    def event(self, name: str, **fields: object) -> None:
        """
        写入一条会话事件。

        Args:
            name: 事件名，如 `session_start` / `session_end`。
            **fields: 事件的附加字段，必须可 JSON 序列化。
        """
        payload = {"type": "event", "event": name, **fields}
        if name in _USAGE_EVENTS:
            payload.setdefault("usage_id", uuid.uuid4().hex)
        self._append(payload)
        if name in _USAGE_EVENTS and self.usage_sink is not None:
            try:
                self.usage_sink(payload, self.session_id, self.user_id)
            except Exception as exc:  # noqa: BLE001
                backend_log.warning("知识库助手用量入账失败: %s", exc)

    def _append(self, payload: dict) -> None:
        """
        把一条记录追加为一行 JSON；失败只记警告。

        Args:
            payload: 已包含业务字段的记录体。
        """
        record = {
            "ts": _timestamp(),
            "session_id": self.session_id,
            "user_id": self.user_id,
            **payload,
        }
        line = json.dumps(record, ensure_ascii=False) + "\n"
        path = self.path
        with _WRITE_LOCK:
            try:
                self.log_dir.mkdir(parents=True, exist_ok=True)
                with path.open("a", encoding="utf-8") as handle:
                    handle.write(line)
            except OSError as exc:
                # 日志是旁路：磁盘满 / 权限不足时继续语音会话，只留运行期告警
                backend_log.warning("知识库助手对话日志写入失败 (%s): %s", path, exc)
