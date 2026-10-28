"""
python -m 调试路径: backend.apps.knowledge_assistant.consumer

本模块的业务功能如下：
1. KnowledgeAssistantConsumer: 知识库助手唯一的 WebSocket 入口。
2. connect(): 校验 JWT，接受连接并启动一次语音会话任务。
3. receive(): 只处理 interrupt、played 与 Pipeline text 三类白名单消息。
4. disconnect(): 取消会话任务、关闭音频传输并释放模型会话。

WS 路径：/ws/knowledge-assistant/?token=<access_token>&mode=<omni|pipeline>
"""

from __future__ import annotations

import asyncio
import json
import uuid

from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.utils import await_many_dispatch

from backend.apps.usage_ledger.api import record_voice_event
from backend.shared.auth.jwt_auth import verify_token
from engines.agents.realtime_vocie.config import (
    PIPELINE_MODE,
    load_config,
    select_mode,
)
from engines.agents.realtime_vocie.pipeline import PipelineVoiceSession
from engines.agents.realtime_vocie.session import RealtimeVoiceSession
from engines.agents.realtime_vocie.transport import WebSocketAudioTransport
from utils.logs import backend_log

from .runtime import session_log_dir
from .transcript_log import DialogueLog


def mode_from_scope(scope: dict) -> str:
    """
    从 WebSocket 握手 query string 里取出路线（omni / pipeline）。

    Args:
        scope: Channels 连接作用域。

    Returns:
        路线字符串；未携带时返回空字符串，由后端配置决定。
    """
    raw = scope.get("query_string") or b""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    values = parse_qs(raw).get("mode") or [""]
    return str(values[0]).strip()


def token_from_scope(scope: dict) -> str:
    """
    从 WebSocket 握手 query string 里取出访问令牌。

    Args:
        scope: Channels 连接作用域。

    Returns:
        令牌字符串；未携带时返回空字符串。
    """
    raw = scope.get("query_string") or b""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    values = parse_qs(raw).get("token") or [""]
    return str(values[0])


