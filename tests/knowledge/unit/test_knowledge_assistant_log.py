"""知识库助手本地对话日志单测：字段、分文件与失败容错。"""

from __future__ import annotations

import json

from datetime import datetime

import pytest

from backend.apps.knowledge_assistant.transcript_log import (
    BEIJING_TZ,
    DialogueLog,
    describe_path,
    today_file,
)

pytestmark = [pytest.mark.unit]


def _read_records(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_message_fields(tmp_path):
    """一条消息写入 ts / session_id / user_id / role / text。"""
    log = DialogueLog(tmp_path, "session-1", "user-1")
    log.message("user", "设备怎么连", "reply-1")

    records = _read_records(log.path)

    assert len(records) == 1
    record = records[0]
    assert record["type"] == "message"
    assert record["session_id"] == "session-1"
    assert record["user_id"] == "user-1"
    assert record["role"] == "user"
    assert record["text"] == "设备怎么连"
    assert record["reply_id"] == "reply-1"
    assert record["ts"].endswith("+08:00")


def test_session_event_fields(tmp_path):
    """会话事件带事件名与附加字段。"""
    log = DialogueLog(tmp_path, "session-1", "user-1")
    log.event("session_start", model="qwen", voice="Tina")

    record = _read_records(log.path)[0]

    assert record["type"] == "event"
    assert record["event"] == "session_start"
    assert record["model"] == "qwen"
    assert record["voice"] == "Tina"


def test_empty_text_is_not_written(tmp_path):
    """空文本不产生空记录。"""
    log = DialogueLog(tmp_path, "session-1", "user-1")
    log.message("assistant", "   ")

    assert not log.path.exists()


def test_daily_file_name(tmp_path):
    """日志文件名按北京时间自然日。"""
    expected = f"{datetime.now(BEIJING_TZ):%Y-%m-%d}.jsonl"

    assert today_file(tmp_path).name == expected


def test_write_failure_does_not_raise(tmp_path):
    """日志目录不可写时只告警，不向调用方抛异常。"""
    blocked = tmp_path / "blocked"
    blocked.write_text("not a directory", encoding="utf-8")
    log = DialogueLog(blocked, "session-1", "user-1")

    log.message("user", "仍然要能继续说话")
    log.event("session_end", reason="closed")


def test_describe_path_prefers_relative(tmp_path, monkeypatch):
    """仓库内路径展示为相对路径。"""
    from backend.apps.knowledge_assistant import transcript_log

    monkeypatch.setattr(transcript_log, "REPO_ROOT", tmp_path)
    target = tmp_path / "logs" / "knowledge_assistant" / "2026-10-28.jsonl"

    assert describe_path(target) == "logs/knowledge_assistant/2026-10-28.jsonl"
