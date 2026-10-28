"""知识库助手 WS 入口单测：令牌解析、控制消息白名单与路由注册。"""

from __future__ import annotations

import pytest

from backend.apps.knowledge_assistant.consumer import (
    _to_int,
    mode_from_scope,
    token_from_scope,
)
from backend.gateway.routing import websocket_urlpatterns

pytestmark = [pytest.mark.unit]


def test_token_from_scope_reads_query_string():
    """从握手 query string 取 token。"""
    scope = {"query_string": b"token=abc.def&other=1"}

    assert token_from_scope(scope) == "abc.def"


def test_token_from_scope_handles_missing_token():
    """未携带 token 时返回空字符串。"""
    assert token_from_scope({"query_string": b""}) == ""
    assert token_from_scope({}) == ""


def test_token_from_scope_handles_text_query():
    """有些测试会直接传字符串 query_string。"""
    assert token_from_scope({"query_string": "token=xyz"}) == "xyz"


def test_mode_from_scope_reads_route():
    """从握手 query string 取路线；缺失时回退后端配置。"""
    assert mode_from_scope({"query_string": b"token=x&mode=pipeline"}) == "pipeline"
    assert mode_from_scope({"query_string": b"token=x"}) == ""


@pytest.mark.asyncio
async def test_receive_routes_text_to_pipeline_session():
    """Pipeline 文本消息转给 submit_text。"""
    from backend.apps.knowledge_assistant.consumer import KnowledgeAssistantConsumer

    class DummySession:
        def __init__(self):
            self.texts = []

        async def submit_text(self, text: str) -> None:
            self.texts.append(text)

    consumer = object.__new__(KnowledgeAssistantConsumer)
    consumer._closed = False
    consumer._pipeline_session = DummySession()

    await consumer.receive(text_data='{"type":"text","text":"长按按键3秒"}')

    assert consumer._pipeline_session.texts == ["长按按键3秒"]


def test_to_int_is_safe():
    """播放进度参数无法转换时按 0 处理。"""
    assert _to_int("120") == 120
    assert _to_int(120) == 120
    assert _to_int("abc") == 0
    assert _to_int(None) == 0


def test_websocket_route_is_registered():
    """知识库助手是当前唯一注册的 WS 路由。"""
    patterns = [str(pattern.pattern) for pattern in websocket_urlpatterns]

    assert patterns == ["ws/knowledge-assistant/"]