class KnowledgeAssistantConsumer(AsyncWebsocketConsumer):
    """
    知识库助手实时语音 WebSocket consumer。

    本 consumer **不接 channel layer**：语音音频是高频双向流，且没有分组广播，
    让每条 100ms 音频帧都经过 Redis 的 channel layer 只会把 Redis 抖动放大成
    会话中断（实测 Redis 读超时会直接 1011 关闭音频）。因此只保留客户端
    receive → dispatch 这条直连路径；鉴权、模型会话与日志都不需要 channel layer。
    """

    async def __call__(self, scope, receive, send) -> None:
        """只分发客户端消息，不创建/读取 channel layer 通道。"""
        self.scope = scope
        self.channel_layer = None
        self.base_send = send
        try:
            await await_many_dispatch([receive], self.dispatch)
        except StopConsumer:
            # 连接正常结束：consumer 已通过 close() 发送 websocket.close
            pass

    async def connect(self) -> None:
        """校验登录态、接受连接并启动会话任务。"""
        self._closed = False
        self._session_task: asyncio.Task | None = None
        self._pipeline_session: PipelineVoiceSession | None = None
        self._user_id = ""
        self._requested_mode = mode_from_scope(self.scope)
        self._session_id = uuid.uuid4().hex
        self._transport = WebSocketAudioTransport(self._send_json, self._send_bytes)

        token = token_from_scope(self.scope)
        try:
            payload = await sync_to_async(verify_token)(token, expected_type="access")
        except Exception as exc:  # 鉴权失败：不创建模型会话，不写对话日志
            backend_log.warning("知识库助手 WS 鉴权失败: %s", exc)
            await self.accept()
            await self._send_json(
                {"type": "error", "message": "登录已过期或令牌无效，请重新登录"},
            )
            await self.close(code=4401)
            return

        self._user_id = str(payload.get("sub") or "")
        await self.accept()
        self._session_task = asyncio.create_task(
            self._run_session(),
            name=f"kb-voice-{self._session_id[:8]}",
        )

    async def disconnect(self, code: int) -> None:
        """取消会话任务并释放传输。"""
        self._closed = True
        task = self._session_task
        self._session_task = None
        if task is not None and not task.done():
            task.cancel()
            await asyncio.gather(task, return_exceptions=True)
        await self._transport.close()

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        """处理浏览器上行音频与白名单控制消息。"""
        if self._closed:
            return
        if bytes_data:
            self._transport.push_audio(bytes_data)
            return
        if not text_data:
            return

        try:
            payload = json.loads(text_data)
        except json.JSONDecodeError:
            backend_log.debug("知识库助手 WS 收到非 JSON 消息")
            return
        if not isinstance(payload, dict):
            return

        kind = payload.get("type")
        if kind == "interrupt":
            self._transport.push_interrupt()
        elif kind == "text":
            text = str(payload.get("text") or "").strip()
            if not text:
                return
            if self._pipeline_session is None:
                await self._send_json(
                    {"type": "error", "message": "当前路线不支持文本输入"},
                )
                return
            await self._pipeline_session.submit_text(text)
        elif kind == "played":
            self._transport.report_played(
                str(payload.get("item_id") or ""),
                _to_int(payload.get("played_ms")),
            )
        else:
            # 白名单之外的消息一律忽略：本通道不承载平台写操作
            backend_log.debug("知识库助手 WS 忽略消息类型: %s", kind)

    async def _run_session(self) -> None:
        """读取配置并运行一次语音会话。"""
        try:
            try:
                config = load_config()
                if self._requested_mode:
                    config = select_mode(config, self._requested_mode)
            except (RuntimeError, ValueError) as exc:
                # 引擎配置错误（缺 Key/关闭/非法 VAD）直接给用户可读原因；
                # 模型连接错误走下面的通用提示，避免把技术细节透给前端。
                backend_log.warning("知识库助手配置不可用: %s", exc)
                await self._send_json({"type": "error", "message": str(exc)})
                return

            log = DialogueLog(
                session_log_dir(),
                self._session_id,
                self._user_id,
                usage_sink=self._enqueue_usage,
            )
            session_class = (
                PipelineVoiceSession if config.mode == PIPELINE_MODE else RealtimeVoiceSession
            )
            session = session_class(
                config,
                self._transport,
                self._send_json,
                log,
            )
            if isinstance(session, PipelineVoiceSession):
                self._pipeline_session = session
            await session.run()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # 会话异常统一转成可读提示，详细堆栈进运行期日志
            backend_log.exception("知识库助手 WS 会话异常: %s", exc)
            await self._send_json(
                {"type": "error", "message": "语音服务异常，请稍后重试"},
            )
        finally:
            self._pipeline_session = None
            await self._send_json({"type": "closed"})
            await self._transport.close()

    def _enqueue_usage(self, payload: dict, session_id: str, user_id: str) -> None:
        """把同步 ORM 入账放到线程池，避免在 async consumer 里直接写库。"""
        try:
            loop = asyncio.get_running_loop()
            loop.run_in_executor(
                None,
                record_voice_event,
                payload,
                session_id,
                user_id,
            )
        except RuntimeError:
            return

    async def _send_json(self, payload: dict) -> None:
        """发送一条 JSON 文本帧；连接已关闭时静默返回。"""
        if self._closed:
            return
        try:
            await self.send(text_data=json.dumps(payload, ensure_ascii=False))
        except Exception as exc:  # 浏览器已断开属正常路径，记调试日志即可
            backend_log.debug("知识库助手 WS JSON 发送失败: %s", exc)
            self._closed = True

    async def _send_bytes(self, payload: bytes) -> None:
        """发送一帧二进制音频；连接已关闭时静默返回。"""
        if self._closed or not payload:
            return
        try:
            await self.send(bytes_data=payload)
        except Exception as exc:  # 同 _send_json：断开是正常路径
            backend_log.debug("知识库助手 WS 音频发送失败: %s", exc)
            self._closed = True


def _to_int(value: object) -> int:
    """
    把前端传来的数值安全转成整数。

    Args:
        value: 任意值。

    Returns:
        整数值；无法转换时返回 0。
    """
    try:
        return int(value)  # type: ignore[arg-type]
    except (TypeError, ValueError):
        return 0
