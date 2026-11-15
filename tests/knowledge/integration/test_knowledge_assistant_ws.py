"""知识库助手 WS 入口集成测试：无效令牌必须被拒绝，不建立模型会话。"""

from __future__ import annotations

import pytest

from channels.testing import WebsocketCommunicator

from backend.config.asgi import application

pytestmark = [pytest.mark.integration]


async def test_rejects_invalid_token_before_session():
    """无效 JWT 连接先收到可读错误，再以 4401 关闭。"""
    communicator = WebsocketCommunicator(
        application,
        "/ws/knowledge-assistant/?token=not-a-real-token",
        headers=[(b"origin", b"http://localhost")],
    )

    connected, _ = await communicator.connect()
    assert connected is True

    message = await communicator.receive_json_from(timeout=5)
    assert message["type"] == "error"
    assert "登录" in message["message"]

    await communicator.disconnect()
