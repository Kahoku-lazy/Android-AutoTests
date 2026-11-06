## 1. 智能体接口瘦身

- [x] 1.1 `backend/apps/ai_assistant/serializers.py`：`AgentListSerializer` 去掉 `avatar` 字段，`route_configs` 只保留 name 与三角色模型信息；`AgentDetailSerializer` 去掉 `avatar`。验证：`tests/graybox/unit/test_agent_payload_trim.py` 断言列表/详情均无 avatar 键。
- [x] 1.2 新增数据迁移 `0063_trim_oversized_avatars.py`：清空 `avatar` 与 `route_configs.*.avatar` 中超过 4096 字符的值；本地执行 `python manage.py migrate ai_assistant` 成功，`id=10` 的两处 6.5MB 值已清空、线路名保留。
- [x] 1.3 `AgentInputSerializer.avatar` 加 `max_length=4096`。验证：`test_oversized_avatar_is_rejected` 通过。

## 2. 任务列表查询

- [x] 2.1 `backend/apps/task_list/views.py`：去掉 `select_related("agent")`，改为 `.only(*TASK_LIST_FIELDS)` + `.prefetch_related("file_attachments")`；一次取线路名后传给序列化。
- [x] 2.2 `backend/apps/task_list/api.py`：新增 `assistant_names_by_agent()`，用 `KeyTextTransform` 在 SQL 侧抽 `route_configs->device_control->name`，不读整个 route_configs；`serialize_agent_task_row()` 接受 `assistant_name` 覆盖。
- [x] 2.3 保持响应字段不变（`assistant_name` / `attachment_names` / `deepseek_cost` 等）。验证：`test_task_list_keeps_row_fields` 通过。

## 3. 前端

- [x] 3.1 `frontend/src/modules/task-list/composables/useTaskList.ts`：轮询间隔 5s → 10s；`inFlight` 计数，上一轮未返回时跳过静默轮询。
- [x] 3.2 类型无需改动：`AgentRecord.avatar` 与线路 `avatar` 本就是可选字段。
- [x] 3.3 `frontend/tests/task-list/p0/useTaskList.spec.ts`：新增「慢请求不叠加」用例。验证：该文件 7 passed。

## 4. 测试

- [x] 4.1 新增 `tests/graybox/unit/test_agent_payload_trim.py`（5 条）：列表无头像且 <64KB、详情无头像、超长写入被拒、任务列表 SQL ≤5 且无 JOIN、行字段不变。 实测：5 passed。
- [x] 4.2 前端目标测试：`npx vitest run tests/task-list --maxWorkers=2` 全绿。

## 5. 验收

- [x] 5.1 重新生成 OpenAPI 基线并纳入提交（响应字段变化）。
- [x] 5.2 实测对比：`GET /api/ai/agents/` **13,114,611 B / 1.6–5.5s → 847 B / 43ms**；`GET /api/tasks/` **22 条 SQL / 1.8–5.4s → 4 条 SQL / 60ms**。
- [ ] 5.3 `python run.py check` 阻塞项全绿；`openspec validate trim-agent-avatar-payload --strict` 通过。 现状：**22/23**，唯一失败是 `vitest` 里 `LoginView.hero.spec.ts` 仍在断言旧品牌「AI 自动化测试平台」，而工作区 [LoginView.vue](frontend/src/views/LoginView.vue) 已被并行改成「智能化」——属外部未提交改动；`openspec validate --strict` 通过，`openapi-schema`/`ruff`/`prettier`/`eslint`/`vue-tsc` 全部通过。
