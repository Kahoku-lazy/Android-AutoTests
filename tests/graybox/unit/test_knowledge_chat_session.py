"""知识库文字问答单测：配置、回显、流式回答与用量记账（不联网）。"""

from __future__ import annotations

import json

import pytest

from agentscope.event import (
    ModelCallEndEvent,
    ReplyEndEvent,
    ReplyStartEvent,
    TextBlockDeltaEvent,
    TextBlockEndEvent,
)
from agentscope.types import ReplyFinishedReason

from backend.apps.knowledge_assistant.transcript_log import DialogueLog
from engines.agents.knowledge_chat import (
    ChatConfig,
    KnowledgeChatSession,
    build_status,
    load_chat_config,
)
from engines.agents.knowledge_chat.session import build_chat_toolkit
from engines.agents.realtime_vocie.events import TranscriptBridge

pytestmark = [pytest.mark.unit]

_CONFIG = ChatConfig(
    model="deepseek-flash",
    api_key_env="DEEPSEEK_API_KEY",
    max_text_chars=2000,
    enabled=True,
)


class _FakeAgent:
    """替身 Agent：按固定事件序列回答，并记录收到的输入。"""

    def __init__(self, events: list) -> None:
        self._events = events
        self.inputs: list = []

    async def reply_stream(self, inputs=None):
        self.inputs.append(inputs)
        for event in self._events:
            yield event


class _FakeRag:
    """替身 RAG 服务：只需要 enabled 标志。"""

    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled


def _reply_events(reply_id: str = "a1") -> list:
    return [
        ReplyStartEvent(
            session_id="session-1",
            reply_id=reply_id,
            name="知识库助手",
            role="assistant",
        ),
        TextBlockDeltaEvent(reply_id=reply_id, block_id="b1", delta="长按 3 秒"),
        TextBlockDeltaEvent(reply_id=reply_id, block_id="b1", delta="进入网络待机"),
        TextBlockEndEvent(reply_id=reply_id, block_id="b1"),
        ReplyEndEvent(
            session_id="session-1",
            reply_id=reply_id,
            finished_reason=ReplyFinishedReason.COMPLETED,
        ),
    ]


def _records(tmp_path):
    path = next(tmp_path.glob("*.jsonl"))
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]


def test_status_needs_deepseek_key():
    """缺 DeepSeek 密钥时文字入口未就绪并说明原因，有密钥时就绪。"""
    missing = build_status({})
    ready = build_status({"DEEPSEEK_API_KEY": "test-key"})

    assert missing["text_ready"] is False
    assert "DEEPSEEK_API_KEY" in missing["text_reason"]
    assert ready == {"text_model": "deepseek-flash", "text_ready": True, "text_reason": ""}


def test_invalid_max_chars_rejected():
    """文本上限不是整数时启动失败并点名环境变量。"""
    with pytest.raises(RuntimeError, match="KNOWLEDGE_CHAT_MAX_CHARS"):
        load_chat_config({"KNOWLEDGE_CHAT_MAX_CHARS": "abc"})


def test_chat_agent_has_no_tts_middleware(monkeypatch):
    """文字角色装配时不带语音合成中间件。"""
    from engines.agents.agent_builders import build_knowledge_chat

    monkeypatch.setenv("DEEPSEEK_API_KEY", "test-key")
    agent = build_knowledge_chat()

    names = [type(item).__name__.lower() for item in getattr(agent, "middlewares", [])]
    assert agent.name == "knowledge_chat_role"
    assert not [name for name in names if "tts" in name]


async def test_answer_echoes_user_and_streams_reply(tmp_path):
    """先回显用户消息，再把助手回答按增量下发并落两条日志。"""
    payloads: list[dict] = []

    async def send(payload: dict) -> None:
        payloads.append(payload)

    agent = _FakeAgent(_reply_events())
    session = KnowledgeChatSession(
        send,
        DialogueLog(tmp_path, "session-1", "user-1"),
        config=_CONFIG,
        agent=agent,
    )

    await session.answer("  长按开关按键3秒会怎样？  ")

    assert payloads[0]["type"] == "reply_start"
    assert payloads[0]["role"] == "user"
    assert payloads[1] == {
        "type": "transcript_final",
        "reply_id": payloads[0]["reply_id"],
        "role": "user",
        "text": "长按开关按键3秒会怎样？",
    }
    assert [payload["type"] for payload in payloads[2:]] == [
        "reply_start",
        "state",
        "transcript_delta",
        "transcript_delta",
        "transcript_final",
        "reply_end",
        "state",
    ]
    assert payloads[-3]["text"] == "长按 3 秒进入网络待机"
    assert agent.inputs[0].content[0].text == "长按开关按键3秒会怎样？"

    messages = [record for record in _records(tmp_path) if record["type"] == "message"]
    assert [(item["role"], item["text"]) for item in messages] == [
        ("user", "长按开关按键3秒会怎样？"),
        ("assistant", "长按 3 秒进入网络待机"),
    ]


async def test_blank_text_is_ignored(tmp_path):
    """空白文本不产生消息、不调用模型。"""
    payloads: list[dict] = []

    async def send(payload: dict) -> None:
        payloads.append(payload)

    agent = _FakeAgent(_reply_events())
    session = KnowledgeChatSession(
        send,
        DialogueLog(tmp_path, "session-1", "user-1"),
        config=_CONFIG,
        agent=agent,
    )

    await session.answer("   ")

    assert payloads == []
    assert agent.inputs == []


def test_usage_event_uses_deepseek_provider(tmp_path):
    """文字会话的用量事件记 deepseek / LLM，不串成 DashScope 实时。"""
    bridge = TranscriptBridge(
        DialogueLog(tmp_path, "session-1", "user-1"),
        model="deepseek-flash",
        provider="deepseek",
        category="LLM",
    )

    bridge.handle(ModelCallEndEvent(reply_id="a1", input_tokens=120, output_tokens=30))

    usage = [record for record in _records(tmp_path) if record.get("event") == "model_usage"]
    assert usage[0]["provider"] == "deepseek"
    assert usage[0]["category"] == "LLM"
    assert usage[0]["model"] == "deepseek-flash"
    assert usage[0]["input_tokens"] == 120


async def test_toolkit_follows_rag_switch():
    """RAG 未启用时不给工具包，启用时装上 search_knowledge。"""
    assert build_chat_toolkit(_FakeRag(False)) is None

    toolkit = build_chat_toolkit(_FakeRag(True))
    assert toolkit is not None
    assert await toolkit.get_tool("search_knowledge") is not None
