"""ScreenshotStream — broadcasts screenshots to Channels consumers."""
import json
import asyncio
import traceback
from django.conf import settings
from apps.device_pool.api import device


class ScreenshotStream:
    """Manages screenshot broadcast to connected WebSocket clients at 2fps."""

    def __init__(self):
        self.clients: set = set()
        self._loop_task = None
        self._last_device_msg = None
        self._last_screenshot_msg = None
        self._last_status_msg = None

    async def add(self, consumer):
        self.clients.add(consumer)
        # Push cached frames so new clients render immediately
        for cached in (self._last_device_msg, self._last_screenshot_msg, self._last_status_msg):
            if cached:
                try:
                    await consumer.send(text_data=cached)
                except Exception:
                    self.remove(consumer)
                    return
        if self._loop_task is None or self._loop_task.done():
            self._loop_task = asyncio.create_task(self._broadcast_loop())

    def remove(self, consumer):
        self.clients.discard(consumer)

    async def _send_all(self, msg: str):
        dead = []
        for consumer in self.clients:
            try:
                await consumer.send(text_data=msg)
            except Exception:
                dead.append(consumer)
        for consumer in dead:
            self.remove(consumer)

    async def _broadcast_loop(self):
        last_serial = None
        loop = asyncio.get_event_loop()
        while self.clients:
            try:
                current = device.current_serial
                if not current:
                    status_msg = json.dumps({
                        "type": "no_device",
                        "message": "未选择设备，请在上方选择或连接设备",
                    })
                    if status_msg != self._last_status_msg:
                        self._last_status_msg = status_msg
                        await self._send_all(status_msg)
                    await asyncio.sleep(settings.SCREENSHOT_INTERVAL)
                    continue

                if current != last_serial:
                    last_serial = current
                    info = await loop.run_in_executor(None, device.info)
                    change_msg = json.dumps({
                        "type": "device_changed",
                        "serial": current,
                        "screen_w": info.get("displayWidth", 0),
                        "screen_h": info.get("displayHeight", 0),
                    })
                    self._last_device_msg = change_msg
                    self._last_status_msg = None
                    await self._send_all(change_msg)

                b64 = await loop.run_in_executor(
                    None, lambda: device.screenshot_b64(quality=50, max_width=720),
                )
                msg = json.dumps({"type": "screenshot", "image": b64, "format": "jpeg"})
                self._last_screenshot_msg = msg
                await self._send_all(msg)
            except Exception as e:
                print(f"Screenshot error: {e}")
                traceback.print_exc()
                err_msg = json.dumps({
                    "type": "screenshot_error",
                    "message": str(e)[:200],
                })
                self._last_status_msg = err_msg
                await self._send_all(err_msg)
            await asyncio.sleep(settings.SCREENSHOT_INTERVAL)


screenshot_stream = ScreenshotStream()
