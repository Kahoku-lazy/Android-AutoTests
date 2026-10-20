## 1. 数据模型与迁移

- [x] 1.1 删除 `AIConversation` / `AIMessage` / `AIExecutionLog` 三个模型，以及 `AITask.description` / `AITask.scheduled_at` 两个字段；验证：`python manage.py check` 通过
- [x] 1.2 删除 `models/constants.py` 的 `ConversationStatus` 与 `ALL_STATUS_ENUMS` 中的 `"conversation"` 键，并把 `MessageRole` 注释改为不依赖 `ai_messages`；验证：全仓 grep `ConversationStatus` 零命中
- [x] 1.3 生成迁移 `0053_retire_ai_chat_surface`（DeleteModel ×3 + RemoveField ×2）；验证：`python manage.py makemigrations --check --dry-run` 输出 `No changes detected`，迁移文件内含三张表与两列的删除操作

## 2. 后端 API 面

- [x] 2.1 删除 `api.create_conversation` / `rename_conversation` / `delete_conversation` / `save_message` 与 `__all__` 中的「对话操作」「消息操作」条目；验证：全仓 grep 四个名字零代码命中
- [x] 2.2 删除 `serializers.ConversationCreateSerializer` / `ConversationListSerializer` / `MessageInputSerializer` / `MessageListSerializer` / `RenameInputSerializer`；验证：`ruff check apps/ai_assistant/serializers.py` 通过
- [x] 2.3 删除 `permissions.check_conversation_access` / `filter_conversations_for_user` 与 `AIConversation` import；验证：全仓 grep 零代码命中
- [x] 2.4 删除 `views_drf.ConversationViewSet`、`_conv_pk`，以及 `AgentViewSet` 上的 `list_conversations` / `create_conversation` 两个 action；验证：`python manage.py check` 通过
- [x] 2.5 删除 `urls.py` 中 `conversations` 路由注册与 `ConversationViewSet` import，并更新模块 docstring；验证：`python manage.py check` 通过
- [x] 2.6 删除 `admin.py` 中 `AIConversation` / `AIMessage` / `AIExecutionLog` 的注册与 import；验证：`python manage.py check` 通过

## 3. 恒空端点

- [x] 3.1 删除 `TaskBoardAPIView`、`AvailableSkillsAPIView` 及其路由 `tasks/`、`available-skills/`；验证：`python manage.py check` 通过，全仓 grep 两个类名零命中
- [x] 3.2 更新 `views_drf.py` 与 `urls.py` 的模块 docstring，移除已删除端点的路径清单；验证：docstring 内不再出现 `/api/ai/tasks/`（提交端点除外）与 `/api/ai/available-skills/`

## 4. 前端与会话类型

- [x] 4.1 删除 `frontend/src/shared/types/ai.ts` 中 `Conversation` / `ChatMessage` / `ContentBlock` 家族 / `ToolCall` / `SSERound` / `Hitl*` / `MessageRole` / `DeliveryStatus` / `StreamReason` / `ToolState` 与四个会话响应类型；验证：全仓 grep 这些类型名零命中
- [x] 4.2 删除 `frontend/src/modules/ai-assistant/api/toolbox.ts` 的 `fetchAvailableSkills`；验证：全仓 grep `fetchAvailableSkills` 零命中
- [x] 4.3 更新 `ai.ts` 文件头注释，去掉「对话 / 消息 / SSE 事件」表述；验证：`npm run build` 通过；`npm run typecheck` 的唯一报错来自既有 `useTaskPublish` 测试漂移（`ATTACH_ACCEPT`，与本单无关）

## 5. 脚本与文档

- [x] 5.1 删除 `tools/test_sse_e2e.py`；验证：文件不存在，全仓 grep `test_sse_e2e` 零命中
- [x] 5.2 接口文档 `dev_docs/DEV_TEST/接口文档/API-AI助手.md`：移除会话组与两个恒空端点的表格行与小节，并在原位置标注已下线；验证：文档内 `/api/ai/conversations` 与 `/api/ai/available-skills/` 零命中

## 6. 门禁与回归

- [x] 6.1 `python manage.py check` + `python manage.py makemigrations --check --dry-run` 通过
- [x] 6.2 `python -m ruff check apps/ai_assistant models` + `python -m ruff format --check apps/ai_assistant models` 通过
- [x] 6.3 `pytest tests/arch -q` 通过（27 passed）
- [x] 6.4 `python tools/gen_arch_stats.py --check-boundaries` 零违规
- [x] 6.5 前端构建：`npm run build` 通过；`npm run test` 为 428 passed / 4 failed，4 条失败均落在既有任务发布测试（`TaskInputPanel.spec.ts` / `useTaskPublish.spec.ts`），与本单无关
