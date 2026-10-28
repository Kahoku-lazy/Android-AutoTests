## Context

- 后端是 Django 6 + DRF + Channels（`backend/config/asgi.py` 已用 `ProtocolTypeRouter` 同时挂 HTTP 与 WebSocket），但当前 `backend/gateway/routing.py` 的 `websocket_urlpatterns` 为空。
- 现有 AI 能力（`backend/apps/ai_assistant`）是请求/响应式 HTTP；实时语音在参考模块 `temps/realtime_voice_demo` 中已经跑通 AgentScope 2.0.9 的 `RealtimeAgent` + `DashScopeRealtimeModel`，但它的传输层是服务端本地声卡 `LocalAudioTransport`，不能直接用于浏览器。
- 前端是 Vue 3 + Vite，已有 `/ws` 开发代理；语音页需要 Web Audio 采集与播放，且必须在用户点击后才申请麦克风权限。
- 根 `.env` 已配置 `DASHSCOPE_API_KEY`；参考模块自己的 `.env` 属于临时目录，不得在运行时读取。

## Goals / Non-Goals

**Goals:**

- 用一条服务端 WebSocket 通道把浏览器音频桥接到 `RealtimeAgent`，复用现有实时模型与回合检测能力，不把服务商 Key 下发到浏览器。
- 在页面上实时呈现用户转写与助手回复，并支持打断与状态反馈。
- 每条最终对话落本机 JSONL 日志，按自然日分文件，写入失败不影响会话。
- 保持单一职责：配置、提示词、日志、传输、会话编排、WS 生命周期、HTTP 状态接口各自独立模块。

**Non-Goals:**

- 不实现 RAG 知识库（文档上传、解析、向量化、检索、引用范围）。
- 不实现语音唤醒词、离线 ASR/TTS、回声消除算法或多人同时说话分离；回声控制交给浏览器 `echoCancellation` 与用户戴耳机。
- 不把任务进度、设备控制或平台写操作搬上 WebSocket。
- 不做跨进程会话共享或多副本广播；每个浏览器连接一个独立模型会话。

## Decisions

### 1. 服务端桥接，而不是浏览器直连模型

浏览器把音频发到本平台后端，由后端持有 `DASHSCOPE_API_KEY` 并连接实时模型。备选是后端签发临时凭证让浏览器直连服务商：那样前端要处理服务商协议、密钥轮换与跨域，且 Key 会进入浏览器内存。服务端桥接复用 AgentScope 的会话治理（重连、打断、工具权限），安全边界也更清晰。

### 2. 自定义 `TransportBase` 适配浏览器

`RealtimeAgent.reply_stream(transport)` 只依赖 `TransportBase` 的 `incoming()` / `send_audio()` / `clear_audio()` / `playout()` 四个能力。新增 `WebSocketAudioTransport`：

- 上行：浏览器二进制帧 → `AudioFrame` 入队；JSON 控制帧（`interrupt` / `played`）→ `ControlFrame` 入队。
- 下行：模型音频经二进制帧下发；`item_id` 变化时先下发一条 JSON `audio_item`，让浏览器按条目归属播放与回报进度。
- 播放进度：浏览器每 200ms 回传 `{type:"played", item_id, played_ms}`；`playout()` 返回最近一次回报，`clear_audio()` 先通知浏览器清空播放队列，再返回该位置，供 `RealtimeAgent` 截断上下文。
- 不采用 `LocalAudioTransport`：它绑定 `sounddevice` 与 PortAudio，服务端部署环境没有声卡也不应该有。

### 3. 二进制音频 + JSON 控制帧

音频帧用 WebSocket 二进制帧（PCM16 原样），避免 base64 的 33% 体积膨胀与编解码开销；控制/转写/状态用 JSON 文本帧。二者在同一个连接内按发送顺序到达，浏览器按帧类型分派。

### 4. 模型参数沿用参考模块的已验证组合

默认 `qwen3.5-omni-plus-realtime` + `Tina` + `server_vad`，与 `temps/realtime_voice_demo/.env` 一致。模型卡声明输入 16000 Hz、输出 24000 Hz，浏览器据此重采样与解码；采样率由服务端 `ready` 事件下发，前端不硬编码。

备选是前端直连 DashScope 的 `qwen3.8-omni-flash-realtime` 专属地址：当前 AgentScope 2.0.9 不含该模型卡，且会绕过统一鉴权，不采用。

### 5. 对话日志独立于四组运行日志

`project-log` 定义的是后端/智能体/设备/串口四组运行日志。对话记录是业务档案，不是运行期排障日志，因此写入 `logs/knowledge_assistant/YYYY-MM-DD.jsonl`，不写入 `backend.log`。运行期异常（连接失败、日志写入失败）仍写 `backend_log`。写入用模块级锁 + 单行追加，保证同一进程多会话不交错；失败只告警。

### 6. JWT 走查询参数，服务端先鉴权再连模型

