## Why

会话/聊天能力已无任何前端入口：SPA 里没有聊天页，`conversations`、`messages`、`save-message` 全部无人调用，但后端仍保留 3 张 `ai_` 表、1 个 ViewSet、5 个序列化器、4 个写库函数，前端仍保留一整套 SSE/消息/HITL 类型与一个手工联调脚本。产品决定**不要这个功能**——继续留着只会让人误判能力仍在，并让 `api_` 表与 API 面持续失真。

## What Changes

- **BREAKING** 下线全部会话端点：`GET /api/ai/agents/{id}/conversations`、`POST /api/ai/agents/{id}/conversations/create`、`GET /api/ai/conversations/*`（messages / save-message / rename / delete / tasks / tasks/{run_id}）。
- **BREAKING** 数据库删除三张表：`ai_conversations`、`ai_messages`、`ai_execution_logs`；并删除死列 `ai_tasks.description`、`ai_tasks.scheduled_at`。
- 删除 `ConversationViewSet`、`ConversationCreateSerializer` / `ConversationListSerializer` / `MessageInputSerializer` / `MessageListSerializer` / `RenameInputSerializer`、`api.create_conversation` / `rename_conversation` / `delete_conversation` / `save_message`、`permissions.check_conversation_access` / `filter_conversations_for_user`、`ConversationStatus` 枚举、admin 中三处模型注册。
- 前端删除 `shared/types/ai.ts` 中会话 / 消息 / SSE / HITL 类型簇（`Conversation`、`ChatMessage`、`ContentBlock` 家族、`ToolCall`、`SSERound`、`Hitl*`、`MessageRole`、`DeliveryStatus`、`StreamReason`、`ToolState` 及 4 个响应类型）。
- 顺带删除两个恒空端点 `GET /api/ai/tasks/` 与 `GET /api/ai/available-skills/`，以及前端未被调用的 `fetchAvailableSkills`。
- 删除手工联调脚本 `tools/test_sse_e2e.py`（它调用的正是被下线的会话端点）。
- 文档同步：`dev_docs` 接口文档移除会话组与两个恒空端点，避免文档继续承诺已下线能力。

## 关联文档

产品口头决策「不要会话/聊天功能」，无对应 PRD 编号；`PRD-需求总纲` 未收录该能力，故不引用编号。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `admin-managed-shared-agent`: 移除「共享智能体下数据隔离」「超级管理员对话审计」两条对话专属需求，并把「共享智能体对普通用户可见且可用」收窄为只承诺可见性。
- `ai-screen-vision`: 移除「截图在对话历史中持久化」——截图改由任务步骤证据与工具返回承载，不再有对话历史。

## Impact

- 后端：`apps/ai_assistant/models.py`、`api.py`、`serializers.py`、`views_drf.py`、`permissions.py`、`urls.py`、`admin.py`；`models/constants.py`；新增一条删表迁移。
- 前端：`frontend/src/shared/types/ai.ts`、`frontend/src/modules/ai-assistant/api/toolbox.ts`。
- 工具脚本：`tools/test_sse_e2e.py`。
- 数据：三张表与两列被物理删除，**不可逆**。
- 测试与门禁：`manage.py check`、`makemigrations --check`、`ruff check/format`、`pytest tests/arch`、`gen_arch_stats --check-boundaries`。
