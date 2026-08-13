"""Channels WebSocket consumer for collaborative case editing."""

from urllib.parse import parse_qs

from channels.generic.websocket import AsyncWebsocketConsumer

from shared.auth.jwt_auth import verify_token


class CaseEditingConsumer(AsyncWebsocketConsumer):
    """Notifies connected editors when a case is updated (e.g. by AI)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.case_id = None
        self.group_name = None

    async def connect(self):
        query_string = self.scope.get("query_string", b"").decode()
        params = parse_qs(query_string)
        token = params.get("token", [None])[0]
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

        self.case_id = self.scope["url_route"]["kwargs"]["case_id"]
        self.group_name = f"case_editing_{self.case_id}"

        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        pass  # keep-alive only; server pushes via group_send

    async def case_updated(self, event):
        """Handler for 'case_updated' group messages — forwarded to the WebSocket client."""
        await self.send(text_data=event.get("message", '{"type":"case_updated"}'))