浏览器 WebSocket API 不能设置 `Authorization` 头，因此用 `?token=<access_token>`。服务端在 `connect()` 里先用既有 `verify_token(expected_type="access")` 校验，失败则发一条错误消息并以 4401 关闭，不创建模型会话、不写日志。令牌不写入任何日志。

### 7. 前端音频：AudioWorklet 为主，ScriptProcessor 兜底

- 采集：`getUserMedia({ audio: { channelCount: 1, echoCancellation: true, noiseSuppression: true } })` → `MediaStreamAudioSourceNode` → AudioWorklet（每 100ms 汇总）→ 线性重采样到模型输入采样率 → Int16 → WebSocket。
- 播放：按 `audio_item` 归属，把 PCM16 解码为 24kHz `AudioBuffer`，用 `AudioBufferSourceNode` 顺序排程；浏览器自动把 24kHz 重采样到设备采样率。
- 打断：服务端 `clear_audio` → 浏览器停止所有 source 并重置排程；同时由服务端 `response.cancel` 停止模型继续生成。
- 纯函数（Int16 转换、线性重采样、转写 reducer）下沉到 `audio/pcm.ts` 与 `helpers/transcript.ts`，用 Vitest 在 jsdom 下直接测，不依赖真实 Web Audio。

### 8. 语音 consumer 不接 channel layer

本 consumer 只处理单连接的双向音频与转写，没有 group 广播、也不接收其它进程投递的消息，因此重写 `__call__` 只保留 `receive → dispatch` 直连路径，不创建/读取 Redis channel layer。理由是实测：每条 100ms 音频帧都经过 `channels_redis` 时，Redis 读超时会被放大成 1011 会话中断；绕过 channel layer 后同一段中文语音可完整跑通转写、回复与落日志。其它模块的 Channels 行为不变，`CHANNEL_LAYERS` 配置也不改。

### 9. UI 采用既有 Doodle 壳层

页面根 `doc-page doc-page--fixed wb-shell` + `WorkbenchHeader`；正文两栏：左侧语音控制台（粘性），右侧对话记录。空态用 `EmptyState`，错误用 `ErrorState`，不新增第二套卡片/按钮皮肤。语音按键用圆形（`border-radius: 50%` 属已登记图形量）与硬偏移阴影，颜色取 `--c-element` / `--c-ai`。

## 模块防火墙自检

- 新 App `backend/apps/knowledge_assistant` 只依赖 `backend/shared/auth/jwt_auth.py`（共享鉴权）与 `utils/logs.py`（共享日志），不 import 其它 App 的 service/runner/consumer/state_machine。
- 本能力不写数据库：没有 Model、没有 migration、没有跨 App 写路径；对话日志是文件档案，不进入 ORM。
- 前端只经 `shared/api-client` 调状态接口，不直连数据库；WebSocket 只承载语音与本会话事件。
- WS 路由集中在 `backend/gateway/routing.py` 注册，符合后端网关约束。
- PRD「无 WebSocket/SSE」的唯一例外仅限本通道；任务与列表仍走 HTTP 轮询。

## Risks / Trade-offs

- [浏览器外放导致助手声音被麦克风收录，触发自打断] → 默认开启 `echoCancellation` / `noiseSuppression`，页面提示戴耳机；服务端 VAD 与前端 `clear_audio` 保证可恢复。
- [实时模型空闲约 3 分钟会被服务端关闭] → 复用 `RealtimeAgent` 的自动重连：下一次说话时重连并补发音频；页面状态回到「聆听中」而非报错。
- [WebSocket 音频与转写事件乱序或丢帧] → 音频与控制共用一条连接、按发送顺序处理；前端只按 `item_id` 聚合文本，丢一帧音频不阻塞转写。
- [服务端每个连接一个模型会话，成本与并发压力] → 首期单机、单用户使用；不自动重连轰炸，连接断开即释放；后续如需并发上限，在 consumer 层加配额。
- [JSONL 日志无限增长] → 按自然日分文件，单日文件可由运维归档；本期不做自动轮转，避免与 `project-log` 的轮转契约混淆。
- [浏览器自动播放策略阻止音频] → 在用户点击语音按键的同一手势内创建并 `resume()` AudioContext。
- [测试环境没有真实 Key/声卡] → 后端单测只测配置、传输、日志与路由，不发起真实模型连接；前端单测只测纯函数。

## Migration Plan

1. 部署后端新 App 并重启 ASGI 服务；`websocket_urlpatterns` 从空表变为一条路由。
2. 确认根 `.env` 的 `DASHSCOPE_API_KEY` 可用；未配置时页面显示未就绪原因，不影响其它模块。
3. 前端发版后侧栏出现「AI 功能」分组；旧 `/ai-assistant` 路径保持不变。
4. 回滚：移除侧栏分组与新路由、卸载新 App、删除 `backend/gateway/routing.py` 中的 WS 路由；日志文件保留，不影响既有功能。

## Open Questions

无。
