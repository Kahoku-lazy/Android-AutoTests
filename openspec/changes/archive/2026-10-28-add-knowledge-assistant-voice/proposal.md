## Why

侧栏目前只有「AI 助手」一个 AI 入口，用户需要一个与它并列的「知识库助手」；本期先落语音交互，让用户点一下就能用说话提问，并在屏幕上实时看到对话记录，记录同时落到本机日志，便于事后核对与排障。

## What Changes

- 侧栏新增「AI 功能」分组，把「AI 助手」与新「知识库助手」放在同一组；「AI 功能」位于「仪表盘」之后、「数据」之前。
- 新增前端页面 `/knowledge-assistant`：一个语音按键、连接/聆听/思考/说话状态、实时对话记录区，以及本地日志落点提示。
- 新增后端 WebSocket 通道 `/ws/knowledge-assistant/`，把浏览器麦克风 PCM 音频桥接到 AgentScope 实时语音模型，并把模型返回的音频与转写实时推回浏览器。
- 每个会话把用户与助手的最终转写逐条追加到本地 JSONL 日志 `logs/knowledge_assistant/YYYY-MM-DD.jsonl`；运行期排障仍写既有 `backend.log`。
- 新增 `GET /api/knowledge-assistant/status/`，返回模型/音色/日志目录与「是否就绪」，不返回任何密钥。
- **BREAKING（产品约束）**：PRD「非功能约束：无 WebSocket / SSE」新增唯一例外——仅知识库助手的实时语音通道使用 WebSocket；任务进度与列表仍走 HTTP 轮询。
- 不恢复已下线的 RAG 知识库：没有文档上传、向量库、检索端点或 `/ai-assistant/knowledge` 页面；「知识库助手」本期只做语音问答，其系统提示词内置平台模块说明。

## 关联文档

- PRD 三、平台业务场景（3.1 登录功能总览、3.3 AI 助手业务流）
- PRD 五、非功能约束（实时性、可观测）
- ARCH 平台架构设计（后端 App / ASGI / Channels 分层）

## Capabilities

### New Capabilities

- `knowledge-assistant-voice`: 知识库助手的语音会话、浏览器音频桥接、实时转写、本地对话日志与就绪状态接口。

### Modified Capabilities

- `frontend-sidebar-nav`: 「AI 助手」不再紧贴「仪表盘」；改为「AI 功能」分组，含「AI 助手」与「知识库助手」，并明确分组标题与顺序。
- `knowledge-base-retirement`: 保留 RAG 知识库整体下线；仅放开「知识库助手」语音问答入口，禁止借该入口恢复文档库、检索或向量化能力。

## Impact

- 后端：新增 `backend/apps/knowledge_assistant/`（配置、提示词、日志、浏览器音频传输、会话编排、WS consumer、状态 API）；`backend/config/settings.py` 注册 App 与 Swagger 分组；`backend/config/urls.py` 挂载 HTTP 路由；`backend/gateway/routing.py` 注册 WS 路由。
- 前端：新增 `frontend/src/modules/knowledge-assistant/`（页面、语音采集/播放、转写 reducer、状态接口）；`frontend/src/router.ts`、`frontend/src/shared/components/sidebarNavConfig.ts`、`frontend/src/shared/icons/lucide-registry.ts` 增量修改。
- 配置：`.env.example` 增加 `KNOWLEDGE_ASSISTANT_*` 说明，复用根 `.env` 的 `DASHSCOPE_API_KEY`。
- 测试：新增后端 unit（配置/日志/传输/路由）与前端 p0（音频纯函数/转写 reducer/侧栏分组）。
- 文档：PRD 非功能约束补充 WebSocket 唯一例外，ARCH 架构文档补知识库助手链路。
