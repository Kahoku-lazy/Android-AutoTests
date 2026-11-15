## Why

模型资产化完成后，`engines/agents/config/data/models.yaml` 已经是「平台支持哪些模型」的唯一真相，但前端没有入口：AI 助手页只有 agent 角色卡片，模型只能靠配置页手输模型名，用户既看不到平台支持什么，也没法直接试。把模型做成卡片、点开就能对话，让「模型资产」从配置文件变成可发现、可验证的能力。

## What Changes

- 新增只读模型清单接口 `GET /api/ai-assistant/models/`：数据来自 `engines.agents.models`，覆盖**可文字对话的 chat 族**与**可语音对话的 realtime 族**；不返回任何密钥（只给环境变量名）。
- AI 助手首页改为**两栏**：左栏 agent 角色卡片（沿用现有看板），右栏模型卡片网格；窄屏上下堆叠。
- 新增对话页 `/ai-assistant/chat/:model`：流式（SSE）逐字输出、可中断、可返回。
- **语音模型**在对话页提供麦克风对话入口（进入既有语音会话，使用模型默认音色）。
- **对话页可切换模型**：顶部下拉切换；视觉模型可随消息上传图片（≤4 张），非视觉模型拒绝图片；语音模型在对话页显示麦克风对话入口。
- 模型卡片**只做展示与跳转**：不可编辑、不可删除、不可改参数，不承担配置职责。
- 对话**不落库**：消息只存在于当前页面会话，刷新即清空。

## 关联文档

- PRD-平台总需求（AI 执行内核）
- ARCH-平台架构设计（Model + Harness 分层：模型是独立资产）
- `engines/agents/models/AGENTS.md`（模型资产表与门面）

## Capabilities

### New Capabilities

- `ai-model-gallery`: AI 助手页的模型卡片列表，以及「点卡片进入对话页并与该模型聊天」的只读链路。

### Modified Capabilities

（无：现有 `ai-agent-model-config` 描述的是配置页的三类模型选择，本次不改变其行为。）

## Impact

- 后端：`backend/apps/ai_assistant/`（模型清单与对话流两个接口）；`backend/apps/knowledge_assistant/consumer.py`（语音会话接受 `voice` 查询参数）。
- 引擎：只读引用 `engines.agents.models`（`available_models` / `get_model` / `get_chat_model`）；`config/data/models.yaml` 的 `omni` 增加 `voices`，`ModelSpec` 增加 `voices` 字段。
- 前端：`frontend/src/modules/ai-assistant/`（`index.vue` 拆两栏、新增 `ModelCard` / `ModelCardGrid` / `ChatPage`、`api/models.ts`、`api/chat.ts`、`routes.ts`、`constants.ts`）。
- 测试：后端接口测试 + 前端 `vue-tsc` / `vite build`；不涉及设备侧与任务侧。
- 数据库：**无迁移**，对话不持久化。
