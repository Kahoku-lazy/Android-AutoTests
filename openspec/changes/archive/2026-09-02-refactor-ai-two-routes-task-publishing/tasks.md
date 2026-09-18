## 1. 后端数据模型

- [x] 1.1 `AIAgent` 增 `route_configs JSONField`、`AITask` 增 goal/requirements/attachment/route/checklist/report_name/status 字段；`python manage.py makemigrations` 生成迁移并 `python manage.py check` 通过
- [x] 1.2 `api.py` 增 `route_configs` 内 api_key 的加密/脱敏工具（复用 encrypt_key/decrypt_key/mask_key）；`ruff check` 通过

## 2. 后端 API 与线路分发

- [x] 2.1 `serializers.py` 增 `route_configs` 入参/输出 DTO + `TaskSubmitInputSerializer`（goal 必填、route 枚举）；`ruff check` 通过
- [x] 2.2 `views_drf.py` `AgentViewSet` 读写 `route_configs`；新增 `TaskSubmitAPIView`（按 route 分发：device_control → plan()+build_agent("vision")，platform_task → 占位）；`urls.py` 增 `tasks/submit`；`python manage.py check` + `pytest tests/ai_assistant` 通过

## 3. 移除主对话（后端）

- [x] 3.1 删 `views/chat_views.py`、`hitl_views.py`、`tool_gateway.py`（若仅对话用）+ `urls.py` 删 `conversations/<id>/chat/stream` 与相关对话端点；`python manage.py check` 通过、grep 无 `chat_stream`/`resolve` 残留

## 4. 前端智能体配置改造

- [x] 4.1 `shared/types/ai.ts` 增 `RouteConfigMap`/`RouteModelConfig`；`AgentRecord` 增 `route_configs`；`api/agents.ts` DTO 同步
- [x] 4.2 `AgentModelConfig.vue` 抽可复用单模型块；新增 `AgentRouteConfig.vue`（两线路各含规划+执行模型）；`AgentDetail.vue` 表单改 `route_configs`；`npm run build` 通过 + `vue-frontend-check` 门禁

## 5. 前端任务发布模块

- [x] 5.1 新增 `api/tasks.ts`（submitTask/listTasks/getTaskDetail）；`routes.ts` 增 `/ai-assistant/tasks`；`constants.ts` 增 tasksRoute + 线路枚举
- [x] 5.2 新增 `TaskPublishCard.vue`（6 字段 + 提交）、`TaskList.vue`（AppTable）、`TaskDetail.vue`；`useTaskPublish.ts`/`useTaskList.ts`；`index.vue` 增 tasks 视图；`npm run build` 通过 + 真实页面端到端验证（提交→列表→详情）

## 6. 移除主对话（前端）

- [x] 6.1 删 `ChatView.vue`/聊天组件/`api/sse.ts`/`api/conversations.ts`/`useSSE`/`useConversation`/`useMessageStore` 等；删 `chatRoute`；`vue-tsc` + `npm run build` 通过、grep 无残留 import

## 7. 测试与文档

- [x] 7.1 删 `tests/ai_assistant/test_conversations_api.py`；新增任务提交 + 多线路配置接口测试；`pytest -m "unit or integration"` 通过
- [x] 7.2 同步 PRD-08 / ARCH-08；`python tools/gen_arch_stats.py --check-md` 与 `--check-boundaries` 通过
