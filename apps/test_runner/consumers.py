"""Channels WebSocket consumer for test run progress."""
from urllib.parse import parse_qs
from channels.generic.websocket import AsyncWebsocketConsumer
from .callbacks import test_callbacks
from shared.auth.jwt_auth import verify_token


class TestRunConsumer(AsyncWebsocketConsumer):
    channel_layer_alias = None

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.run_id = None

    async def connect(self):
        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = (params.get("token", [None])[0])
        if not token:
            await self.close(code=4001, reason="missing token")
            return
        try:
            payload = verify_token(token)
            if not payload:
                await self.close(code=4001, reason="invalid token")
                return
        except Exception:
            await self.close(code=4001, reason="token verification failed")
            return
        self.run_id = self.scope['url_route']['kwargs']['run_id']
        await self.accept()
        test_callbacks.register(self.run_id, self)

    async def disconnect(self, close_code):
        test_callbacks.unregister(self.run_id, self)

    async def receive(self, text_data=None, bytes_data=None):
        pass  # keep-alive
