## Context

现状：`frontend/src/modules/ai-assistant/index.vue` 只有 agent 角色卡（`AgentRouteCard`），后端 `ai_assistant` 只有 agents CRUD（任务接口已迁 `task_list`），仓库内**没有** AI 助手的对话页；唯一聊天 UI 是 `knowledge-assistant`（带 RAG、走 WebSocket，不复用）。

模型侧已经就绪：`engines/agents/models` 提供 `available_models()` / `get_model()` / `get_chat_model()`，`describe_model()` 保证不返回密钥。后端已有直接引用 engines 的先例（`device_pool`、`knowledge_assistant`）。

参考需求：[proposal.md](proposal.md)；行为契约：[`specs/ai-model-gallery/spec.md`](specs/ai-model-gallery/spec.md)。

## Goals / Non-Goals

**Goals:**

- 一个接口把「平台支持哪些对话模型」吐给前端，前端不硬编码模型名。
- 首页两栏：角色与模型并列，模型卡只展示、不配置。
- 点卡片进对话页，流式输出、可中断、错误可见。
- 不新增数据库表、不写历史。

**Non-Goals:**

- 不做模型配置/参数编辑（那属于 `ai-agent-model-config` 与配置页）。
- 不做多轮持久化、不做会话列表。
- 不做工具调用与 SOP（纯模型对话）。
- 不把 embedding / tts / realtime 做成卡片（它们不能「聊」）。
- 不做联网连通性探测。

## Decisions

**D1：卡片只列 chat 族。**
理由：卡片的唯一动作是「进入对话」，非 chat 族进去无法工作。备选「全族列出、非 chat 置灰」——被否，会制造一堆不可用的灰卡。

**D2：对话用 SSE（POST + 文本流），不用 WebSocket。**
单向流、无需保活、便于过反向代理；`knowledge_assistant` 的 WS 是为音频双向设计的，不适用。事件约定：`data: {"delta": "..."}`、`event: done`、`event: error`。

**D3：后端无状态，历史由前端持有。**
每轮请求携带完整消息列表，后端只做「messages → 模型 → 流」。备选「后端 session 缓存」——被否，引入状态与清理问题，且与「不持久化」冲突。

**D4：后端只经 engines 门面取模型。**
`from engines.agents.models import get_chat_model, get_model, available_models`；后端 MUST NOT 直接构造 `agentscope` 模型类，保持「模型实例只在 models 包内造」的既有边界。

**D5：路由 `/ai-assistant/chat/:model`。**
刷新可恢复：页面按 `:model` 重新拉清单定位元数据；找不到就显示不可用提示（不白屏）。

**D6：就绪判定 = 环境变量存在，不联网。**
`ready = bool(os.environ.get(api_key_env))`。备选「实际调一次」——被否，列表接口会被打爆；后续可加手动「测试」按钮。

**D7：组件拆分。**
`index.vue` 只做布局；`ModelCard` / `ModelCardGrid` 为 L4 数据面；`ChatPage.vue` 独占 L2–L5；样式复用模块 `tokens.css`，不新造主题。

**D8：对话不计费、不写用量台账。**
与「不持久化」一致；代价是这部分 token 消耗不可见（记录日志即可）。若后续要记账，再走 usage_ledger，不塞进本期。

**D9：语音模型复用知识库助手的语音会话，不新建第二条语音通道。**
对话页切到语音模型时展示麦克风入口，跳转知识库助手并带 `?mode=voice`（默认音色）；前端把 `voice` 拼进既有 WS 握手，后端 consumer 校验后覆盖 `RealtimeVoiceConfig.voice`。
备选「在 AI 助手模块内新建语音通道」——被否：会重复麦克风采集、播放队列、打断与事件桥一整套，且违背「本模块不做第二套 WS」的既有约束。

**D10：对话页 = 模型卡池的入口，卡片本身不承载任何操作。**
卡片只展示能力与规格；进入对话页后由顶部下拉切换模型。视觉模型的图片随最后一条用户消息以 `DataBlock` 附加（≤4 张），非视觉模型在视图层直接 400。切换模型即清空当前消息，避免跨模型串台。

## 模块防火墙自检

- 跨 App import：后端 `ai_assistant` 只调用 engines 门面（只读），不反向依赖；engines 不 import `apps.*` / `django.*`。
- 写库：**无**。新增接口一个只读、一个流式，均不碰 ORM。
- 数据落点：模型数据仍只在 `engines/agents/config/data/models.yaml`，前端不存模型清单副本。
- 前端边界：卡片与对话页都是 `ai-assistant` 模块私有组件，不跨模块复用；共享件继续走 `shared/`。

## Risks / Trade-offs

- [SSE 被 Nginx/代理缓冲，前端看不到增量] → 响应加 `X-Accel-Buffering: no`，并 `Cache-Control: no-cache`。
- [客户端中断后后端任务继续跑、白烧 token] → 以请求断开为取消信号，`finally` 里取消生成器。
- [清单接口把密钥带出去] → 只序列化 `api_key_env`（`env:NAME`），并有单测断言无 `api_key`/`token` 字段。
- [对话页刷新丢上下文，用户困惑] → 空会话时给一行说明「对话不会保存」。
- [误把卡片当配置入口] → 卡片不渲染任何编辑控件，点击唯一定向对话页。
- [未就绪模型误判] → 只按环境变量判定，卡片明确写「未配置密钥」，不假装可用。

## Migration Plan

纯新增，无数据迁移：

1. 后端先上 `GET /models/`（前端可并行开发）→ 再上 `POST /chat/stream/`。
2. 前端先接卡片（不影响现有角色卡），再接对话页与路由。
3. 回滚：删除两条路由与前端入口即可，无库表残留。

## Open Questions

- 卡片是否显示价格？当前模型表没有价目，本期不做；要做先把价目搬进 `models.yaml`。
- 对话是否要展示 token 用量？本期不做（不记账），留作后续增强。
