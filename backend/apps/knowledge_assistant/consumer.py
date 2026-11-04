"""
python -m 调试路径: backend.apps.knowledge_assistant.consumer

本模块的业务功能如下：
1. KnowledgeAssistantConsumer: 知识库助手唯一的 WebSocket 入口。
2. connect(): 校验 JWT，按 `mode` 启动语音（Omni）或文字（DeepSeek Flash）会话。
3. receive(): 只处理 interrupt / played / text 三类白名单消息。
4. disconnect(): 取消会话任务、关闭音频传输并释放模型会话。

WS 路径：/ws/knowledge-assistant/?token=<access_token>&mode=voice|text
mode 缺省为 voice（旧客户端行为不变）；text 只承载文字问答，不碰音频。
"""

from __future__ import annotations

import asyncio
import json
import uuid

from functools import partial
from urllib.parse import parse_qs

from asgiref.sync import sync_to_async
from channels.exceptions import StopConsumer
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.utils import await_many_dispatch

from backend.apps.usage_ledger.api import record_voice_event
from backend.shared.auth.jwt_auth import verify_token
from engines.agents.knowledge_chat import (
    DEFAULT_AGENT_NAME,
    KnowledgeChatSession,
    load_chat_config,
)
from engines.agents.knowledge_chat import (
    build_status as build_chat_status,
)
from engines.agents.realtime_vocie.config import load_config
from engines.agents.realtime_vocie.transport import WebSocketAudioTransport
from utils.logs import backend_log

from .runtime import session_log_dir
from .transcript_log import DialogueLog

MODE_VOICE = "voice"
MODE_TEXT = "text"
SUPPORTED_MODES = (MODE_VOICE, MODE_TEXT)
# 账本来源与连接方式分开命名：语音 voice、文字 chat。
SOURCE_VOICE = "voice"
SOURCE_CHAT = "chat"


def token_from_scope(scope: dict) -> str:
    """
    从 WebSocket 握手 query string 里取出访问令牌。

    Args:
        scope: Channels 连接作用域。

    Returns:
        令牌字符串；未携带时返回空字符串。
    """
    return _query_value(scope, "token")


def mode_from_scope(scope: dict) -> str:
    """
    从 WebSocket 握手 query string 里取出会话方式。

    Args:
        scope: Channels 连接作用域。

    Returns:
        `voice` 或 `text`；未携带时返回 `voice`（保持旧客户端行为）。
    """
    return _query_value(scope, "mode").lower() or MODE_VOICE


def _query_value(scope: dict, name: str) -> str:
    """读取握手 query string 里的一个字段。"""
    raw = scope.get("query_string") or b""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", errors="replace")
    values = parse_qs(raw).get(name) or [""]
    return str(values[0])


