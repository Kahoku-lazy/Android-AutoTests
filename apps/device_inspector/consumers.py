"""Channels WebSocket consumer for screenshot streaming."""

from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer

from shared.auth.jwt_auth import verify_token

from .stream import screenshot_stream


class ScreenshotConsumer(AsyncWebsocketConsumer):
    # Screenshot broadcast uses in-process stream, not channel groups.
    channel_layer_alias = None

    async def connect(self):
        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]
        if not token:
            await self.close()
            return
        try:
            payload = verify_token(token)
            if not payload:
                await self.close()
                return
        except Exception:
            await self.close()
            return
        await self.accept()
        await screenshot_stream.add(self)

    async def disconnect(self, close_code):
        screenshot_stream.remove(self)

    async def receive(self, text_data=None, bytes_data=None):
        pass  # keep-alive