class KnowledgeAssistantConsumer(AsyncWebsocketConsumer):
    """
    知识库助手 WebSocket consumer（语音 / 文字两种方式）。

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
        """校验登录态、接受连接并按方式启动会话任务。"""
        self._closed = False
        self._session_task: asyncio.Task | None = None
        self._reply_task: asyncio.Task | None = None
        self._user_id = ""
        self._session_id = uuid.uuid4().hex
        self._mode = mode_from_scope(self.scope)
        self._log: DialogueLog | None = None
        self._chat: KnowledgeChatSession | None = None
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

        if self._mode not in SUPPORTED_MODES:
            await self.accept()
            choices = " / ".join(SUPPORTED_MODES)
            await self._send_json(
                {"type": "error", "message": f"不支持的会话方式：{self._mode}（可选 {choices}）"},
            )
            await self.close(code=4400)
            return

        self._user_id = str(payload.get("sub") or "")
        await self.accept()
        if self._mode == MODE_TEXT:
            await self._start_text_session()
            return
        self._session_task = asyncio.create_task(
            self._run_session(),
            name=f"kb-voice-{self._session_id[:8]}",
        )

    async def disconnect(self, code: int) -> None:
        """取消会话任务并释放传输。"""
        self._closed = True
        for task in (self._session_task, self._reply_task):
            if task is not None and not task.done():
                task.cancel()
                await asyncio.gather(task, return_exceptions=True)
        self._session_task = None
        self._reply_task = None
        if self._mode == MODE_TEXT and self._log is not None:
            self._log.event(
                "session_end",
                reason="closed",
                mode=MODE_TEXT,
                input_tokens=self._chat.usage_input if self._chat else 0,
                output_tokens=self._chat.usage_output if self._chat else 0,
            )
            self._log = None
        await self._transport.close()

    async def receive(self, text_data: str | None = None, bytes_data: bytes | None = None) -> None:
        """处理白名单上行消息：音频、打断、播放进度与文字提问。"""
        if self._closed:
            return
        if bytes_data:
            if self._mode == MODE_VOICE:
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
        elif kind == "played":
            self._transport.report_played(
                str(payload.get("item_id") or ""),
                _to_int(payload.get("played_ms")),
            )
        elif kind == "text":
            await self._on_text(payload)
        else:
            # 白名单之外的消息一律忽略：本通道不承载平台写操作
            backend_log.debug("知识库助手 WS 忽略消息类型: %s", kind)

    async def _on_text(self, payload: dict) -> None:
        """校验并串行处理一条文字提问。"""
        if self._mode != MODE_TEXT or self._chat is None:
            backend_log.debug("知识库助手 WS 忽略语音模式下的 text 消息")
            return
        content = str(payload.get("text") or "").strip()
        if not content:
            return
        limit = self._chat.config.max_text_chars
        if len(content) > limit:
            await self._send_json(
                {"type": "notice", "message": f"单条消息最多 {limit} 字，请精简后再发送"},
            )
            return
        if self._reply_task is not None and not self._reply_task.done():
            await self._send_json(
                {"type": "notice", "message": "上一条还在回答，请稍候再发送"},
            )
            return
        self._reply_task = asyncio.create_task(
            self._answer_text(content),
            name=f"kb-text-{self._session_id[:8]}",
        )

    async def _answer_text(self, content: str) -> None:
        """跑一轮文字回答，异常转成可读提示。"""
        try:
            if self._chat is not None:
                await self._chat.answer(content)
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # 模型异常统一转成可读提示，详细堆栈进运行期日志
            backend_log.exception("知识库助手文字会话异常: %s", exc)
            await self._send_json({"type": "error", "message": "文字服务异常，请稍后重试"})
        finally:
            self._reply_task = None

    async def _start_text_session(self) -> None:
        """装配文字会话，下发 ready 与 session_start；配置不可用时给可读原因。"""
        status = build_chat_status()
        if not status["text_ready"]:
            await self._send_json({"type": "error", "message": status["text_reason"]})
            await self.close(code=4404)
            return

        try:
            config = load_chat_config()
        except RuntimeError as exc:
            await self._send_json({"type": "error", "message": str(exc)})
            await self.close(code=4404)
            return

        self._log = DialogueLog(
            session_log_dir(),
            self._session_id,
            self._user_id,
            usage_sink=self._enqueue_usage,
        )
        self._chat = KnowledgeChatSession(self._send_json, self._log, config=config)
        await self._send_json(
            {
                "type": "ready",
                "session_id": self._session_id,
                "agent_name": DEFAULT_AGENT_NAME,
                "model": config.model,
                "voice": "",
                "turn_detection": "",
                "mode": MODE_TEXT,
                "input_sample_rate": 0,
                "output_sample_rate": 0,
                "log_path": self._log.display_path,
            },
        )
        self._log.event(
            "session_start",
            mode=MODE_TEXT,
            model=config.model,
            agent_name=DEFAULT_AGENT_NAME,
        )

    async def _run_session(self) -> None:
        """读取配置并运行一次 Omni 语音会话。"""
        try:
            try:
                config = load_config()
            except RuntimeError as exc:
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
            from engines.agents.realtime_vocie.session import RealtimeVoiceSession

            session = RealtimeVoiceSession(
                config,
                self._transport,
                self._send_json,
                log,
            )
            await session.run()
        except asyncio.CancelledError:
            raise
        except Exception as exc:  # 会话异常统一转成可读提示，详细堆栈进运行期日志
            backend_log.exception("知识库助手 WS 会话异常: %s", exc)
            await self._send_json(
                {"type": "error", "message": "语音服务异常，请稍后重试"},
            )
        finally:
            await self._send_json({"type": "closed"})
            await self._transport.close()

    def _enqueue_usage(
        self,
        payload: dict,
        session_id: str,
        user_id: str,
    ) -> asyncio.Future | None:
        """把同步 ORM 入账放到线程池，避免在 async consumer 里直接写库。

        Args:
            payload: 日志里的用量事件。
            session_id: 会话 id。
            user_id: 当前登录用户 id。

        Returns:
            线程池任务的下标；没有运行中的事件循环时返回 None。
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return None
        return loop.run_in_executor(
            None,
            partial(
                record_voice_event,
                payload,
                session_id,
                user_id,
                source=SOURCE_CHAT if self._mode == MODE_TEXT else SOURCE_VOICE,
            ),
        )

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
